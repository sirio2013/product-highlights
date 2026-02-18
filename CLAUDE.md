# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate virtual environment (Windows/Git Bash)
source venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Process first N products
python script/main.py 5

# Process all products
python script/main.py
```

## Architecture

Batch processing tool using Gemini AI to select product highlights and integrate them into Italian pet care product descriptions.

**Data Flow:**
1. Load products from `source/products-list.csv` and highlights (3 groups) from `source/prod_highl.csv`
2. Deduplicate against existing `results.json` to skip already-processed products
3. For each product: build Italian XML prompt → call Gemini async → extract JSON → validate highlights → save incrementally
4. Export final results to `results.xlsx`

**Key Modules:**
- `script/main.py` - Entry point, orchestrates async processing via `asyncio.run()`
- `script/gemini_client.py` - Async Gemini API calls, 30 concurrent requests, retry logic with exponential backoff
- `script/prompt_builder.py` - Builds Italian XML prompts with product description and highlight groups
- `script/data_import.py` - CSV import with validation helpers (`resolve_source_path`, `load_csv_validated`)
- `script/export_excel.py` - Pandas-based Excel export

**Processing Model:**
- Uses `gemini-3-flash-preview` model
- Async parallel processing with `asyncio.Semaphore(30)` for rate limiting
- Incremental JSON save after each batch (atomic write via temp file + rename)
- Automatic retry with exponential backoff (3 attempts max)

**Output Format:**
Each product result includes: `id`, `titolo`, `descrizione-iniziale`, `product-highlights-1/2/3`, `descrizione` (HTML), `prompt`, timestamps, `duration_seconds`

## Conventions

- Product field names are in Italian (`titolo`, `descrizione`)
- Prompts sent to Gemini are in Italian using XML structure
- Console output uses `tqdm.write()` for progress-safe logging
- Config constants defined at module level (e.g., `GEMINI_MODEL`, `MAX_RETRIES`)

## Environment

Requires `GEMINI_API_KEY` in `.env` file.
