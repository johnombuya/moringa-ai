# AfyaPlus Observability Capstone (Week 3)

Operational evaluation, drift monitoring, and cost tracking for the AfyaPlus generative layer built in Weeks 1–2. This is **coursework observability**, not a live clinic deployment.

## Thresholds

| Gate | Value |
|---|---|
| Judge overall | ≥ 4.0 / 5 |
| Groundedness | ≥ 4.0 / 5 |
| ROUGE-L | ≥ 0.35 |
| Daily cap | $50 |
| Monthly cap | $1,500 |
| Canary split | 75% gpt-4o-mini / 25% gpt-4o |
| Simulated volume | 2,000 requests/day × 30 days |

Token prices (USD / 1M tokens) are in `config.py`. Human-in-the-loop review is assumed at **$2.50 per ticket** for the executive memo only — labelled as an assumption.

## Setup

```powershell
cd capstone-project-week3
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Add `OPENAI_API_KEY` for live evaluation. Drift, cost, and the dashboard do not require an API key.

## Run commands

**Phase 1 — evaluation** (live, falls back to `--offline` on quota/auth errors):

```powershell
python evaluation/run_full_evaluation.py
python evaluation/run_full_evaluation.py --offline
```

**Phase 2 — drift:**

```powershell
python drift/simulate_monthly_traffic.py
python drift/run_monthly_drift.py
```

**Phase 3 — cost:**

```powershell
python cost/run_cost_analysis.py
```

**Phase 4 — dashboard:**

```powershell
cd dashboard
uvicorn app:app --reload --port 8000
```

Open http://127.0.0.1:8000 and http://127.0.0.1:8000/metrics

**Phase 5 — memo PDF:**

```powershell
python generate_executive_pdf.py
```

## Live vs offline

`evaluation/run_full_evaluation.py` tries gpt-4o-mini and gpt-4o first. If the API is unavailable it writes the same CSV schema from a seeded fallback and records `run_mode=offline` on every row. Never skip a model or judge column.

## Honesty

Not a production AfyaPlus install. Not NVIDIA-certified. Weeks 1–2 remain the generative system; this repo only observes it.
