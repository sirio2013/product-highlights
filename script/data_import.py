import os
import pandas as pd


REQUIRED_PRODUCT_COLUMNS = {"id", "title", "description"}


def import_products(file_path: str = None) -> pd.DataFrame:
    """Import products from the CSV file and return a cleaned DataFrame."""
    if file_path is None:
        file_path = os.path.join(os.path.dirname(__file__), "..", "source", "products-list.csv")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Products file not found: {file_path}")

    df = pd.read_csv(file_path, encoding="utf-8")

    if df.empty:
        raise ValueError(f"Products file is empty: {file_path}")

    missing = REQUIRED_PRODUCT_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Products CSV missing required columns: {missing}")

    return df


def import_highlights(file_path: str = None) -> dict[str, list[str]]:
    """Import product highlights from CSV and return a dictionary.

    Returns a dict where keys are column names (e.g. 'product-highlights-1')
    and values are lists of non-empty highlight strings.
    """
    if file_path is None:
        file_path = os.path.join(os.path.dirname(__file__), "..", "source", "prod_highl.csv")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Highlights file not found: {file_path}")

    df = pd.read_csv(file_path, encoding="utf-8")

    if df.empty:
        raise ValueError(f"Highlights file is empty: {file_path}")

    highlights = {}
    for col in df.columns:
        highlights[col] = df[col].dropna().loc[df[col].str.strip() != ""].tolist()

    return highlights


if __name__ == "__main__":
    df = import_products()
    print(f"Loaded {len(df)} products")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nFirst 5 rows:\n{df[['id', 'title']].head()}")
    print(f"\nData types:\n{df.dtypes}")

    print("\n--- Product Highlights ---")
    highlights = import_highlights()
    for key, values in highlights.items():
        print(f"\n{key}:")
        for v in values:
            print(f"  - {v}")
