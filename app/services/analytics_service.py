from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.models.filters import AnalysisFilters


def apply_filters(frame: pd.DataFrame, filters: AnalysisFilters) -> pd.DataFrame:
    filtered = frame.copy()

    if filters.start_date:
        filtered = filtered[filtered["date"].dt.date >= filters.start_date]
    if filters.end_date:
        filtered = filtered[filtered["date"].dt.date <= filters.end_date]
    if filters.regions:
        filtered = filtered[filtered["region"].isin(filters.regions)]
    if filters.categories:
        filtered = filtered[filtered["category"].isin(filters.categories)]
    if filters.products:
        filtered = filtered[filtered["product"].isin(filters.products)]

    return filtered.reset_index(drop=True)


def build_summary(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {
            "total_sales": 0.0,
            "total_profit": 0.0,
            "profit_margin_pct": 0.0,
            "average_order_value": 0.0,
            "best_region": "No data",
            "top_product": "No data",
            "sales_volatility": 0.0,
        }

    monthly_sales = frame.groupby("month", as_index=False)["sales"].sum()
    region_profit = frame.groupby("region", as_index=False)["profit"].sum()
    product_sales = frame.groupby("product", as_index=False)["sales"].sum()

    total_sales = float(frame["sales"].sum())
    total_profit = float(frame["profit"].sum())
    total_orders = float(frame["orders"].sum())

    return {
        "total_sales": round(total_sales, 2),
        "total_profit": round(total_profit, 2),
        "profit_margin_pct": round((total_profit / total_sales) * 100 if total_sales else 0.0, 2),
        "average_order_value": round(total_sales / total_orders if total_orders else 0.0, 2),
        "best_region": str(region_profit.sort_values("profit", ascending=False).iloc[0]["region"]),
        "top_product": str(product_sales.sort_values("sales", ascending=False).iloc[0]["product"]),
        "sales_volatility": round(float(np.std(monthly_sales["sales"])), 2),
    }


def build_monthly_trend(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby("month", as_index=False)[["sales", "profit", "orders"]]
        .sum()
        .sort_values("month")
    )


def build_region_breakdown(frame: pd.DataFrame) -> pd.DataFrame:
    summary = (
        frame.groupby("region", as_index=False)[["sales", "profit", "orders"]]
        .sum()
        .sort_values("sales", ascending=False)
    )
    summary["profit_margin_pct"] = np.where(
        summary["sales"] > 0,
        (summary["profit"] / summary["sales"]) * 100,
        0.0,
    )
    return summary


def build_category_performance(frame: pd.DataFrame) -> pd.DataFrame:
    summary = (
        frame.groupby(["category", "product"], as_index=False)[["sales", "profit", "orders"]]
        .sum()
        .sort_values("sales", ascending=False)
    )
    summary["avg_order_value"] = np.where(
        summary["orders"] > 0,
        summary["sales"] / summary["orders"],
        0.0,
    )
    return summary


def build_analytical_insights(frame: pd.DataFrame) -> list[str]:
    if frame.empty:
        return ["No insights available because the current filters returned no data."]

    summary = build_summary(frame)
    rating_by_region = frame.groupby("region", as_index=False)["customer_rating"].mean()
    strongest_region = rating_by_region.sort_values("customer_rating", ascending=False).iloc[0]
    weakest_margin = (
        frame.groupby("category", as_index=False)["profit_margin"].mean()
        .sort_values("profit_margin", ascending=True)
        .iloc[0]
    )

    return [
        f"Top sales driver: {summary['top_product']} with region leader {summary['best_region']}.",
        (
            f"Best customer satisfaction is in {strongest_region['region']}: "
            f"{strongest_region['customer_rating']:.2f} average rating."
        ),
        (
            f"The weakest margin is in category {weakest_margin['category']}: "
            f"{weakest_margin['profit_margin'] * 100:.2f}% average margin."
        ),
    ]

