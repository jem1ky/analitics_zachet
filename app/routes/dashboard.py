from __future__ import annotations

from dataclasses import dataclass
from hashlib import md5

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st

from app.config.settings import APP_DESCRIPTION, APP_TITLE, REQUIRED_COLUMNS
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
    load_text_dataset,
    load_uploaded_dataset,
    prepare_dataset,
)
from app.services.export_service import (
    dataframe_to_csv_bytes,
    save_results,
    summary_to_json_bytes,
)


@dataclass(slots=True)
class UploadedBuffer:
    name: str
    payload: bytes

    def getvalue(self) -> bytes:
        return self.payload


@st.cache_data(show_spinner=False)
def get_sample_dataset():
    return load_sample_dataset()


def _init_upload_state() -> None:
    defaults = {
        "uploader_version": 0,
        "uploaded_dataset_bytes": None,
        "uploaded_dataset_name": None,
        "uploaded_dataset_token": None,
        "uploaded_dataset_error": None,
        "custom_resources": {},
        "active_resource_name": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _clear_uploaded_dataset() -> None:
    st.session_state.uploaded_dataset_bytes = None
    st.session_state.uploaded_dataset_name = None
    st.session_state.uploaded_dataset_token = None
    st.session_state.uploaded_dataset_error = None
    st.session_state.uploader_version += 1


def _build_upload_token(file_name: str, payload: bytes) -> str:
    digest = md5(payload, usedforsecurity=False).hexdigest()
    return f"{file_name}:{len(payload)}:{digest}"


def _sync_uploaded_dataset() -> None:
    uploader_key = f"upload_csv_{st.session_state.uploader_version}"
    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV file",
        type=["csv"],
        key=uploader_key,
        help="The file is kept only for the current browser session.",
    )

    if st.session_state.uploaded_dataset_error:
        st.sidebar.error(st.session_state.uploaded_dataset_error)

    if st.sidebar.button("Clear uploaded file", use_container_width=True):
        _clear_uploaded_dataset()
        st.rerun()

    if uploaded_file is None:
        return

    payload = uploaded_file.getvalue()
    token = _build_upload_token(uploaded_file.name, payload)

    if token == st.session_state.uploaded_dataset_token:
        return

    try:
        load_uploaded_dataset(uploaded_file)
    except DataValidationError as error:
        st.session_state.uploaded_dataset_error = str(error)
        st.session_state.uploaded_dataset_bytes = None
        st.session_state.uploaded_dataset_name = None
        st.session_state.uploaded_dataset_token = None
        st.session_state.uploader_version += 1
        st.rerun()

    st.session_state.uploaded_dataset_bytes = payload
    st.session_state.uploaded_dataset_name = uploaded_file.name
    st.session_state.uploaded_dataset_token = token
    st.session_state.uploaded_dataset_error = None


def _get_active_uploaded_dataset():
    if not st.session_state.uploaded_dataset_bytes:
        return None

    buffer = UploadedBuffer(
        name=st.session_state.uploaded_dataset_name or "uploaded.csv",
        payload=st.session_state.uploaded_dataset_bytes,
    )
    return load_uploaded_dataset(buffer)


def _normalize_resource_name(raw_name: str) -> str:
    return " ".join(raw_name.strip().split())


def _frame_to_records(frame: pd.DataFrame) -> list[dict[str, object]]:
    export_frame = frame[REQUIRED_COLUMNS].copy()
    export_frame["date"] = export_frame["date"].dt.strftime("%Y-%m-%d")
    return export_frame.to_dict(orient="records")


def _set_active_resource(resource_name: str | None) -> None:
    st.session_state.active_resource_name = resource_name


def _create_resource(resource_name: str) -> None:
    normalized = _normalize_resource_name(resource_name)
    if not normalized:
        raise DataValidationError("Enter a resource name before creating it.")
    if normalized in st.session_state.custom_resources:
        raise DataValidationError("A resource with this name already exists.")

    st.session_state.custom_resources[normalized] = []
    _set_active_resource(normalized)


def _delete_active_resource() -> None:
    active_name = st.session_state.active_resource_name
    if not active_name:
        return

    st.session_state.custom_resources.pop(active_name, None)
    remaining_names = sorted(st.session_state.custom_resources.keys())
    _set_active_resource(remaining_names[0] if remaining_names else None)


def _append_manual_record(resource_name: str, record: dict[str, object]) -> None:
    frame = prepare_dataset(pd.DataFrame([record]))
    valid_record = _frame_to_records(frame)[0]
    st.session_state.custom_resources.setdefault(resource_name, []).append(valid_record)


def _merge_csv_text_into_resource(resource_name: str, csv_text: str, mode: str) -> int:
    frame = load_text_dataset(csv_text)
    new_records = _frame_to_records(frame)

    if mode == "replace":
        st.session_state.custom_resources[resource_name] = new_records
    else:
        st.session_state.custom_resources.setdefault(resource_name, []).extend(new_records)

    return len(new_records)


def _get_active_resource_dataset():
    active_name = st.session_state.active_resource_name
    if not active_name:
        return None

    records = st.session_state.custom_resources.get(active_name, [])
    if not records:
        return None

    frame = pd.DataFrame(records)
    return prepare_dataset(frame)


