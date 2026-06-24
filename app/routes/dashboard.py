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


LANGUAGE_OPTIONS = {"Русский": "ru", "English": "en"}

TEXT = {
    "ru": {
        "app_description": "Браузерная аналитика данных полностью на Python.",
        "app_caption": (
            "Приложение полностью сделано на Python с помощью Streamlit. "
            "Загруженные CSV и кастомные ресурсы работают как отдельные источники данных."
        ),
        "language": "Язык",
        "data_source": "Источник данных",
        "choose_source": "Выберите источник",
        "source_sample": "Встроенный пример",
        "source_upload": "Загрузить CSV",
        "source_resources": "Кастомные ресурсы",
        "filters": "Фильтры",
        "date_range": "Диапазон дат",
        "region": "Регион",
        "category": "Категория",
        "product": "Товар",
        "overview": "Обзор",
        "visualizations": "Визуализации",
        "data_export": "Данные и экспорт",
        "analytical_summary": "Аналитическая сводка",
        "current_source": "Текущий источник: {source}",
        "best_region": "Лучший регион",
        "top_product": "Топ-товар",
        "sales_volatility": "Колебание продаж",
        "total_sales": "Общая сумма продаж",
        "total_profit": "Общая прибыль",
        "margin": "Маржинальность",
        "avg_order_value": "Средний чек",
        "filtered_data": "Отфильтрованные данные",
        "rows_count": "Строк в текущем наборе: {count}",
        "download_csv": "Скачать CSV",
        "download_json": "Скачать JSON",
        "save_results": "Сохранить результаты в data/exports",
        "saved_ok": "Файлы успешно сохранены:\n- {dataset}\n- {summary}",
        "upload_file": "Загрузите CSV файл",
        "upload_help": "Файл хранится только в рамках текущей сессии браузера.",
        "clear_file": "Очистить загруженный файл",
        "loaded_file": "Загружен файл: {name}",
        "upload_info": (
            "Загрузите CSV в сайдбаре. Если структура файла некорректна, "
            "он будет очищен, и его нужно будет загрузить заново."
        ),
        "custom_resources": "Кастомные ресурсы",
        "custom_caption": (
            "Создавайте отдельные именованные наборы данных и добавляйте строки вручную "
            "или через вставку CSV-текста."
        ),
        "new_resource_name": "Название нового ресурса",
        "create_resource": "Создать ресурс",
        "create_first_resource": "Сначала создайте ресурс.",
        "active_resource": "Активный ресурс",
        "rows_in_resource": "Строк в ресурсе: {count}",
        "delete_resource": "Удалить ресурс",
        "clear_rows": "Очистить строки",
        "add_one_record": "Добавить одну запись",
        "date": "Дата",
        "unit_price": "Sales (цена за 1 товар)",
        "unit_price_help": "Для ручного ввода здесь указывается цена за одну единицу товара.",
        "profit_total": "Profit (прибыль по строке)",
        "orders": "Количество / orders",
        "customer_rating": "Рейтинг клиента",
        "add_record": "Добавить запись",
        "paste_csv": "Вставить CSV в ресурс",
        "apply_mode": "Как применить вставленные данные",
        "append_rows": "Добавить строки",
        "replace_resource": "Заменить ресурс",
        "csv_text": "CSV текст",
        "import_csv_text": "Импортировать CSV текст",
        "imported_rows": "Импортировано {count} строк в ресурс '{name}'.",
        "resource_empty": "Ресурс '{name}' пуст. Добавьте запись или вставьте CSV-текст в сайдбаре.",
        "create_resource_first": "Создайте кастомный ресурс в сайдбаре, чтобы начать добавлять данные.",
        "no_rows": "По текущим фильтрам нет данных. Измените фильтры и попробуйте снова.",
        "source_uploaded": "Загруженный CSV",
        "source_resource": "Кастомный ресурс: {name}",
        "source_sample_label": "Встроенный пример",
        "insight_top": "Лидер по продажам: {product}. Лучший регион: {region}.",
        "insight_rating": "Лучшая оценка клиентов в регионе {region}: {rating:.2f}.",
        "insight_margin": "Самая слабая средняя маржа у категории {category}: {margin:.2f}%.",
        "chart_monthly": "Динамика по месяцам",
        "chart_region": "Продажи по регионам",
        "chart_category": "Эффективность категорий и товаров",
        "chart_rating": "Распределение рейтинга клиентов",
        "metric_legend": "Метрика",
        "resource_name_required": "Введите название ресурса перед созданием.",
        "resource_exists": "Ресурс с таким названием уже существует.",
        "unexpected_error": "Непредвиденная ошибка: {error}",
        "preview_date": "Дата",
        "preview_region": "Регион",
        "preview_category": "Категория",
        "preview_product": "Товар",
        "preview_sales": "Сумма продаж",
        "preview_profit": "Прибыль",
        "preview_orders": "Заказы",
        "preview_rating": "Рейтинг",
    },
    "en": {
        "app_description": APP_DESCRIPTION,
        "app_caption": (
            "This app is fully built in Python with Streamlit. Uploaded CSV files and "
            "custom resources are separate data sources inside the interface."
        ),
        "language": "Language",
        "data_source": "Data source",
        "choose_source": "Choose source",
        "source_sample": "Built-in sample dataset",
        "source_upload": "Upload CSV",
        "source_resources": "Custom resources",
        "filters": "Filters",
        "date_range": "Date range",
        "region": "Region",
        "category": "Category",
        "product": "Product",
        "overview": "Overview",
        "visualizations": "Visualizations",
        "data_export": "Data and export",
        "analytical_summary": "Analytical summary",
        "current_source": "Current source: {source}",
        "best_region": "Best region",
        "top_product": "Top product",
        "sales_volatility": "Sales volatility",
        "total_sales": "Total sales amount",
        "total_profit": "Total profit",
        "margin": "Margin",
        "avg_order_value": "Avg order value",
        "filtered_data": "Filtered data",
        "rows_count": "Rows in current dataset: {count}",
        "download_csv": "Download filtered CSV",
        "download_json": "Download summary JSON",
        "save_results": "Save results into data/exports",
        "saved_ok": "Files saved successfully:\n- {dataset}\n- {summary}",
        "upload_file": "Upload CSV file",
        "upload_help": "The file is kept only for the current browser session.",
        "clear_file": "Clear uploaded file",
        "loaded_file": "Loaded file: {name}",
        "upload_info": (
            "Upload a CSV file in the sidebar. If the file structure is invalid, "
            "it will be cleared and you will need to upload it again."
        ),
        "custom_resources": "Custom resources",
        "custom_caption": (
            "Create separate named datasets and add rows manually or by pasted CSV text."
        ),
        "new_resource_name": "New resource name",
        "create_resource": "Create resource",
        "create_first_resource": "Create a resource first.",
        "active_resource": "Active resource",
        "rows_in_resource": "Rows in resource: {count}",
        "delete_resource": "Delete resource",
        "clear_rows": "Clear rows",
        "add_one_record": "Add one record",
        "date": "Date",
        "unit_price": "Sales (unit price for 1 item)",
        "unit_price_help": "For manual entry, this field means price for one item.",
        "profit_total": "Profit (total for the row)",
        "orders": "Orders / quantity",
        "customer_rating": "Customer rating",
        "add_record": "Add record",
        "paste_csv": "Paste CSV into resource",
        "apply_mode": "How to apply pasted data",
        "append_rows": "Append rows",
        "replace_resource": "Replace resource",
        "csv_text": "CSV text",
        "import_csv_text": "Import CSV text",
        "imported_rows": "Imported {count} rows into resource '{name}'.",
        "resource_empty": "Resource '{name}' is empty. Add one record or paste CSV text in the sidebar.",
        "create_resource_first": "Create a custom resource in the sidebar to start adding data.",
        "no_rows": "No rows match the selected filters. Adjust the filters and try again.",
        "source_uploaded": "Uploaded CSV",
        "source_resource": "Custom resource: {name}",
        "source_sample_label": "Built-in sample dataset",
        "insight_top": "Top sales driver: {product}. Best region: {region}.",
        "insight_rating": "Best customer rating is in {region}: {rating:.2f}.",
        "insight_margin": "Weakest average margin is in {category}: {margin:.2f}%.",
        "chart_monthly": "Monthly trend",
        "chart_region": "Sales by region",
        "chart_category": "Category and product performance",
        "chart_rating": "Customer rating distribution",
        "metric_legend": "Metric",
        "resource_name_required": "Enter a resource name before creating it.",
        "resource_exists": "A resource with this name already exists.",
        "unexpected_error": "Unexpected error: {error}",
        "preview_date": "Date",
        "preview_region": "Region",
        "preview_category": "Category",
        "preview_product": "Product",
        "preview_sales": "Sales amount",
        "preview_profit": "Profit",
        "preview_orders": "Orders",
        "preview_rating": "Rating",
    },
}


