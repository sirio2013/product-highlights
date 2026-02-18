import asyncio
import sys

from dotenv import load_dotenv

from export_excel import export_to_excel
from gemini_client import process_products_async, save_results

load_dotenv()


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else None
    results = asyncio.run(process_products_async(n))
    save_results(results)
    export_to_excel(results)


if __name__ == "__main__":
    main()
