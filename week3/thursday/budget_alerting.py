import json, os
from datetime import datetime, timedelta

WARN_THRESHOLD = 0.80  # Alert at 80%
CRIT_THRESHOLD = 0.95  # Alert at 95%
DAILY_CAP_USD  = 50.00

def load_records(log_file: str) -> list:
    if not os.path.exists(log_file): return []
    with open(log_file) as f:
        return [json.loads(l) for l in f if l.strip()]

def compute_spend(records: list, since: datetime) -> float:
    return sum(
        r["cost_usd"] for r in records
        if datetime.fromisoformat(r["timestamp"]) >= since
    )

def run_budget_check(log_file="inference_costs.jsonl"):
    records     = load_records(log_file)
    daily_spend = compute_spend(records, datetime.utcnow() - timedelta(days=1))
    util        = daily_spend / DAILY_CAP_USD
    print(f"Daily spend: ${daily_spend:.4f} / ${DAILY_CAP_USD:.2f} ({util*100:.1f}%)")
    if util >= CRIT_THRESHOLD:
        print("[CRITICAL] Stop all non-essential traffic immediately!")
    elif util >= WARN_THRESHOLD:
        print("[WARNING] Approaching daily budget limit - investigate promptly.")
    else:
        print("[OK] Budget nominal.")

if __name__ == "__main__":
    run_budget_check()