from __future__ import annotations

from io import BytesIO

import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError, ParserError

from app.config.settings import NUMERIC_COLUMNS, REQUIRED_COLUMNS, SAMPLE_DATA_PATH
from app.utils.sample_data import ensure_sample_data


class DataValidationError(ValueError):
    """Raised when the uploaded dataset cannot be analyzed safely."""


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame.columns = [
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        for column in frame.columns
    ]
    return frame


def validate_columns(frame: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        missing_columns = ", ".join(missing)
        raise DataValidationError(
            f"Missing required columns: {missing_columns}. "
            "Expected columns: date, region, category, product, sales, profit, orders, customer_rating."
        )


def prepare_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        raise DataValidationError("The dataset is empty. Upload a CSV file with data.")

    prepared = normalize_columns(frame.copy())
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
            return pd.read_csv(BytesIO(payload), encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise DataValidationError("The file encoding is not supported. Use UTF-8 or CP1251 CSV.")


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

