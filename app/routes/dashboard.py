from __future__ import annotations

import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st

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
from app.services.export_service import (
    dataframe_to_csv_bytes,
    save_results,
    summary_to_json_bytes,
)


@st.cache_data(show_spinner=False)
def get_sample_dataset():
    return load_sample_dataset()


def render_filters(frame):
    min_date = frame["date"].min().date()
    max_date = frame["date"].max().date()

    st.sidebar.header("Filters")
    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    regions = st.sidebar.multiselect(
        "Region",
        options=sorted(frame["region"].unique().tolist()),
    )
    categories = st.sidebar.multiselect(
        "Category",
        options=sorted(frame["category"].unique().tolist()),
    )
    products = st.sidebar.multiselect(
        "Product",
        options=sorted(frame["product"].unique().tolist()),
    )

    return AnalysisFilters(
        start_date=start_date,
        end_date=end_date,
        regions=regions,
        categories=categories,
        products=products,
    )


def render_metrics(summary):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total sales", f"${summary['total_sales']:,.0f}")
    col2.metric("Total profit", f"${summary['total_profit']:,.0f}")
    col3.metric("Margin", f"{summary['profit_margin_pct']:.2f}%")
    col4.metric("Avg order value", f"${summary['average_order_value']:,.0f}")


def render_charts(filtered_frame):
    monthly_trend = build_monthly_trend(filtered_frame)
    region_breakdown = build_region_breakdown(filtered_frame)
    category_performance = build_category_performance(filtered_frame)

    trend_chart = px.line(
        monthly_trend,
        x="month",
        y=["sales", "profit"],
        markers=True,
        title="Monthly trend",
    )
    trend_chart.update_layout(legend_title_text="Metric")

    region_chart = px.bar(
        region_breakdown,
        x="region",
        y="sales",
        color="profit_margin_pct",
        title="Sales by region",
        text_auto=".2s",
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

    left, right = st.columns(2)
    left.plotly_chart(trend_chart, use_container_width=True)
    right.plotly_chart(region_chart, use_container_width=True)
    st.plotly_chart(bubble_chart, use_container_width=True)

    fig, axis = plt.subplots(figsize=(8, 4))
    axis.hist(filtered_frame["customer_rating"], bins=8, color="#1f77b4", edgecolor="white")
    axis.set_title("Customer rating distribution")
    axis.set_xlabel("Rating")
    axis.set_ylabel("Frequency")
    st.pyplot(fig)
    plt.close(fig)


def render_dashboard():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)
    st.write(APP_DESCRIPTION)

    st.sidebar.header("Data source")
    source = st.sidebar.radio(
        "Choose source",
        options=["Built-in sample dataset", "Upload CSV"],
    )

    try:
        if source == "Upload CSV":
            uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
            if uploaded_file is None:
                st.info("Upload a CSV file or switch to the built-in sample dataset.")
                return
            dataset = load_uploaded_dataset(uploaded_file)
        else:
            dataset = get_sample_dataset()

        filters = render_filters(dataset)
        filtered_frame = apply_filters(dataset, filters)
        summary = build_summary(filtered_frame)

        if filtered_frame.empty:
            st.warning("No rows match the selected filters. Adjust the filters and try again.")
            return

        tab_overview, tab_visuals, tab_export = st.tabs(
            ["Overview", "Visualizations", "Data and export"]
        )

        with tab_overview:
            render_metrics(summary)
            st.subheader("Analytical summary")
            st.write(
                f"Best region: {summary['best_region']} | "
                f"Top product: {summary['top_product']} | "
                f"Sales volatility: ${summary['sales_volatility']:,.0f}"
            )
            for insight in build_analytical_insights(filtered_frame):
                st.write(f"- {insight}")

        with tab_visuals:
            render_charts(filtered_frame)

        with tab_export:
            preview_columns = [
                "date",
                "region",
                "category",
                "product",
                "sales",
                "profit",
                "orders",
                "customer_rating",
            ]
            st.subheader("Filtered data")
            st.dataframe(filtered_frame[preview_columns], use_container_width=True)

            csv_bytes = dataframe_to_csv_bytes(filtered_frame)
            json_bytes = summary_to_json_bytes(summary)

            download_col1, download_col2 = st.columns(2)
            download_col1.download_button(
                "Download filtered CSV",
                data=csv_bytes,
                file_name="filtered_dataset.csv",
                mime="text/csv",
            )
            download_col2.download_button(
                "Download summary JSON",
                data=json_bytes,
                file_name="analytics_summary.json",
                mime="application/json",
            )

            if st.button("Save results into data/exports"):
                dataset_path, summary_path = save_results(filtered_frame, summary)
                st.success(
                    "Files saved successfully:\n"
                    f"- {dataset_path}\n"
                    f"- {summary_path}"
                )

    except DataValidationError as error:
        st.error(str(error))
    except Exception as error:
        st.error(f"Unexpected error: {error}")

