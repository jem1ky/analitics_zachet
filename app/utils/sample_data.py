from pathlib import Path

import numpy as np
import pandas as pd


def build_sample_dataset() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    months = pd.date_range("2025-01-01", "2025-12-01", freq="MS")
    regions = ["North", "South", "East", "West"]
    categories = {
        "Electronics": ["Laptop", "Smartphone", "Headphones"],
        "Office": ["Chair", "Desk", "Monitor"],
        "Home": ["Vacuum", "Air Purifier", "Coffee Machine"],
    }

    records: list[dict[str, object]] = []
    for month in months:
        seasonal_boost = 1.18 if month.month in (11, 12) else 1.0
        for region in regions:
            for category, products in categories.items():
                product = str(rng.choice(products))
                sales = float(rng.integers(12_000, 60_000) * seasonal_boost)
                profit = round(sales * rng.uniform(0.12, 0.34), 2)
                orders = int(rng.integers(25, 120))
                customer_rating = round(float(rng.uniform(3.5, 5.0)), 2)
                records.append(
                    {
                        "date": month + pd.Timedelta(days=int(rng.integers(0, 27))),
                        "region": region,
                        "category": category,
                        "product": product,
                        "sales": round(sales, 2),
                        "profit": profit,
                        "orders": orders,
                        "customer_rating": customer_rating,
                    }
                )

    return pd.DataFrame(records).sort_values("date").reset_index(drop=True)


def ensure_sample_data(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        dataset = build_sample_dataset()
        dataset.to_csv(path, index=False)
    return path

