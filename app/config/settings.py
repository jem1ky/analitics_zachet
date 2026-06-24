from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
EXPORT_DIR = DATA_DIR / "exports"
SAMPLE_DATA_PATH = DATA_DIR / "sample_sales_data.csv"

APP_TITLE = "DataScope Analytics"
APP_DESCRIPTION = (
    "Browser dashboard for loading, filtering and analyzing sales data."
)

REQUIRED_COLUMNS = [
    "date",
    "region",
    "category",
    "product",
    "sales",
    "profit",
    "orders",
    "customer_rating",
]

NUMERIC_COLUMNS = ["sales", "profit", "orders", "customer_rating"]
FILTER_COLUMNS = ["region", "category", "product"]

