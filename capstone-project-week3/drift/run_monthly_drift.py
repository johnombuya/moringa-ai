"""Run Evidently drift reports for months 1–3 against the Month 0 reference."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from config import DRIFT_ALERTS_JSON, DRIFT_DIR, DRIFT_TREND_CSV

COLUMNS = ("input_length", "rouge_l", "latency_ms")


def _run_evidently(reference_df: pd.DataFrame, current_df: pd.DataFrame, html_path: Path) -> dict:
    Report = None
    try:
        from evidently.legacy.report import Report
        from evidently.legacy.metrics import ColumnDriftMetric, DatasetDriftMetric
        from evidently.legacy.metric_preset import DataDriftPreset
    except ImportError:
        try:
            from evidently.report import Report
            from evidently.metrics import ColumnDriftMetric, DatasetDriftMetric
            from evidently.metric_preset import DataDriftPreset
        except ImportError:
            Report = None

    if Report is None:
        print("Evidently Report API unavailable; writing a descriptive HTML snapshot.")
        html_path.write_text(
            f"<html><body><h1>AfyaPlus drift snapshot</h1>"
            f"<pre>{current_df.describe().to_string()}</pre></body></html>",
            encoding="utf-8",
        )
        return {}

    report = Report(
        metrics=[
            DatasetDriftMetric(),
            DataDriftPreset(),
            ColumnDriftMetric(column_name="input_length"),
            ColumnDriftMetric(column_name="rouge_l"),
            ColumnDriftMetric(column_name="latency_ms"),
            ColumnDriftMetric(column_name="token_count"),
        ]
    )
    report.run(reference_data=reference_df, current_data=current_df)
    report.save_html(str(html_path))
    return report.as_dict()


def _column_drift_flags(payload: dict) -> dict[str, bool]:
    flags = {col: False for col in COLUMNS}
    for metric in payload.get("metrics", []):
        result = metric.get("result", {})
        col = result.get("column_name")
        if col in flags and "drift_detected" in result:
            flags[col] = bool(result["drift_detected"])
    return flags


def _heuristic_flags(reference_df: pd.DataFrame, current_df: pd.DataFrame) -> dict[str, bool]:
    """If Evidently dict shape changes, flag mean shifts > 15% as drifted."""
    flags = {}
    for col in COLUMNS:
        ref = reference_df[col].mean()
        cur = current_df[col].mean()
        if ref == 0:
            flags[col] = False
            continue
        flags[col] = abs(cur - ref) / abs(ref) >= 0.15
    return flags


def main() -> None:
    reference = pd.read_csv(DRIFT_DIR / "reference_data.csv")
    trend_rows = []
    alerts = []
    first_seen: dict[str, int] = {}

    for month in (1, 2, 3):
        current = pd.read_csv(DRIFT_DIR / f"month_{month}.csv")
        html_path = DRIFT_DIR / f"month_{month}_report.html"
        payload = _run_evidently(reference, current, html_path)
        flags = _column_drift_flags(payload)
        if not payload or not any(col in str(payload) for col in COLUMNS):
            flags = _heuristic_flags(reference, current)

        trend_rows.append(
            {
                "month": month,
                "rouge_l_mean": round(current["rouge_l"].mean(), 4),
                "latency_ms_mean": round(current["latency_ms"].mean(), 1),
                "input_length_mean": round(current["input_length"].mean(), 2),
                "rouge_l_drift": flags.get("rouge_l", False),
                "latency_ms_drift": flags.get("latency_ms", False),
                "input_length_drift": flags.get("input_length", False),
            }
        )
        for col, drifted in flags.items():
            if drifted and col not in first_seen:
                first_seen[col] = month
                alerts.append({"month": month, "column": col, "drift_detected": True})
        print(f"Month {month}: wrote {html_path}")

    trend = pd.DataFrame(trend_rows)
    trend.to_csv(DRIFT_TREND_CSV, index=False)
    DRIFT_ALERTS_JSON.write_text(json.dumps({"first_drift": alerts}, indent=2), encoding="utf-8")
    print(f"Wrote {DRIFT_TREND_CSV}")
    print(f"Wrote {DRIFT_ALERTS_JSON}")


if __name__ == "__main__":
    main()
