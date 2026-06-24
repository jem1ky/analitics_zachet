from datetime import date

import pandas as pd

from app.models.filters import AnalysisFilters
from app.services.analytics_service import apply_filters, build_summary
from app.services.data_service import prepare_dataset


def build_test_frame() -> pd.DataFrame:
    raw_frame = pd.DataFrame(
        [
            {
                "date": "2025-01-05",
                "region": "North",
                "category": "Electronics",
                "product": "Laptop",
                "sales": 1000,
                "profit": 250,
                "orders": 10,
                "customer_rating": 4.8,
            },
            {
                "date": "2025-02-10",
                "region": "South",
                "category": "Office",
                "product": "Desk",
                "sales": 800,
                "profit": 160,
                "orders": 8,
                "customer_rating": 4.3,
            },
        ]
    )
    return prepare_dataset(raw_frame)


def test_apply_filters_returns_only_requested_region():
    frame = build_test_frame()
    filters = AnalysisFilters(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        regions=["North"],
    )

    filtered = apply_filters(frame, filters)

    assert len(filtered) == 1
    assert filtered.iloc[0]["region"] == "North"


def test_build_summary_calculates_expected_values():
    frame = build_test_frame()

    summary = build_summary(frame)

    assert summary["total_sales"] == 1800.0
    assert summary["total_profit"] == 410.0
    assert summary["best_region"] in {"North", "South"}
    assert summary["top_product"] == "Laptop"

