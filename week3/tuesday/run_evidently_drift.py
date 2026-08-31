import pandas as pd
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
from evidently.metrics import ColumnDriftMetric, DatasetDriftMetric

reference_df = pd.read_csv("reference_data.csv")
production_df = pd.read_csv("production_data.csv")

# Dataset-level overview: high-level drift assertion
overview_report = Report(metrics=[DatasetDriftMetric(), DataDriftPreset()])
overview_report.run(reference_data=reference_df, current_data=production_df)
overview_report.save_html("drift_report_overview.html")
print("Saved: drift_report_overview.html")

# Targeted column-level: pinpoints specific degrading metrics
targeted = Report(metrics=[
    ColumnDriftMetric(column_name="input_length"),
    ColumnDriftMetric(column_name="rouge_l"),
    ColumnDriftMetric(column_name="latency_ms"),
    ColumnDriftMetric(column_name="token_count"),
])
targeted.run(reference_data=reference_df, current_data=production_df)
targeted.save_html("drift_report_targeted.html")

# Machine-readable results for alerting
results = targeted.as_dict()
for m in results["metrics"]:
    r = m.get("result", {})
    if "drift_detected" in r:
        col     = r.get("column_name", "unknown")
        drifted = r["drift_detected"]
        pval    = r.get("p_value", "N/A")
        status  = "DRIFT DETECTED" if drifted else "No drift"
        print(f"  {col:<20}: {status}  (p={pval})")