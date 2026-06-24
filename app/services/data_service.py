from __future__ import annotations

from io import BytesIO, StringIO
import re

import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError, ParserError

from app.config.settings import NUMERIC_COLUMNS, REQUIRED_COLUMNS, SAMPLE_DATA_PATH
from app.utils.sample_data import ensure_sample_data


class DataValidationError(ValueError):
    """Raised when the uploaded dataset cannot be analyzed safely."""


COLUMN_ALIASES = {
    "date": [
        "date",
        "order_date",
        "sale_date",
        "transaction_date",
        "report_date",
        "дата",
        "дата_продажи",
        "дата_заказа",
    ],
    "region": [
        "region",
        "area",
        "territory",
        "market",
        "location",
        "geo_region",
        "sales_region",
        "регион",
        "область",
        "район",
        "территория",
        "рынок",
        "локация",
    ],
    "category": [
        "category",
        "segment",
        "department",
        "group",
        "product_category",
        "категория",
        "сегмент",
        "отдел",
        "группа",
        "тип",
    ],
    "product": [
        "product",
        "item",
        "product_name",
        "item_name",
        "sku_name",
        "товар",
        "продукт",
        "наименование",
        "название_товара",
        "позиция",
    ],
    "sales": [
        "sales",
        "revenue",
        "amount",
        "total_sales",
        "turnover",
        "income",
        "выручка",
        "продажи",
        "сумма",
        "сумма_продаж",
        "оборот",
        "доход",
    ],
    "profit": [
        "profit",
        "net_profit",
        "gross_profit",
        "margin_value",
        "прибыль",
        "чистая_прибыль",
        "валовая_прибыль",
        "маржа",
    ],
    "orders": [
        "orders",
        "order_count",
        "quantity",
        "units",
        "units_sold",
        "qty",
        "заказы",
        "количество",
        "кол_во",
        "шт",
    ],
    "customer_rating": [
        "customer_rating",
        "rating",
        "review_score",
        "score",
        "stars",
        "customer_score",
        "рейтинг_клиента",
        "рейтинг",
        "оценка_клиента",
        "оценка",
    ],
}

PROFIT_SOURCE_ALIASES = [
    "cost",
    "costs",
    "expense",
    "expenses",
    "cogs",
    "total_cost",
    "cost_price",
    "себестоимость",
    "затраты",
    "расходы",
]


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame.columns = [
        re.sub(r"_+", "_", str(column).strip().lower().replace(" ", "_").replace("-", "_"))
        .strip("_")
        for column in frame.columns
    ]
    return frame


def apply_column_aliases(frame: pd.DataFrame) -> pd.DataFrame:
    renamed_columns: dict[str, str] = {}
    current_columns = set(frame.columns)

    for canonical_name, aliases in COLUMN_ALIASES.items():
        if canonical_name in current_columns:
            continue

        for alias in aliases:
            if alias in current_columns:
                renamed_columns[alias] = canonical_name
                current_columns.remove(alias)
                current_columns.add(canonical_name)
                break

    if renamed_columns:
        frame = frame.rename(columns=renamed_columns)

    return frame


def derive_missing_columns(frame: pd.DataFrame) -> pd.DataFrame:
    if "profit" not in frame.columns and "sales" in frame.columns:
        for cost_alias in PROFIT_SOURCE_ALIASES:
            if cost_alias in frame.columns:
                sales_series = pd.to_numeric(frame["sales"], errors="coerce")
                cost_series = pd.to_numeric(frame[cost_alias], errors="coerce")
                frame["profit"] = sales_series - cost_series
                break

    return frame


def validate_columns(frame: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        missing_columns = ", ".join(missing)
        raise DataValidationError(
            f"Missing required columns: {missing_columns}. "
            "Expected columns: date, region, category, product, sales, profit, orders, customer_rating. "
            "The app also tries to adapt common English and Russian aliases automatically."
        )


def prepare_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        raise DataValidationError("The dataset is empty. Upload a CSV file with data.")

    prepared = normalize_columns(frame.copy())
    prepared = apply_column_aliases(prepared)
    prepared = derive_missing_columns(prepared)
    validate_columns(prepared)

    prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce")
    for column in NUMERIC_COLUMNS:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")

    prepared = prepared.dropna(subset=["date", *NUMERIC_COLUMNS])
    if prepared.empty:
        raise DataValidationError(
            "All rows were removed during cleaning. Check date and numeric values in the file."
        )

    prepared["sales"] = prepared["sales"].clip(lower=0)
    prepared["orders"] = prepared["orders"].clip(lower=0)
    prepared["profit_margin"] = np.where(
        prepared["sales"] > 0,
        prepared["profit"] / prepared["sales"],
        0.0,
    )
    prepared["avg_order_value"] = np.where(
        prepared["orders"] > 0,
        prepared["sales"] / prepared["orders"],
        0.0,
    )
    prepared["month"] = prepared["date"].dt.to_period("M").astype(str)

    return prepared.sort_values("date").reset_index(drop=True)


def _read_csv_bytes(payload: bytes) -> pd.DataFrame:
    for encoding in ("utf-8", "utf-8-sig", "cp1251"):
        try:
            return pd.read_csv(BytesIO(payload), encoding=encoding, sep=None, engine="python")
        except UnicodeDecodeError:
            continue
    raise DataValidationError("The file encoding is not supported. Use UTF-8 or CP1251 CSV.")


def load_text_dataset(csv_text: str) -> pd.DataFrame:
    if not csv_text or not csv_text.strip():
        raise DataValidationError("CSV text is empty. Paste data with headers and rows.")

    try:
        frame = pd.read_csv(StringIO(csv_text.strip()), sep=None, engine="python")
    except EmptyDataError as error:
        raise DataValidationError("The pasted CSV text is empty.") from error
    except ParserError as error:
        raise DataValidationError("Could not parse the pasted CSV text.") from error

    return prepare_dataset(frame)


def load_uploaded_dataset(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        raise DataValidationError("No file was uploaded.")

    try:
        payload = uploaded_file.getvalue()
        frame = _read_csv_bytes(payload)
    except EmptyDataError as error:
        raise DataValidationError("The uploaded file is empty.") from error
    except ParserError as error:
        raise DataValidationError("Could not parse the CSV file. Check separators and headers.") from error

    return prepare_dataset(frame)


def load_sample_dataset() -> pd.DataFrame:
    sample_path = ensure_sample_data(SAMPLE_DATA_PATH)
    frame = pd.read_csv(sample_path)
    return prepare_dataset(frame)
