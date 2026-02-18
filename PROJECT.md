# Products Highlights

## Overview
Application for the marketing team to manage and highlight products.
For each product, the app uses Gemini AI to select the most relevant product highlights
from a predefined set and integrates them into the product description as HTML.

## Data Sources

### products-list.csv
390 pet products with 3 columns:
| Column | Type | Description |
|---|---|---|
| `id` | int | Product ID |
| `title` | str | Product name (Italian) |
| `description` | str | Long product description (Italian) |

### prod_highl.csv
Predefined product highlights organized in 3 groups:
| Column | Description |
|---|---|
| `product-highlights-1` | Action/efficacy highlights (30 values) |
| `product-highlights-2` | Duration/protection highlights (30 values) |
| `product-highlights-3` | Application format highlights (30 values) |

## Project Structure

| File / Folder | Description |
|---|---|
| `script/main.py` | Entry point — runs the full pipeline for N products |
| `script/data_import.py` | CSV import functions with validation (`import_products`, `import_highlights`) |
| `script/prompt_builder.py` | Builds the Gemini prompt for each product (`build_prompt`) |
| `script/gemini_client.py` | Gemini API calls with retry logic, JSON extraction, sequential batch processing |
| `script/export_excel.py` | Exports results to Excel (`export_to_excel`) |
| `source/products-list.csv` | Product catalog (390 products) |
| `source/prod_highl.csv` | Predefined product highlights (3 groups × 30 values) |
| `.env` | API key (GEMINI_API_KEY) — not committed to version control |
| `.gitignore` | Excludes `.env`, `venv/`, `__pycache__/` from version control |
| `requirements.txt` | Python dependencies (pandas, requests, python-dotenv, tqdm, openpyxl) |
| `results.json` | Output — processed products in JSON format |
| `results.xlsx` | Output — processed products in Excel format |

## Workflow

```
 python script/main.py [n]
          |
          v
 +------------------+
 | 1. DATA IMPORT   |  data_import.py
 |                  |
 |  products-list   |---> DataFrame (390 products)
 |  .csv            |
 |                  |
 |  prod_highl      |---> dict (3 groups, 90 highlights total)
 |  .csv            |
 +--------+---------+
          |
          v
 +------------------+
 | 2. DEDUPLICATION |  gemini_client.py
 |                  |
 |  Load results    |
 |  .json           |---> processed IDs
 |                  |
 |  Filter out      |
 |  already done    |
 +--------+---------+
          |
          v
 +------------------+
 | 3. SEQUENTIAL    |  gemini_client.py + prompt_builder.py
 |    PROCESSING    |
 |                  |
 |  For each product:
 |  a. build_prompt()    --> Italian XML prompt
 |  b. call_gemini()     --> Gemini API (with retry)
 |  c. extract_json()    --> parse response
 |  d. ensure_html()     --> wrap in <p> tags
 |  e. validate_highlights() --> warn if missing
 |  f. save_results()    --> incremental JSON save
 +--------+---------+
          |
          v
 +------------------+
 | 4. SAVE JSON     |  gemini_client.py
 |                  |
 |  results.json    |---> atomic write (temp + rename)
 +--------+---------+
          |
          v
 +------------------+
 | 5. EXPORT EXCEL  |  export_excel.py
 |                  |
 |  results.xlsx    |---> all columns via pandas + openpyxl
 +------------------+
```

## Workflow Validation

The complete workflow has been tested and validated (2026-02-04):

✅ **Step 1: Data Import** - Successfully loads 390 products and 30 highlights per group
✅ **Step 2: Prompt Builder** - Generates correct Italian XML prompt with all highlights
✅ **Step 3: Gemini Processing** - Processes products with retry logic (~51s per product)
✅ **Step 4: Output Validation** - All 3 highlights correctly integrated in HTML descriptions
✅ **Step 5: File Generation** - Creates results.json and results.xlsx with all 11 columns

### Step 1: Data Import
- Module: `script/data_import.py`
- `import_products()` — reads `source/products-list.csv`, validates required columns, returns a pandas DataFrame (390 products)
- `import_highlights()` — reads `source/prod_highl.csv`, validates non-empty, returns a dict of highlight lists (3 groups × 30 values)

### Step 2: Deduplication
- Module: `script/gemini_client.py`
- Loads existing `results.json` (if present)
- Extracts already-processed product IDs
- Filters the product list to skip duplicates

### Step 3: Sequential AI Processing
- Module: `script/gemini_client.py` + `script/prompt_builder.py`
- Model: `gemini-3-flash-preview` with MEDIUM thinking level
- Sequential processing — one product at a time
- Retry logic with exponential backoff (up to 3 attempts per product)
- Per-product error handling — failures are logged but don't stop the batch
- Post-processing: ensures all descriptions are wrapped in `<p>` tags
- Validation: warns if selected highlights are not found in the rewritten description
- Incremental save: `results.json` is updated after each product

### Step 4: Save JSON
- Module: `script/gemini_client.py`
- `save_results(results)` — atomic write to `results.json` (write to temp file, then rename)

### Step 5: Export Excel
- Module: `script/export_excel.py`
- `export_to_excel(results)` — converts results to `results.xlsx` using pandas + openpyxl
- All 11 columns exported in order: `id`, `titolo`, `descrizione-iniziale`, `product-highlights-1/2/3`, `descrizione`, `prompt`, `start_timestamp`, `end_timestamp`, `duration_seconds`

### Output Format
Each product result contains these fields (both in JSON and Excel):
```json
{
  "id": 9034956,
  "titolo": "Product title",
  "descrizione-iniziale": "Original description",
  "product-highlights-1": "Selected highlight",
  "product-highlights-2": "Selected highlight",
  "product-highlights-3": "Selected highlight",
  "descrizione": "<p>Description with highlights integrated as HTML</p>",
  "prompt": "Complete prompt sent to Gemini",
  "start_timestamp": "2026-01-29T13:33:21.393688",
  "end_timestamp": "2026-01-29T13:33:50.283216",
  "duration_seconds": 28.89
}
```

## Usage

```bash
# Activate virtual environment
venv\Scripts\activate

# Process first N products
python script/main.py 5

# Process all products
python script/main.py
```

Output files are saved in the project root:
- `results.json` — JSON format (updated incrementally during processing)
- `results.xlsx` — Excel format (generated at the end of the run)

## Tech Stack
- Python 3.14
- pandas — data manipulation and Excel export
- requests — direct Gemini REST API calls with retry logic
- python-dotenv — environment variable loading
- tqdm — progress bar
- openpyxl — Excel file writing engine
- Run locally via `script/main.py`