ERROR_TRANSLATIONS = {
    "ru": {
        "No file was uploaded.": "Файл не был загружен.",
        "The uploaded file is empty.": "Загруженный файл пуст.",
        "Could not parse the CSV file. Check separators and headers.": (
            "Не удалось разобрать CSV-файл. Проверьте разделители и заголовки."
        ),
        "The file encoding is not supported. Use UTF-8 or CP1251 CSV.": (
            "Кодировка файла не поддерживается. Используйте CSV в UTF-8 или CP1251."
        ),
        "The dataset is empty. Upload a CSV file with data.": (
            "Набор данных пуст. Загрузите CSV-файл с данными."
        ),
        "All rows were removed during cleaning. Check date and numeric values in the file.": (
            "Все строки были удалены при очистке. Проверьте даты и числовые значения в файле."
        ),
        "CSV text is empty. Paste data with headers and rows.": (
            "CSV-текст пуст. Вставьте данные с заголовками и строками."
        ),
        "The pasted CSV text is empty.": "Вставленный CSV-текст пуст.",
        "Could not parse the pasted CSV text.": "Не удалось разобрать вставленный CSV-текст.",
        "Enter a resource name before creating it.": "Введите название ресурса перед созданием.",
        "A resource with this name already exists.": "Ресурс с таким названием уже существует.",
    }
}


