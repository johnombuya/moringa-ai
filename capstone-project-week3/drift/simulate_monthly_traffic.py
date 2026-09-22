"""Simulate Month 0 reference plus three months of production traffic."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from config import DRIFT_DIR, RANDOM_SEED

N_ROWS = 200

QUESTIONS = [
    "What documents do I need for a standard clinical lab screening?",
    "How long does it take to process outpatient laboratory results?",
    "Can I book an inpatient clinical appointment online?",
    "My infant has a sudden rash and high fever - what are my triage options?",
    "Has the new MoH policy changed our clinical referral rules?",
]


def _month(rng: np.random.Generator, rouge_mu: float, rouge_sd: float,
           latency_mu: float, latency_sd: float, length_low: int, length_high: int,
           token_low: int, token_high: int) -> pd.DataFrame:
    rows = []
    for _ in range(N_ROWS):
        q = QUESTIONS[int(rng.integers(0, len(QUESTIONS)))]
        rows.append(
            {
                "question": q,
                "input_length": int(rng.integers(length_low, length_high + 1)),
                "rouge_l": round(float(rng.normal(rouge_mu, rouge_sd)), 4),
                "latency_ms": round(float(rng.normal(latency_mu, latency_sd)), 0),
                "token_count": int(rng.integers(token_low, token_high + 1)),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    rng = np.random.default_rng(RANDOM_SEED)
    DRIFT_DIR.mkdir(parents=True, exist_ok=True)
    months = {
        "reference_data.csv": _month(rng, 0.42, 0.05, 800, 100, 8, 14, 150, 300),
        "month_1.csv": _month(rng, 0.41, 0.05, 820, 110, 8, 15, 160, 310),
        "month_2.csv": _month(rng, 0.37, 0.07, 980, 160, 10, 18, 180, 380),
        "month_3.csv": _month(rng, 0.33, 0.08, 1100, 200, 12, 22, 200, 450),
    }
    for name, frame in months.items():
        path = DRIFT_DIR / name
        frame.to_csv(path, index=False)
        print(f"Wrote {path} ({len(frame)} rows)")


if __name__ == "__main__":
    main()
