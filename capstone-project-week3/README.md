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

Add `OPENAI_API_KEY` for live evaluation. Drift, cost, and the dashboard do not require an API key. Evaluation may run **offline** (seeded fallback, same CSV schema) if the API is unavailable.

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

The console is a dark card layout (health, quality, drift, budget) and still **artifact-only** — it does not call OpenAI.

## Tests

```powershell
cd capstone-project-week3
python -m unittest discover -s tests -v
```

Covers `GET /` (four sections), `GET /metrics` (`afyaplus_*` gauges), and empty artifacts (still 200, health DOWN). No live server or API key required.

## Phase 5 — memo

The engineering decision memorandum is `executive_summary.pdf`.

## Honesty

Not a production AfyaPlus install. Not NVIDIA-certified. Weeks 1–2 remain the generative system; this repo only observes it.
