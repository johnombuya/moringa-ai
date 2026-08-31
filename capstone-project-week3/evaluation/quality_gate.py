"""Pass/fail mapping against shared clinical safety thresholds."""

from __future__ import annotations

import pandas as pd

from config import JUDGE_GROUNDEDNESS_MIN, JUDGE_OVERALL_MIN, QUALITY_GATE_CSV, ROUGE_L_MIN


def assess_quality_gates(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = df.groupby(["model", "feature"], as_index=False).agg(
        rouge_l=("rouge_l", "mean"),
        groundedness=("groundedness", "mean"),
        judge_overall=("judge_overall", "mean"),
        bleu_4=("bleu_4", "mean"),
        token_f1=("token_f1", "mean"),
        relevance=("relevance", "mean"),
        helpfulness=("helpfulness", "mean"),
        correctness=("correctness", "mean"),
    )
    for record in grouped.to_dict(orient="records"):
        passes = (
            record["judge_overall"] >= JUDGE_OVERALL_MIN
            and record["groundedness"] >= JUDGE_GROUNDEDNESS_MIN
            and record["rouge_l"] >= ROUGE_L_MIN
        )
        rows.append(
            {
                **record,
                "gate": "PASS" if passes else "FAIL",
                "overall_min": JUDGE_OVERALL_MIN,
                "groundedness_min": JUDGE_GROUNDEDNESS_MIN,
                "rouge_l_min": ROUGE_L_MIN,
            }
        )
    gate_df = pd.DataFrame(rows)
    QUALITY_GATE_CSV.parent.mkdir(parents=True, exist_ok=True)
    gate_df.to_csv(QUALITY_GATE_CSV, index=False)
    return gate_df
