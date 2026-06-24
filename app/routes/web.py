from __future__ import annotations

import base64
from io import BytesIO

import matplotlib
import pandas as pd
import plotly.express as px
from flask import Response, render_template, request

from app.config.settings import APP_DESCRIPTION, APP_TITLE
from app.models.filters import AnalysisFilters
from app.services.analytics_service import (
    apply_filters,
    build_analytical_insights,
    build_category_performance,
    build_monthly_trend,
    build_region_breakdown,
    build_summary,
)
from app.services.data_service import (
    DataValidationError,
    load_sample_dataset,
    load_uploaded_dataset,
)
from app.services.export_service import dataframe_to_csv_bytes, summary_to_json_bytes

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _parse_text_list(raw_value: str) -> list[str]:
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _get_date_value(raw_value: str):
    if not raw_value:
        return None
    return pd.to_datetime(raw_value, errors="coerce").date()


def _build_filters_from_query(frame: pd.DataFrame) -> AnalysisFilters:
    min_date = frame["date"].min().date()
    max_date = frame["date"].max().date()
    return AnalysisFilters(
        start_date=_get_date_value(request.args.get("start_date", "")) or min_date,
        end_date=_get_date_value(request.args.get("end_date", "")) or max_date,
        regions=request.args.getlist("region"),
        categories=request.args.getlist("category"),
        products=request.args.getlist("product"),
    )


def _build_filters_from_form(frame: pd.DataFrame) -> AnalysisFilters:
    min_date = frame["date"].min().date()
    max_date = frame["date"].max().date()
    return AnalysisFilters(
        start_date=_get_date_value(request.form.get("start_date", "")) or min_date,
        end_date=_get_date_value(request.form.get("end_date", "")) or max_date,
        regions=_parse_text_list(request.form.get("regions", "")),
        categories=_parse_text_list(request.form.get("categories", "")),
        products=_parse_text_list(request.form.get("products", "")),
    )


def _build_histogram_image(frame: pd.DataFrame) -> str:
    figure, axis = plt.subplots(figsize=(8, 4))
    axis.hist(frame["customer_rating"], bins=8, color="#ea580c", edgecolor="white")
    axis.set_title("Customer rating distribution")
    axis.set_xlabel("Rating")
    axis.set_ylabel("Frequency")
    figure.tight_layout()

    buffer = BytesIO()
    figure.savefig(buffer, format="png", dpi=140, bbox_inches="tight")
    plt.close(figure)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def _build_chart_html(frame: pd.DataFrame) -> dict[str, str]:
    monthly_trend = build_monthly_trend(frame)
    region_breakdown = build_region_breakdown(frame)
    category_performance = build_category_performance(frame)

    trend_chart = px.line(
        monthly_trend,
        x="month",
        y=["sales", "profit"],
        markers=True,
        title="Monthly trend",
    )
    trend_chart.update_layout(
        template="plotly_white",
        legend_title_text="Metric",
        margin=dict(l=20, r=20, t=50, b=20),
    )

    region_chart = px.bar(
        region_breakdown,
        x="region",
        y="sales",
        color="profit_margin_pct",
        title="Sales by region",
        text_auto=".2s",
        color_continuous_scale="Oranges",
    )
    region_chart.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20),
    )

    bubble_chart = px.scatter(
        category_performance,
        x="sales",
        y="profit",
        size="orders",
        color="category",
        hover_name="product",
        title="Category and product performance",
    )
    bubble_chart.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return {
        "trend": trend_chart.to_html(full_html=False, include_plotlyjs="cdn"),
        "region": region_chart.to_html(full_html=False, include_plotlyjs=False),
        "bubble": bubble_chart.to_html(full_html=False, include_plotlyjs=False),
        "histogram": _build_histogram_image(frame),
    }


def _format_table(frame: pd.DataFrame, columns: list[str], limit: int = 20) -> str:
    preview = frame[columns].head(limit).copy()
    if "date" in preview.columns:
        preview["date"] = preview["date"].dt.strftime("%Y-%m-%d")
    return preview.to_html(
        classes="data-table",
        index=False,
        border=0,
        justify="left",
    )


def _build_dashboard_context(frame: pd.DataFrame, filters: AnalysisFilters, source_name: str) -> dict:
    filtered_frame = apply_filters(frame, filters)
    empty = filtered_frame.empty

    context = {
        "source_name": source_name,
        "filters": filters,
        "row_count": len(filtered_frame),
        "empty": empty,
        "date_min": frame["date"].min().date().isoformat(),
        "date_max": frame["date"].max().date().isoformat(),
    }

    if empty:
        context.update(
            {
                "summary": build_summary(filtered_frame),
                "insights": ["No rows match the selected filters."],
                "charts": None,
                "table_html": "",
            }
        )
        return context

    summary = build_summary(filtered_frame)
    context.update(
        {
            "summary": summary,
            "insights": build_analytical_insights(filtered_frame),
            "charts": _build_chart_html(filtered_frame),
            "table_html": _format_table(
                filtered_frame,
                [
                    "date",
                    "region",
                    "category",
                    "product",
                    "sales",
                    "profit",
                    "orders",
                    "customer_rating",
                ],
            ),
        }
    )
    return context


def _build_sample_context() -> dict:
    sample_frame = load_sample_dataset()
    filters = _build_filters_from_query(sample_frame)
    context = _build_dashboard_context(sample_frame, filters, "Built-in sample dataset")
    context["options"] = {
        "regions": sorted(sample_frame["region"].unique().tolist()),
        "categories": sorted(sample_frame["category"].unique().tolist()),
        "products": sorted(sample_frame["product"].unique().tolist()),
    }
    return context


def register_routes(app):
    @app.get("/")
    def index():
        sample_context = _build_sample_context()
        return render_template(
            "index.html",
            app_title=APP_TITLE,
            app_description=APP_DESCRIPTION,
            sample=sample_context,
            upload=None,
            upload_error=None,
        )

    @app.post("/upload")
    def upload():
        sample_context = _build_sample_context()

        try:
            uploaded_file = request.files.get("dataset")
            dataset = load_uploaded_dataset(uploaded_file)
            filters = _build_filters_from_form(dataset)
            upload_context = _build_dashboard_context(
                dataset,
                filters,
                uploaded_file.filename or "Uploaded CSV",
            )

            action = request.form.get("action", "analyze")
            filtered_frame = apply_filters(dataset, filters)
            summary = build_summary(filtered_frame)

            if action == "download_csv":
                return Response(
                    dataframe_to_csv_bytes(filtered_frame),
                    mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=filtered_dataset.csv"},
                )
            if action == "download_json":
                return Response(
                    summary_to_json_bytes(summary),
                    mimetype="application/json",
                    headers={"Content-Disposition": "attachment; filename=analytics_summary.json"},
                )

            return render_template(
                "index.html",
                app_title=APP_TITLE,
                app_description=APP_DESCRIPTION,
                sample=sample_context,
                upload=upload_context,
                upload_error=None,
            )
        except DataValidationError as error:
            return render_template(
                "index.html",
                app_title=APP_TITLE,
                app_description=APP_DESCRIPTION,
                sample=sample_context,
                upload=None,
                upload_error=str(error),
            )
        except Exception as error:
            return render_template(
                "index.html",
                app_title=APP_TITLE,
                app_description=APP_DESCRIPTION,
                sample=sample_context,
                upload=None,
                upload_error=f"Unexpected error: {error}",
            )
