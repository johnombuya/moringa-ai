import pandas as pd
from tabulate import tabulate
from evaluation_data import EVAL_DATASET
from model_querier import query_model
from evaluator import evaluate_response
from llm_judge import llm_judge

MODELS = ["gpt-4o-mini", "gpt-4o"]

def run_full_evaluation():
    results = []
    for example in EVAL_DATASET:
        for model in MODELS:
            hypothesis   = query_model(model, example["question"])
            auto_scores  = evaluate_response(example["reference"], hypothesis)
            judge_scores = llm_judge(example["question"], example["reference"], hypothesis)
            results.append({
                "id": example["id"], "model": model,
                **auto_scores,
                "correctness":   judge_scores.get("correctness", 0),
                "groundedness":  judge_scores.get("groundedness", 0),
                "helpfulness":   judge_scores.get("helpfulness", 0),
                "judge_overall": judge_scores.get("overall", 0),
                "reasoning":     judge_scores.get("reasoning", ""),
            })
    return pd.DataFrame(results)

if __name__ == "__main__":
    df = run_full_evaluation()
    df.to_csv("full_evaluation_results.csv", index=False)
    summary = df.groupby("model")[
        ["bleu_4","rouge_l","token_f1","correctness","groundedness","helpfulness","judge_overall"]
    ].mean().round(3)
    print(tabulate(summary, headers='keys', tablefmt='grid', floatfmt=".3f"))
    print("\nNote: Automated metrics scored 0-1. LLM Judge metrics scored 1-5.")