def _render_resource_manager() -> None:
    st.sidebar.divider()
    st.sidebar.subheader("Custom resources")
    st.sidebar.caption(
        "Create separate named datasets and add rows manually or by pasted CSV text."
    )

    try:
        with st.sidebar.form("create_resource_form", clear_on_submit=True):
            resource_name = st.text_input("New resource name")
            create_resource = st.form_submit_button("Create resource", use_container_width=True)

            if create_resource:
                _create_resource(resource_name)
                st.rerun()

        resource_names = sorted(st.session_state.custom_resources.keys())
        if not resource_names:
            st.sidebar.info("Create a resource first.")
            return

        active_name = st.session_state.active_resource_name
        if active_name not in resource_names:
            active_name = resource_names[0]
            _set_active_resource(active_name)

        selected_name = st.sidebar.selectbox(
            "Active resource",
            options=resource_names,
            index=resource_names.index(active_name),
        )
        _set_active_resource(selected_name)

        resource_rows = st.session_state.custom_resources[selected_name]
        st.sidebar.caption(f"Rows in resource: {len(resource_rows)}")

        action_col1, action_col2 = st.sidebar.columns(2)
        if action_col1.button("Delete resource", use_container_width=True):
            _delete_active_resource()
            st.rerun()
        if action_col2.button("Clear rows", use_container_width=True):
            st.session_state.custom_resources[selected_name] = []
            st.rerun()

        with st.sidebar.expander("Add one record", expanded=False):
            with st.form("add_manual_record_form", clear_on_submit=True):
                date_value = st.date_input("Date")
                region = st.text_input("Region", value="North")
                category = st.text_input("Category", value="Electronics")
                product = st.text_input("Product", value="Laptop")
                sales = st.number_input("Sales", min_value=0.0, value=1000.0, step=100.0)
                profit = st.number_input("Profit", min_value=0.0, value=250.0, step=50.0)
                orders = st.number_input("Orders", min_value=0, value=10, step=1)
                customer_rating = st.number_input(
                    "Customer rating",
                    min_value=0.0,
                    max_value=5.0,
                    value=4.5,
                    step=0.1,
                )
                add_record = st.form_submit_button("Add record", use_container_width=True)

                if add_record:
                    _append_manual_record(
                        selected_name,
                        {
                            "date": date_value.isoformat(),
                            "region": region,
                            "category": category,
                            "product": product,
                            "sales": sales,
                            "profit": profit,
                            "orders": orders,
                            "customer_rating": customer_rating,
                        },
                    )
                    st.rerun()

        with st.sidebar.expander("Paste CSV into resource", expanded=False):
            with st.form("paste_csv_resource_form", clear_on_submit=False):
                paste_mode = st.radio(
                    "How to apply pasted data",
                    options=["Append rows", "Replace resource"],
                    horizontal=False,
                )
                csv_text = st.text_area(
                    "CSV text",
                    height=180,
                    placeholder=(
                        "date,region,category,product,sales,profit,orders,customer_rating\n"
                        "2025-01-01,North,Electronics,Laptop,1200,300,10,4.7"
                    ),
                )
                import_csv_text = st.form_submit_button(
                    "Import CSV text",
                    use_container_width=True,
                )

                if import_csv_text:
                    imported_rows = _merge_csv_text_into_resource(
                        selected_name,
                        csv_text,
                        "append" if paste_mode == "Append rows" else "replace",
                    )
                    st.sidebar.success(f"Imported {imported_rows} rows into '{selected_name}'.")
                    st.rerun()
    except DataValidationError as error:
        st.sidebar.error(str(error))


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


def _render_dataset_view(dataset, source_label: str) -> None:
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
        st.caption(f"Current source: {source_label}")
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
        st.caption(f"Rows in current dataset: {len(filtered_frame)}")
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


def render_dashboard():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    _init_upload_state()

    st.title(APP_TITLE)
    st.write(APP_DESCRIPTION)
    st.caption(
        "This app is fully built in Python with Streamlit. Uploaded CSV files and custom "
        "resources are separate data sources inside the interface."
    )

    st.sidebar.header("Data source")
    source = st.sidebar.radio(
        "Choose source",
        options=["Built-in sample dataset", "Upload CSV", "Custom resources"],
    )

    try:
        if source == "Upload CSV":
            _sync_uploaded_dataset()
            dataset = _get_active_uploaded_dataset()

            if dataset is None:
                st.info(
                    "Upload a CSV file in the sidebar. If the file structure is invalid, "
                    "it will be cleared and you will need to upload it again."
                )
                return

            st.sidebar.success(f"Loaded file: {st.session_state.uploaded_dataset_name}")
            _render_dataset_view(dataset, "Uploaded CSV")
            return

        if source == "Custom resources":
            _render_resource_manager()
            dataset = _get_active_resource_dataset()
            active_name = st.session_state.active_resource_name

            if not active_name:
                st.info("Create a custom resource in the sidebar to start adding data.")
                return

            if dataset is None:
                st.info(
                    f"Resource '{active_name}' is empty. Add one record or paste CSV text in the sidebar."
                )
                return

            _render_dataset_view(dataset, f"Custom resource: {active_name}")
            return

        dataset = get_sample_dataset()
        _render_dataset_view(dataset, "Built-in sample dataset")

    except DataValidationError as error:
        st.error(str(error))
    except Exception as error:
        st.error(f"Unexpected error: {error}")
