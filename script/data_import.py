import os
import pandas as pd


REQUIRED_PRODUCT_COLUMNS = {"id", "title", "description"}


def resolve_source_path(filename: str) -> str:
    """Resolve path to file in source/ directory."""
    return os.path.join(os.path.dirname(__file__), "..", "source", filename)


def load_csv_validated(file_path: str, required_columns: set = None) -> pd.DataFrame:
    """Load CSV with existence and column validation."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    df = pd.read_csv(file_path, encoding="utf-8")

    if df.empty:
        raise ValueError(f"File is empty: {file_path}")

    if required_columns:
        missing = required_columns - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns: {missing}")

    return df


def import_products(file_path: str = None) -> pd.DataFrame:
    """Import products from the CSV file and return a cleaned DataFrame."""
    if file_path is None:
        file_path = resolve_source_path("products-list.csv")
    return load_csv_validated(file_path, REQUIRED_PRODUCT_COLUMNS)


def import_highlights(file_path: str = None) -> dict[str, list[str]]:
    """Import product highlights from CSV and return a dictionary.

    Returns a dict where keys are column names (e.g. 'product-highlights-1')
    and values are lists of non-empty highlight strings.
    """
    if file_path is None:
        file_path = resolve_source_path("prod_highl.csv")

    df = load_csv_validated(file_path)

    return {
        col: df[col].dropna().loc[df[col].str.strip() != ""].tolist()
        for col in df.columns
    }


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
