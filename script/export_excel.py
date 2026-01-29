import os

import pandas as pd

EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "results.xlsx")

COLUMNS = [
    "id",
    "titolo",
    "descrizione-iniziale",
    "product-highlights-1",
    "product-highlights-2",
    "product-highlights-3",
    "descrizione",
    "prompt",
    "start_timestamp",
    "end_timestamp",
    "duration_seconds",
]


def export_to_excel(results: list[dict], output_path: str = None):
    """Export results to an Excel file."""
    if output_path is None:
        output_path = EXCEL_PATH

    df = pd.DataFrame(results)

    # Reorder columns, keeping only those that exist
    cols = [c for c in COLUMNS if c in df.columns]
    df = df[cols]

    df.to_excel(output_path, index=False, engine="openpyxl")
    print(f"Excel saved to {output_path} ({len(df)} rows)")
