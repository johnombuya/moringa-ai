"""Build executive_summary.md and .pdf from Phase 1–4 artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
from fpdf import FPDF

from config import (
    DAILY_CAP_USD,
    DAILY_COSTS_CSV,
    DRIFT_ALERTS_JSON,
    DRIFT_TREND_CSV,
    EVAL_RESULTS_CSV,
    HUMAN_REVIEW_USD_PER_TICKET,
    MONTHLY_CAP_USD,
    PROJECT_ROOT,
    QUALITY_GATE_CSV,
    SAVINGS_CSV,
    SIMULATION_DAYS,
)


def _md(eval_df, gates, trend, alerts, daily, savings) -> str:
    run_mode = eval_df["run_mode"].iloc[0] if "run_mode" in eval_df.columns else "unknown"
    n_rows = len(eval_df)
    mini = gates[gates["model"] == "gpt-4o-mini"]
    four = gates[gates["model"] == "gpt-4o"]
    mini_pass = (mini["gate"] == "PASS").sum()
    four_pass = (four["gate"] == "PASS").sum()
    mini_g = float(mini["groundedness"].mean()) if len(mini) else 0
    four_g = float(four["groundedness"].mean()) if len(four) else 0
    mini_o = float(mini["judge_overall"].mean()) if len(mini) else 0
    four_o = float(four["judge_overall"].mean()) if len(four) else 0
    m3 = trend[trend["month"] == 3].iloc[0]
    m1 = trend[trend["month"] == 1].iloc[0]
    first = alerts[0] if alerts else {"month": "n/a", "column": "n/a"}
    month_spend = float(daily["usd"].sum())
    daily_spend = month_spend / SIMULATION_DAYS
    save_4o = float(savings["savings_vs_all_gpt4o_usd"].sum())
    save_canary = float(savings["savings_vs_canary_usd"].sum())
    tickets = int(daily["requests"].sum())
    human = tickets * HUMAN_REVIEW_USD_PER_TICKET
    routed = "; ".join(f"{r.feature} → {r.routed_model}" for r in savings.itertuples())

    return f"""# AfyaPlus Generative Layer — Engineering Decision Memorandum

**To:** CTO and Medical Director  
**From:** Platform Engineering (observability capstone)  
**Re:** Six weeks of production AI without automated evaluation, drift monitoring, or cost tracking  
**Evaluation run mode:** {run_mode}

## Executive summary

The AfyaPlus generative layer has been answering clinical and insurance queries without automated quality gates, drift reports, or token accounting. We evaluated both **gpt-4o-mini** and **gpt-4o** on a **{n_rows // 2}-question** clinical set ({n_rows} model rows), simulated three months of traffic, and projected 30-day spend at 2,000 requests/day. Mean judge overall is **{mini_o:.2f}/5** for mini and **{four_o:.2f}/5** for gpt-4o; Month 3 mean ROUGE-L is **{m3['rouge_l_mean']}** versus **{m1['rouge_l_mean']}** in Month 1; 30-day generative spend is **${month_spend:.2f}** against a **${MONTHLY_CAP_USD:.0f}** cap.

## Quality performance breakdown

Automated overlap (BLEU / ROUGE-L / token F1) plus an LLM judge (correctness, groundedness, relevance, helpfulness) were scored for every row. gpt-4o-mini passed **{mini_pass}** of {len(mini)} feature gates; gpt-4o passed **{four_pass}** of {len(four)}. Mean groundedness is **{mini_g:.2f}** (mini) vs **{four_g:.2f}** (gpt-4o). Clinically this means mini is cheaper on overlap-heavy protocol restatements but is more likely to drop numbers, waiting periods, or red-flag lists — the details clinicians need for safe routing.

## Cost and efficiency analysis

At the documented 75/25 canary, 30-day token spend is **${month_spend:.2f}** (**${daily_spend:.2f}/day** vs a **${DAILY_CAP_USD:.0f}** daily cap). Routing each feature to the cheapest model that still **PASSES** the quality gate saves **${save_4o:.2f}** versus sending all traffic to gpt-4o and **${save_canary:.2f}** versus the current canary. Human review of the same {tickets:,} tickets at an assumed **${HUMAN_REVIEW_USD_PER_TICKET:.2f}/ticket** would cost **${human:,.0f}** — token inference remains far cheaper than full human validation, but it does not replace a clinician on failed gates.

Recommended routing from this run: {routed}.

## Systemic operational risks

First detected drift: **Month {first['month']}**, column **{first['column']}**. Month 3 latency mean is **{m3['latency_ms_mean']} ms** with ROUGE-L **{m3['rouge_l_mean']}**. That pattern matches longer, more complex production questions than the pre-deploy baseline. Hallucination risk is highest where groundedness fails the 4.0 gate: unsupported dosages or cover terms must not ship. Waiting-period emergencies remain a policy exception (bypass cover checks) and must stay out of cost-only routing.

## Actionable engineering roadmap

1. **Route by feature, not by default canary.** Keep any FAIL feature on gpt-4o. Estimated 30-day saving vs all-gpt-4o: **${save_4o:.2f}**, with groundedness held at the 4.0 safety bar.
2. **Page on first-column drift.** Alert already isolates Month {first['month']} / {first['column']}. Wire the Prometheus `/metrics` gauges to the existing 80%/95% budget WARN/CRIT policy so spend and quality share one on-call path.
3. **Do not drop human review on pediatric_triage FAIL rows.** Token cost of the full 30-day corpus is **${month_spend:.2f}** versus **${human:,.0f}** for blanket human review; spend the human budget only on gate failures and Month 3 drifted slices.

*Coursework snapshot — not a live AfyaPlus production certification.*
"""


def write_pdf(text: str, path: Path) -> None:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    pdf.set_left_margin(16)
    pdf.set_right_margin(16)
    usable = pdf.w - 32
    for line in text.splitlines():
        pdf.set_x(16)
        safe = line.encode("latin-1", "replace").decode("latin-1").strip()
        if not safe or safe.startswith("```"):
            pdf.ln(2)
            continue
        if safe.startswith("# "):
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(usable, 7, safe[2:])
        elif safe.startswith("## "):
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(usable, 6, safe[3:])
        else:
            pdf.set_font("Helvetica", size=10)
            pdf.multi_cell(usable, 5, safe.replace("**", ""))
    pdf.output(str(path))


def main() -> None:
    eval_df = pd.read_csv(EVAL_RESULTS_CSV)
    gates = pd.read_csv(QUALITY_GATE_CSV)
    trend = pd.read_csv(DRIFT_TREND_CSV)
    alerts = json.loads(DRIFT_ALERTS_JSON.read_text(encoding="utf-8")).get("first_drift", [])
    daily = pd.read_csv(DAILY_COSTS_CSV)
    savings = pd.read_csv(SAVINGS_CSV)
    md = _md(eval_df, gates, trend, alerts, daily, savings)
    md_path = PROJECT_ROOT / "executive_summary.md"
    pdf_path = PROJECT_ROOT / "executive_summary.pdf"
    md_path.write_text(md, encoding="utf-8")
    write_pdf(md, pdf_path)
    print(f"Wrote {md_path}")
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    main()
