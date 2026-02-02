# CLAUDE.md

## Project Overview

Product Highlights is a Python CLI tool that uses Google Gemini AI to select and integrate product highlights into Italian pet care product descriptions. It processes CSV product data, sends prompts to Gemini, and exports results as JSON and Excel.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run on first N products
python script/main.py 5

# Run on all products
python script/main.py
```

There is no test suite, linter, or CI/CD pipeline.

## Architecture

Entry point: `script/main.py`

Pipeline: CSV import → deduplication (skip already-processed) → Gemini AI processing → JSON save → Excel export

```
script/
  main.py            # Entry point, orchestration
  data_import.py     # CSV loading and validation
  prompt_builder.py  # Italian XML prompt generation for Gemini
  gemini_client.py   # Gemini API calls, retry logic, response parsing
  export_excel.py    # Excel export via openpyxl
source/
  products-list.csv  # 97 pet products (Italian)
  prod_highl_antip.csv  # 14 predefined highlights in 3 groups
```

## Key Conventions

- **Python 3.14** with type hints throughout
- **snake_case** for functions/variables, **UPPERCASE** for constants
- Product field names are in Italian (`titolo`, `descrizione`)
- Prompts sent to Gemini are in Italian using XML structure
- Console output uses `tqdm.write()` for progress-safe logging
- Config constants defined at module level (e.g., `GEMINI_MODEL`, `MAX_RETRIES`)
- Atomic file writes using temp file + rename pattern
- Incremental saves to `results.json` after each product
- Exponential backoff retry logic (max 3 attempts) for API calls

## Environment

- Requires `GEMINI_API_KEY` set via environment variable or `.env` file
- Model: `gemini-3-flash-preview` with MEDIUM thinking level
- Output files: `results.json`, `results.xlsx`