@dataclass(slots=True)
class UploadedBuffer:
    name: str
    payload: bytes

    def getvalue(self) -> bytes:
        return self.payload


@st.cache_data(show_spinner=False)
def get_sample_dataset():
    return load_sample_dataset()


def t(language: str, key: str, **kwargs) -> str:
    return TEXT[language][key].format(**kwargs)


def translate_error_message(language: str, message: str) -> str:
    if language == "en":
        return message

    if message.startswith("Missing required columns: "):
        missing = message.split("Missing required columns: ", 1)[1].split(". Expected columns:", 1)[0]
        return (
            f"Отсутствуют обязательные столбцы: {missing}. "
            "Ожидаемые столбцы: date, region, category, product, sales, profit, orders, customer_rating. "
            "Приложение также пытается автоматически распознавать популярные русские и английские названия колонок."
        )

    return ERROR_TRANSLATIONS.get(language, {}).get(message, message)


def get_display_columns(language: str) -> dict[str, str]:
    return {
        "date": t(language, "preview_date"),
        "region": t(language, "preview_region"),
        "category": t(language, "preview_category"),
        "product": t(language, "preview_product"),
        "sales": t(language, "preview_sales"),
        "profit": t(language, "preview_profit"),
        "orders": t(language, "preview_orders"),
        "customer_rating": t(language, "preview_rating"),
    }


