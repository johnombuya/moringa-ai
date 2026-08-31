"""AfyaPlus observability console — reads Phase 1–3 artifacts only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST

from config import (
    DAILY_CAP_USD,
    DAILY_COSTS_CSV,
    DRIFT_ALERTS_JSON,
    DRIFT_TREND_CSV,
    EVAL_RESULTS_CSV,
    MONTHLY_CAP_USD,
    QUALITY_GATE_CSV,
    SAVINGS_CSV,
    SIMULATION_DAYS,
)

app = FastAPI(title="AfyaPlus Observability Console")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

EXCEPTION_COUNT = 0


def _records(path: Path) -> list[dict]:
    """Load a CSV as native Python types so Jinja and Prometheus never see NumPy scalars."""
    return json.loads(pd.read_csv(path).to_json(orient="records"))


def _load() -> dict:
    global EXCEPTION_COUNT
    payload = {
        "health": "UP",
        "exceptions": EXCEPTION_COUNT,
        "quality": [],
        "drift": [],
        "alerts": [],
        "daily_spend": 0.0,
        "monthly_spend": 0.0,
        "daily_cap": DAILY_CAP_USD,
        "monthly_cap": MONTHLY_CAP_USD,
        "routing": [],
    }
    try:
        if QUALITY_GATE_CSV.exists():
            payload["quality"] = _records(QUALITY_GATE_CSV)
        if DRIFT_TREND_CSV.exists():
            payload["drift"] = _records(DRIFT_TREND_CSV)
        if DRIFT_ALERTS_JSON.exists():
            payload["alerts"] = json.loads(DRIFT_ALERTS_JSON.read_text(encoding="utf-8")).get(
                "first_drift", []
            )
        if DAILY_COSTS_CSV.exists():
            daily = pd.read_csv(DAILY_COSTS_CSV)
            payload["monthly_spend"] = round(float(daily["usd"].sum()), 2)
            payload["daily_spend"] = round(payload["monthly_spend"] / SIMULATION_DAYS, 2)
        if SAVINGS_CSV.exists():
            payload["routing"] = _records(SAVINGS_CSV)
        if not EVAL_RESULTS_CSV.exists():
            payload["health"] = "DOWN"
            payload["exceptions"] += 1
    except Exception:
        EXCEPTION_COUNT += 1
        payload["health"] = "DOWN"
        payload["exceptions"] = EXCEPTION_COUNT
    return payload


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    data = _load()
    daily_pct = float(min(100.0, 100.0 * data["daily_spend"] / DAILY_CAP_USD) if DAILY_CAP_USD else 0.0)
    monthly_pct = float(
        min(100.0, 100.0 * data["monthly_spend"] / MONTHLY_CAP_USD) if MONTHLY_CAP_USD else 0.0
    )
    current_drift = data["drift"][-1] if data["drift"] else {}
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "data": data,
            "daily_pct": daily_pct,
            "monthly_pct": monthly_pct,
            "current_drift": current_drift,
        },
    )


@app.get("/metrics")
def metrics() -> Response:
    data = _load()
    registry = CollectorRegistry()
    Gauge("afyaplus_health_up", "1 if console can read artifacts", registry=registry).set(
        1 if data["health"] == "UP" else 0
    )
    Gauge("afyaplus_exceptions_total", "Artifact load exceptions", registry=registry).set(
        data["exceptions"]
    )
    Gauge("afyaplus_daily_spend_usd", "Mean daily generative spend", registry=registry).set(
        data["daily_spend"]
    )
    Gauge("afyaplus_monthly_spend_usd", "30-day generative spend", registry=registry).set(
        data["monthly_spend"]
    )
    Gauge("afyaplus_daily_cap_usd", "Daily spend cap", registry=registry).set(DAILY_CAP_USD)
    Gauge("afyaplus_monthly_cap_usd", "Monthly spend cap", registry=registry).set(MONTHLY_CAP_USD)
    if data["quality"]:
        g_overall = Gauge(
            "afyaplus_judge_overall",
            "Mean LLM-judge overall by model and feature",
            ["model", "feature"],
            registry=registry,
        )
        for row in data["quality"]:
            g_overall.labels(model=str(row["model"]), feature=str(row["feature"])).set(
                float(row["judge_overall"])
            )
    if current := (data["drift"][-1] if data["drift"] else None):
        Gauge("afyaplus_month3_rouge_l", "Month 3 mean ROUGE-L", registry=registry).set(
            float(current.get("rouge_l_mean", 0))
        )
        Gauge("afyaplus_drift_flag", "1 if column drifted in latest month", ["column"], registry=registry).labels(
            column="rouge_l"
        ).set(1 if current.get("rouge_l_drift") else 0)
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)
