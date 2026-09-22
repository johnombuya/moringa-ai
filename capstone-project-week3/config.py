"""Shared thresholds, prices, and paths for the AfyaPlus observability capstone."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
EVALUATION_DIR = PROJECT_ROOT / "evaluation"
DRIFT_DIR = PROJECT_ROOT / "drift"
COST_DIR = PROJECT_ROOT / "cost"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"

load_dotenv(PROJECT_ROOT / ".env")

MODELS = ("gpt-4o-mini", "gpt-4o")
CHANNELS = ("USSD", "Mobile App", "Web Portal")
FEATURES = ("pediatric_triage", "chronic_care_referral", "insurance_routing")

JUDGE_OVERALL_MIN = 4.0
JUDGE_GROUNDEDNESS_MIN = 4.0
ROUGE_L_MIN = 0.35

DAILY_CAP_USD = 50.00
MONTHLY_CAP_USD = 1500.00
WARN_THRESHOLD = 0.80
CRIT_THRESHOLD = 0.95

MINI_TRAFFIC_SHARE = 0.75
GPT4O_TRAFFIC_SHARE = 0.25
DAILY_REQUESTS = 2000
SIMULATION_DAYS = 30
RANDOM_SEED = 42

# Published list prices (USD per 1M tokens). Documented in README.
INPUT_USD_PER_1M = {
    "gpt-4o-mini": 0.15,
    "gpt-4o": 2.50,
}
OUTPUT_USD_PER_1M = {
    "gpt-4o-mini": 0.60,
    "gpt-4o": 10.00,
}

HUMAN_REVIEW_USD_PER_TICKET = 2.50

EVAL_RESULTS_CSV = EVALUATION_DIR / "full_evaluation_results.csv"
QUALITY_GATE_CSV = EVALUATION_DIR / "quality_gate.csv"
DRIFT_TREND_CSV = DRIFT_DIR / "drift_trend.csv"
DRIFT_ALERTS_JSON = DRIFT_DIR / "drift_alerts.json"
DAILY_COSTS_CSV = COST_DIR / "daily_costs.csv"
SAVINGS_CSV = COST_DIR / "savings_analysis.csv"
PROMPT_COST_CSV = COST_DIR / "prompt_cost_comparison.csv"


def get_openai_api_key() -> str:
    return os.environ.get("OPENAI_API_KEY", "").strip()