def _init_upload_state() -> None:
    defaults = {
        "uploader_version": 0,
        "uploaded_dataset_bytes": None,
        "uploaded_dataset_name": None,
        "uploaded_dataset_token": None,
        "uploaded_dataset_error": None,
        "custom_resources": {},
        "active_resource_name": None,
        "language_code": "ru",
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


def _sync_uploaded_dataset(language: str) -> None:
    uploader_key = f"upload_csv_{st.session_state.uploader_version}"
    uploaded_file = st.sidebar.file_uploader(
        t(language, "upload_file"),
        type=["csv"],
        key=uploader_key,
        help=t(language, "upload_help"),
    )

    if st.session_state.uploaded_dataset_error:
        st.sidebar.error(translate_error_message(language, st.session_state.uploaded_dataset_error))

    if st.sidebar.button(t(language, "clear_file"), use_container_width=True):
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


def _render_resource_manager(language: str) -> None:
    st.sidebar.divider()
    st.sidebar.subheader(t(language, "custom_resources"))
    st.sidebar.caption(t(language, "custom_caption"))

    try:
        with st.sidebar.form("create_resource_form", clear_on_submit=True):
            resource_name = st.text_input(t(language, "new_resource_name"))
            create_resource = st.form_submit_button(t(language, "create_resource"), use_container_width=True)

            if create_resource:
                _create_resource(resource_name)
                st.rerun()

        resource_names = sorted(st.session_state.custom_resources.keys())
        if not resource_names:
            st.sidebar.info(t(language, "create_first_resource"))
            return

        active_name = st.session_state.active_resource_name
        if active_name not in resource_names:
            active_name = resource_names[0]
            _set_active_resource(active_name)

        selected_name = st.sidebar.selectbox(
            t(language, "active_resource"),
            options=resource_names,
            index=resource_names.index(active_name),
        )
        _set_active_resource(selected_name)

        resource_rows = st.session_state.custom_resources[selected_name]
        st.sidebar.caption(t(language, "rows_in_resource", count=len(resource_rows)))

        action_col1, action_col2 = st.sidebar.columns(2)
        if action_col1.button(t(language, "delete_resource"), use_container_width=True):
            _delete_active_resource()
            st.rerun()
        if action_col2.button(t(language, "clear_rows"), use_container_width=True):
            st.session_state.custom_resources[selected_name] = []
            st.rerun()

        with st.sidebar.expander(t(language, "add_one_record"), expanded=False):
            st.caption(t(language, "unit_price_help"))
            with st.form("add_manual_record_form", clear_on_submit=True):
                date_value = st.date_input(t(language, "date"))
                region = st.text_input(t(language, "region"), value="North")
                category = st.text_input(t(language, "category"), value="Electronics")
                product = st.text_input(t(language, "product"), value="Laptop")
                unit_price = st.number_input(t(language, "unit_price"), min_value=0.0, value=100.0, step=10.0)
                profit = st.number_input(t(language, "profit_total"), min_value=0.0, value=250.0, step=50.0)
                orders = st.number_input(t(language, "orders"), min_value=0, value=10, step=1)
                customer_rating = st.number_input(
                    t(language, "customer_rating"),
                    min_value=0.0,
                    max_value=5.0,
                    value=4.5,
                    step=0.1,
                )
                add_record = st.form_submit_button(t(language, "add_record"), use_container_width=True)

                if add_record:
                    _append_manual_record(
                        selected_name,
                        {
                            "date": date_value.isoformat(),
                            "region": region,
                            "category": category,
                            "product": product,
                            "sales": float(unit_price) * int(orders),
                            "profit": profit,
                            "orders": orders,
                            "customer_rating": customer_rating,
                        },
                    )
                    st.rerun()

        with st.sidebar.expander(t(language, "paste_csv"), expanded=False):
            with st.form("paste_csv_resource_form", clear_on_submit=False):
                paste_mode = st.radio(
                    t(language, "apply_mode"),
                    options=["append", "replace"],
                    format_func=lambda value: t(language, "append_rows") if value == "append" else t(language, "replace_resource"),
                    horizontal=False,
                )
                csv_text = st.text_area(
                    t(language, "csv_text"),
                    height=180,
                    placeholder=(
                        "date,region,category,product,sales,profit,orders,customer_rating\n"
                        "2025-01-01,North,Electronics,Laptop,1200,300,10,4.7"
                    ),
                )
                import_csv_text = st.form_submit_button(
                    t(language, "import_csv_text"),
                    use_container_width=True,
                )

                if import_csv_text:
                    imported_rows = _merge_csv_text_into_resource(selected_name, csv_text, paste_mode)
                    st.sidebar.success(t(language, "imported_rows", count=imported_rows, name=selected_name))
                    st.rerun()
    except DataValidationError as error:
        st.sidebar.error(translate_error_message(language, str(error)))


def render_filters(frame: pd.DataFrame, language: str) -> AnalysisFilters:
    min_date = frame["date"].min().date()
    max_date = frame["date"].max().date()

    st.sidebar.header(t(language, "filters"))
    date_range = st.sidebar.date_input(
        t(language, "date_range"),
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    regions = st.sidebar.multiselect(
        t(language, "region"),
        options=sorted(frame["region"].unique().tolist()),
    )
    categories = st.sidebar.multiselect(
        t(language, "category"),
        options=sorted(frame["category"].unique().tolist()),
    )
    products = st.sidebar.multiselect(
        t(language, "product"),
        options=sorted(frame["product"].unique().tolist()),
    )

    return AnalysisFilters(
        start_date=start_date,
        end_date=end_date,
        regions=regions,
        categories=categories,
        products=products,
    )


def render_metrics(summary: dict[str, float], language: str) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t(language, "total_sales"), f"${summary['total_sales']:,.0f}")
    col2.metric(t(language, "total_profit"), f"${summary['total_profit']:,.0f}")
    col3.metric(t(language, "margin"), f"{summary['profit_margin_pct']:.2f}%")
    col4.metric(t(language, "avg_order_value"), f"${summary['average_order_value']:,.0f}")


def render_charts(filtered_frame: pd.DataFrame, language: str) -> None:
    monthly_trend = build_monthly_trend(filtered_frame)
    region_breakdown = build_region_breakdown(filtered_frame)
    category_performance = build_category_performance(filtered_frame)

    trend_chart = px.line(
        monthly_trend,
        x="month",
        y=["sales", "profit"],
        markers=True,
        title=t(language, "chart_monthly"),
    )
    trend_chart.update_layout(legend_title_text=t(language, "metric_legend"))

    region_chart = px.bar(
        region_breakdown,
        x="region",
        y="sales",
        color="profit_margin_pct",
        title=t(language, "chart_region"),
        text_auto=".2s",
    )

    bubble_chart = px.scatter(
        category_performance,
        x="sales",
        y="profit",
        size="orders",
        color="category",
        hover_name="product",
        title=t(language, "chart_category"),
    )

    left, right = st.columns(2)
    left.plotly_chart(trend_chart, use_container_width=True)
    right.plotly_chart(region_chart, use_container_width=True)
    st.plotly_chart(bubble_chart, use_container_width=True)

    fig, axis = plt.subplots(figsize=(8, 4))
    axis.hist(filtered_frame["customer_rating"], bins=8, color="#1f77b4", edgecolor="white")
    axis.set_title(t(language, "chart_rating"))
    axis.set_xlabel(t(language, "customer_rating"))
    axis.set_ylabel("Count" if language == "en" else "Количество")
    st.pyplot(fig)
    plt.close(fig)


def get_localized_insights(filtered_frame: pd.DataFrame, summary: dict[str, float], language: str) -> list[str]:
    if language == "en":
        return build_analytical_insights(filtered_frame)

    rating_by_region = filtered_frame.groupby("region", as_index=False)["customer_rating"].mean()
    strongest_region = rating_by_region.sort_values("customer_rating", ascending=False).iloc[0]
    weakest_margin = (
        filtered_frame.groupby("category", as_index=False)["profit_margin"].mean()
        .sort_values("profit_margin", ascending=True)
        .iloc[0]
    )

    return [
        t(language, "insight_top", product=summary["top_product"], region=summary["best_region"]),
        t(language, "insight_rating", region=strongest_region["region"], rating=strongest_region["customer_rating"]),
        t(language, "insight_margin", category=weakest_margin["category"], margin=weakest_margin["profit_margin"] * 100),
    ]


def _render_dataset_view(dataset: pd.DataFrame, source_label: str, language: str) -> None:
    filters = render_filters(dataset, language)
    filtered_frame = apply_filters(dataset, filters)
    summary = build_summary(filtered_frame)

    if filtered_frame.empty:
        st.warning(t(language, "no_rows"))
        return

    tab_overview, tab_visuals, tab_export = st.tabs(
        [t(language, "overview"), t(language, "visualizations"), t(language, "data_export")]
    )

    with tab_overview:
        render_metrics(summary, language)
        st.subheader(t(language, "analytical_summary"))
        st.caption(t(language, "current_source", source=source_label))
        st.write(
            f"{t(language, 'best_region')}: {summary['best_region']} | "
            f"{t(language, 'top_product')}: {summary['top_product']} | "
            f"{t(language, 'sales_volatility')}: ${summary['sales_volatility']:,.0f}"
        )
        for insight in get_localized_insights(filtered_frame, summary, language):
            st.write(f"- {insight}")

    with tab_visuals:
        render_charts(filtered_frame, language)

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
        display_frame = filtered_frame[preview_columns].copy()
        display_frame = display_frame.rename(columns=get_display_columns(language))

        st.subheader(t(language, "filtered_data"))
        st.caption(t(language, "rows_count", count=len(filtered_frame)))
        st.dataframe(display_frame, use_container_width=True)

        csv_bytes = dataframe_to_csv_bytes(filtered_frame)
        json_bytes = summary_to_json_bytes(summary)

        download_col1, download_col2 = st.columns(2)
        download_col1.download_button(
            t(language, "download_csv"),
            data=csv_bytes,
            file_name="filtered_dataset.csv",
            mime="text/csv",
        )
        download_col2.download_button(
            t(language, "download_json"),
            data=json_bytes,
            file_name="analytics_summary.json",
            mime="application/json",
        )

        if st.button(t(language, "save_results")):
            dataset_path, summary_path = save_results(filtered_frame, summary)
            st.success(t(language, "saved_ok", dataset=dataset_path, summary=summary_path))


def render_dashboard() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    _init_upload_state()

    language_label = st.sidebar.selectbox(
        "Language / Язык",
        options=list(LANGUAGE_OPTIONS.keys()),
        index=0 if st.session_state.language_code == "ru" else 1,
    )
    language = LANGUAGE_OPTIONS[language_label]
    st.session_state.language_code = language

    st.title(APP_TITLE)
    st.write(t(language, "app_description"))
    st.caption(t(language, "app_caption"))

    st.sidebar.header(t(language, "data_source"))
    source = st.sidebar.radio(
        t(language, "choose_source"),
        options=["sample", "upload", "resources"],
        format_func=lambda value: {
            "sample": t(language, "source_sample"),
            "upload": t(language, "source_upload"),
            "resources": t(language, "source_resources"),
        }[value],
    )

    try:
        if source == "upload":
            _sync_uploaded_dataset(language)
            dataset = _get_active_uploaded_dataset()

            if dataset is None:
                st.info(t(language, "upload_info"))
                return

            st.sidebar.success(t(language, "loaded_file", name=st.session_state.uploaded_dataset_name))
            _render_dataset_view(dataset, t(language, "source_uploaded"), language)
            return

        if source == "resources":
            _render_resource_manager(language)
            dataset = _get_active_resource_dataset()
            active_name = st.session_state.active_resource_name

            if not active_name:
                st.info(t(language, "create_resource_first"))
                return

            if dataset is None:
                st.info(t(language, "resource_empty", name=active_name))
                return

            _render_dataset_view(dataset, t(language, "source_resource", name=active_name), language)
            return

        dataset = get_sample_dataset()
        _render_dataset_view(dataset, t(language, "source_sample_label"), language)

    except DataValidationError as error:
        st.error(translate_error_message(language, str(error)))
    except Exception as error:
        st.error(t(language, "unexpected_error", error=error))
