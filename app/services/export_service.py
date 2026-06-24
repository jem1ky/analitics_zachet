from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.config.settings import EXPORT_DIR


def _make_json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _make_json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_make_json_safe(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def save_results(frame: pd.DataFrame, summary: dict[str, Any]) -> tuple[Path, Path]:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    dataset_path = EXPORT_DIR / f"filtered_dataset_{timestamp}.csv"
    summary_path = EXPORT_DIR / f"analytics_summary_{timestamp}.json"

    export_frame = frame.copy()
    if "date" in export_frame.columns:
        export_frame["date"] = export_frame["date"].dt.strftime("%Y-%m-%d")
    export_frame.to_csv(dataset_path, index=False)

    safe_summary = _make_json_safe(summary)
    summary_path.write_text(
        json.dumps(safe_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return dataset_path, summary_path


def dataframe_to_csv_bytes(frame: pd.DataFrame) -> bytes:
    export_frame = frame.copy()
    if "date" in export_frame.columns:
        export_frame["date"] = export_frame["date"].dt.strftime("%Y-%m-%d")
    return export_frame.to_csv(index=False).encode("utf-8")


def summary_to_json_bytes(summary: dict[str, Any]) -> bytes:
    safe_summary = _make_json_safe(summary)
    return json.dumps(safe_summary, ensure_ascii=False, indent=2).encode("utf-8")

