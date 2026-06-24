import pandas as pd
import pytest

from app.services.data_service import DataValidationError, prepare_dataset


def test_prepare_dataset_creates_helper_columns():
    frame = pd.DataFrame(
        [
            {
                "date": "2025-03-15",
                "region": "West",
                "category": "Home",
                "product": "Vacuum",
                "sales": "2000",
                "profit": "400",
                "orders": "20",
                "customer_rating": "4.6",
            }
        ]
    )

    prepared = prepare_dataset(frame)

    assert "profit_margin" in prepared.columns
    assert "avg_order_value" in prepared.columns
    assert prepared.iloc[0]["month"] == "2025-03"
    assert prepared.iloc[0]["avg_order_value"] == 100.0


def test_prepare_dataset_raises_for_missing_columns():
    frame = pd.DataFrame([{"date": "2025-03-15", "region": "West"}])

    with pytest.raises(DataValidationError):
        prepare_dataset(frame)

