import asyncio
import json
import os
import re
import tempfile
from datetime import datetime

import google.generativeai as genai
from dotenv import load_dotenv
from tqdm import tqdm

from data_import import import_products, import_highlights
from prompt_builder import build_prompt

load_dotenv()

# Configuration
GEMINI_MODEL = "gemini-3-flash-preview"
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "..", "results.json")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MAX_RETRIES = 3
BATCH_SIZE = 30  # Concurrent requests limit

# Configure SDK
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name=GEMINI_MODEL)


async def call_gemini_async(prompt: str, product_id: int) -> str:
    """Send a prompt to Gemini asynchronously and return the response text.

    Retries up to MAX_RETRIES times with exponential backoff on transient errors.
    """
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = await model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                wait = 2 ** attempt
                tqdm.write(f"[RETRY] ID {product_id} attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                await asyncio.sleep(wait)

    raise last_error


def extract_json(text: str) -> dict:
    """Extract JSON dictionary from the model response text."""
    # Remove markdown fences if present
    text = re.sub(r"```json?\s*", "", text)
    text = re.sub(r"```", "", text)

    # Find JSON object (greedy to capture full object)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found in response")

    return json.loads(match.group())


def ensure_html_wrapped(description: str) -> str:
    """Ensure the description is wrapped in <p> tags."""
    text = description.strip()
    if not text.lower().startswith("<p"):
        text = f"<p>{text}</p>"
    return text


def validate_highlights(result: dict) -> list[str]:
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


async def process_product_async(row, highlights: dict, semaphore: asyncio.Semaphore) -> dict:
    """Process a single product asynchronously with rate limiting."""
    async with semaphore:
        prompt = build_prompt(row["id"], row["title"], row["description"], highlights)

        start_time = datetime.now()
        response_text = await call_gemini_async(prompt, row["id"])
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

        return result


def filter_unprocessed_products(df, processed_ids: set, n: int = None) -> tuple[list, int]:
    """Filter products to process, return (to_process list, skip_count)."""
    total = len(df) if n is None else min(n, len(df))
    to_process = []
    skip_count = 0

    for _, row in df.head(total).iterrows():
        if row["id"] in processed_ids:
            print(f"[SKIP] ID: {row['id']} | {row['title']}")
            skip_count += 1
        else:
            to_process.append(row)

    return to_process, skip_count


async def process_batch(batch: list, highlights: dict, semaphore, results: list, pbar) -> list:
    """Process a single batch of products, return list of failures."""
    tasks = [process_product_async(row, highlights, semaphore) for row in batch]
    batch_results = await asyncio.gather(*tasks, return_exceptions=True)

    failed = []
    for row, result in zip(batch, batch_results):
        if isinstance(result, Exception):
            failed.append((row["id"], row["title"], str(result)))
            tqdm.write(f"[FAIL] ID: {row['id']} | {row['title']} | Error: {result}")
        else:
            warnings = validate_highlights(result)
            for w in warnings:
                tqdm.write(f"[WARN] ID {row['id']}: {w}")
            results.append(result)
            tqdm.write(f"[NEW]  ID: {row['id']} | {row['title']}")
        pbar.update(1)

    return failed


async def process_products_async(n: int = None) -> list[dict]:
    """Process products asynchronously in parallel batches.

    Args:
        n: Number of products to process. None = all products.
    """
    df = import_products()
    highlights = import_highlights()

    existing = load_existing_results()
    processed_ids = {r["id"] for r in existing if "id" in r}
    results = list(existing)

    to_process, skip_count = filter_unprocessed_products(df, processed_ids, n)

    if not to_process:
        total = len(df) if n is None else min(n, len(df))
        print(f"\nAll {total} products already processed ({len(existing)} total)")
        return results

    print(f"\nProcessing {len(to_process)} products with {BATCH_SIZE} concurrent requests...")

    semaphore = asyncio.Semaphore(BATCH_SIZE)
    pbar = tqdm(total=len(to_process), desc="Processing products", unit="product")
    all_failed = []

    for i in range(0, len(to_process), BATCH_SIZE):
        batch = to_process[i:i + BATCH_SIZE]
        failed = await process_batch(batch, highlights, semaphore, results, pbar)
        all_failed.extend(failed)
        save_results(results, silent=True)

    pbar.close()

    print(f"\nProcessed {len(to_process) - len(all_failed)} new products ({len(existing)} already existed)")
    if all_failed:
        print(f"Failed {len(all_failed)} products:")
        for pid, title, err in all_failed:
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
