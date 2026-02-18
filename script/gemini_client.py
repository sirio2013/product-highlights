import json
import os
import re
import tempfile
import time
from datetime import datetime

import requests as http_requests
from dotenv import load_dotenv
from tqdm import tqdm

from data_import import import_products, import_highlights
from prompt_builder import build_prompt

load_dotenv()

# GEMINI_MODEL = "gemini-3-pro-preview"
GEMINI_MODEL = "gemini-3-flash-preview"
# GEMINI_MODEL = "gemini-2.5-flash-preview-09-2025"
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "..", "results.json")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MAX_RETRIES = 3


def call_gemini(prompt: str) -> str:
    """Send a prompt to Gemini via REST API and return the response text.

    Retries up to MAX_RETRIES times with exponential backoff on transient errors.
    """
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "thinkingConfig": {"thinkingLevel": "MEDIUM"}
        },
    }

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = http_requests.post(
                GEMINI_URL,
                params={"key": GEMINI_API_KEY},
                json=payload,
                timeout=120,
            )
            response.raise_for_status()

            data = response.json()
            parts = data["candidates"][0]["content"]["parts"]
            # Return the last text part (skip thinking parts)
            for part in reversed(parts):
                if "text" in part:
                    return part["text"]

            raise ValueError("No text found in Gemini response")

        except (http_requests.exceptions.RequestException, ValueError, KeyError) as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                wait = 2 ** attempt
                tqdm.write(f"[RETRY] Attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                time.sleep(wait)

    raise last_error


def extract_json(text: str) -> dict:
    """Extract JSON dictionary from the model response text."""
    # Try to find JSON block in markdown code fence
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))

    # Try to find raw JSON object (non-greedy to avoid matching too much)
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Fall back to greedy match as last resort
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError("No JSON found in response")


def ensure_html_wrapped(description: str) -> str:
    """Ensure the description is wrapped in <p> tags."""
    text = description.strip()
    if not text.lower().startswith("<p"):
        text = f"<p>{text}</p>"
    return text


def validate_highlights(result: dict, highlights: dict[str, list[str]]) -> list[str]:
    """Check that selected highlights appear in the description.

    Returns a list of warning messages for highlights not found in the description.
    """
    warnings = []
    description = result.get("descrizione", "").lower()
    for key in ["product-highlights-1", "product-highlights-2", "product-highlights-3"]:
        selected = result.get(key, "")
        if selected and selected.lower() not in description:
            warnings.append(f"Highlight '{selected}' not found in description")
    return warnings


def load_existing_results(output_path: str = None) -> list[dict]:
    """Load existing results from JSON file, if it exists."""
    if output_path is None:
        output_path = RESULTS_PATH

    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return []


def process_products(n: int = None) -> list[dict]:
    """Process products and return a list of result dicts.

    Args:
        n: Number of products to process. None = all products.
    """
    df = import_products()
    highlights = import_highlights()

    existing = load_existing_results()
    processed_ids = {r["id"] for r in existing if "id" in r}

    total = len(df) if n is None else min(n, len(df))
    results = list(existing)
    failed = []

    # Filter to only unprocessed products
    to_process = []
    for i in range(total):
        row = df.iloc[i]
        if row["id"] in processed_ids:
            print(f"[SKIP] ID: {row['id']} | {row['title']}")
        else:
            to_process.append(row)

    if not to_process:
        print(f"\nAll {total} products already processed ({len(existing)} total)")
        return results

    # Process products sequentially
    pbar = tqdm(total=len(to_process), desc="Processing products", unit="product")

    for row in to_process:
        try:
            prompt = build_prompt(row["id"], row["title"], row["description"], highlights)

            start_time = datetime.now()
            response_text = call_gemini(prompt)
            end_time = datetime.now()

            result = extract_json(response_text)

            # Add metadata
            result["prompt"] = prompt
            result["start_timestamp"] = start_time.isoformat()
            result["end_timestamp"] = end_time.isoformat()
            result["duration_seconds"] = round((end_time - start_time).total_seconds(), 2)

            # Post-process: ensure HTML wrapping
            if "descrizione" in result:
                result["descrizione"] = ensure_html_wrapped(result["descrizione"])

            # Validate highlight integration
            warnings = validate_highlights(result, highlights)
            if warnings:
                for w in warnings:
                    tqdm.write(f"[WARN] ID {row['id']}: {w}")

            results.append(result)
            save_results(results, silent=True)
            tqdm.write(f"[NEW]  ID: {row['id']} | {row['title']}")

        except Exception as e:
            failed.append((row["id"], row["title"], str(e)))
            tqdm.write(f"[FAIL] ID: {row['id']} | {row['title']} | Error: {e}")

        pbar.update(1)

    pbar.close()

    processed_count = len(to_process) - len(failed)
    print(f"\nProcessed {processed_count} new products ({len(existing)} already existed)")
    if failed:
        print(f"Failed {len(failed)} products:")
        for pid, title, err in failed:
            print(f"  - ID {pid} | {title} | {err}")

    return results


def save_results(results: list[dict], output_path: str = None, silent: bool = False):
    """Save results to a JSON file using atomic write (temp file + rename)."""
    if output_path is None:
        output_path = RESULTS_PATH

    dir_name = os.path.dirname(os.path.abspath(output_path))
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, output_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    if not silent:
        print(f"Results saved to {output_path} ({len(results)} total)")
