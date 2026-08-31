"""Run BLEU/ROUGE/F1 + LLM judge for gpt-4o-mini and gpt-4o across 15 questions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
from tabulate import tabulate

from config import EVAL_RESULTS_CSV, MODELS
from evaluation.evaluation_data import EVAL_DATASET
from evaluation.evaluator import evaluate_response
from evaluation.llm_judge import llm_judge, offline_judge
from evaluation.model_querier import offline_hypothesis, query_model
from evaluation.quality_gate import assess_quality_gates


def _probe_api() -> bool:
    try:
        query_model("gpt-4o-mini", "Reply with the single word ok.")
        return True
    except Exception as exc:
        print(f"Live API unavailable ({type(exc).__name__}: {exc}). Using offline fallback.")
        return False


def run_full_evaluation(*, force_offline: bool = False) -> pd.DataFrame:
    live = False if force_offline else _probe_api()
    mode = "live" if live else "offline"
    results = []
    for example in EVAL_DATASET:
        for model in MODELS:
            if live:
                try:
                    hypothesis = query_model(model, example["question"])
                    judge_scores = llm_judge(
                        example["question"], example["reference"], hypothesis
                    )
                except Exception as exc:
                    print(f"Live call failed for {example['id']}/{model}: {exc}. Falling back.")
                    live = False
                    mode = "offline"
                    hypothesis = offline_hypothesis(
                        example["question"], example["reference"], model
                    )
                    judge_scores = offline_judge(
                        example["question"], example["reference"], hypothesis, model
                    )
            else:
                hypothesis = offline_hypothesis(
                    example["question"], example["reference"], model
                )
                judge_scores = offline_judge(
                    example["question"], example["reference"], hypothesis, model
                )

            auto_scores = evaluate_response(example["reference"], hypothesis)
            results.append(
                {
                    "id": example["id"],
                    "channel": example["channel"],
                    "feature": example["feature"],
                    "model": model,
                    "run_mode": mode,
                    "question": example["question"],
                    "reference": example["reference"],
                    "hypothesis": hypothesis,
                    **auto_scores,
                    "correctness": judge_scores.get("correctness", 0),
                    "groundedness": judge_scores.get("groundedness", 0),
                    "relevance": judge_scores.get("relevance", 0),
                    "helpfulness": judge_scores.get("helpfulness", 0),
                    "judge_overall": judge_scores.get("overall", 0),
                    "reasoning": judge_scores.get("reasoning", ""),
                }
            )
    df = pd.DataFrame(results)
    EVAL_RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(EVAL_RESULTS_CSV, index=False)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="AfyaPlus clinical evaluation pipeline")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip the API and write seeded fallback scores",
    )
    args = parser.parse_args()
    df = run_full_evaluation(force_offline=args.offline)
    summary = (
        df.groupby(["model", "feature"])[
            [
                "bleu_4",
                "rouge_l",
                "token_f1",
                "correctness",
                "groundedness",
                "relevance",
                "helpfulness",
                "judge_overall",
            ]
        ]
        .mean()
        .round(3)
    )
    print(tabulate(summary, headers="keys", tablefmt="grid", floatfmt=".3f"))
    gates = assess_quality_gates(df)
    print("\nQuality gates")
    print(tabulate(gates, headers="keys", tablefmt="grid", showindex=False))
    print(f"\nWrote {EVAL_RESULTS_CSV}")


if __name__ == "__main__":
    main()
