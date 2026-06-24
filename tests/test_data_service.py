import pandas as pd
import pytest

from app.services.data_service import DataValidationError, load_text_dataset, prepare_dataset


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


def test_load_text_dataset_accepts_valid_csv_text():
    csv_text = """date,region,category,product,sales,profit,orders,customer_rating
2025-04-01,North,Electronics,Laptop,1500,300,12,4.8
"""

    prepared = load_text_dataset(csv_text)

    assert len(prepared) == 1
    assert prepared.iloc[0]["product"] == "Laptop"
    assert prepared.iloc[0]["month"] == "2025-04"


def test_prepare_dataset_adapts_russian_column_names():
    frame = pd.DataFrame(
        [
            {
                "дата": "2025-05-01",
                "регион": "Север",
                "категория": "Электроника",
                "товар": "Ноутбук",
                "продажи": 2400,
                "прибыль": 480,
                "заказы": 12,
                "рейтинг клиента": 4.9,
            }
        ]
    )

    prepared = prepare_dataset(frame)

    assert list(prepared[["region", "category", "product"]].iloc[0]) == [
        "Север",
        "Электроника",
        "Ноутбук",
    ]
    assert prepared.iloc[0]["customer_rating"] == 4.9


def test_prepare_dataset_derives_profit_from_sales_and_cost():
    frame = pd.DataFrame(
        [
            {
                "order date": "2025-05-02",
                "sales region": "West",
                "department": "Office",
                "item": "Chair",
                "revenue": 1000,
                "cost": 760,
                "quantity": 5,
                "rating": 4.4,
            }
        ]
    )

    prepared = prepare_dataset(frame)

    assert prepared.iloc[0]["sales"] == 1000
    assert prepared.iloc[0]["profit"] == 240
    assert prepared.iloc[0]["orders"] == 5
