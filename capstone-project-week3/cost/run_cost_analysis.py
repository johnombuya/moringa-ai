"""30-day token cost simulation, prompt comparison, and routing savings."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import tiktoken
from tabulate import tabulate

from config import (
    COST_DIR,
    DAILY_CAP_USD,
    DAILY_COSTS_CSV,
    DAILY_REQUESTS,
    FEATURES,
    GPT4O_TRAFFIC_SHARE,
    INPUT_USD_PER_1M,
    MINI_TRAFFIC_SHARE,
    MONTHLY_CAP_USD,
    OUTPUT_USD_PER_1M,
    PROMPT_COST_CSV,
    QUALITY_GATE_CSV,
    RANDOM_SEED,
    SAVINGS_CSV,
    SIMULATION_DAYS,
)

COT_PROMPT = """You are a clinical assistant. Think through the patient's symptoms step-by-step:
1. Identify key indicators.
2. Compare against triage protocols.
3. Formulate a safe recommendation.
Respond concisely."""

DIRECT_PROMPT = "You are a clinical assistant. Provide a safe triage recommendation: {symptoms}"

COMPLETION_TOKENS = {"gpt-4o-mini": 90, "gpt-4o": 140}


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("o200k_base")
    return len(encoding.encode(text))


def usd_for(model: str, input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * INPUT_USD_PER_1M[model] / 1_000_000
        + output_tokens * OUTPUT_USD_PER_1M[model] / 1_000_000
    )


def prompt_comparison() -> pd.DataFrame:
    sample = "Infant fever 39.2 C with lethargy. What is the routing destination?"
    rows = []
    for name, prompt in (("Chain-of-Thought", COT_PROMPT), ("Direct", DIRECT_PROMPT.format(symptoms=sample))):
        for model in ("gpt-4o-mini", "gpt-4o"):
            inp = count_tokens(prompt, model)
            out = COMPLETION_TOKENS[model]
            cost = usd_for(model, inp, out)
            rows.append(
                {
                    "prompt_config": name,
                    "model": model,
                    "input_tokens": inp,
                    "output_tokens": out,
                    "usd_per_request": round(cost, 6),
                }
            )
    df = pd.DataFrame(rows)
    COST_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROMPT_COST_CSV, index=False)
    return df


def simulate_30_days() -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    direct_tokens = count_tokens(DIRECT_PROMPT.format(symptoms="placeholder"), "gpt-4o-mini")
    rows = []
    for day in range(1, SIMULATION_DAYS + 1):
        for feature in FEATURES:
            feature_share = 1 / len(FEATURES)
            n = int(DAILY_REQUESTS * feature_share)
            n_mini = int(n * MINI_TRAFFIC_SHARE)
            n_4o = n - n_mini
            for model, count in (("gpt-4o-mini", n_mini), ("gpt-4o", n_4o)):
                inp = direct_tokens + int(rng.integers(12, 40))
                out = COMPLETION_TOKENS[model]
                spend = usd_for(model, inp, out) * count
                rows.append(
                    {
                        "day": day,
                        "feature": feature,
                        "model": model,
                        "requests": count,
                        "usd": round(spend, 4),
                    }
                )
    df = pd.DataFrame(rows)
    df.to_csv(DAILY_COSTS_CSV, index=False)
    return df


def savings_from_gates(daily: pd.DataFrame) -> pd.DataFrame:
    if not QUALITY_GATE_CSV.exists():
        raise FileNotFoundError(f"Run evaluation first: missing {QUALITY_GATE_CSV}")
    gates = pd.read_csv(QUALITY_GATE_CSV)
    month_by_model_feature = (
        daily.groupby(["model", "feature"], as_index=False)["usd"].sum()
        .rename(columns={"usd": "canary_usd"})
    )
    all_4o = daily[daily["model"] == "gpt-4o"].copy()
    scale = 1 / GPT4O_TRAFFIC_SHARE
    all_4o_month = (
        all_4o.groupby("feature", as_index=False)["usd"].sum()
        .assign(all_gpt4o_usd=lambda d: d["usd"] * scale)
        .drop(columns=["usd"])
    )

    routed = []
    for feature in FEATURES:
        eligible = gates[(gates["feature"] == feature) & (gates["gate"] == "PASS")]
        if eligible.empty:
            chosen = "gpt-4o"
        else:
            costs = {"gpt-4o-mini": 0.03, "gpt-4o": 0.45}
            chosen = min(eligible["model"].tolist(), key=lambda m: costs.get(m, 9))
        feature_daily = daily[daily["feature"] == feature]
        reqs = feature_daily["requests"].sum()
        inp = count_tokens(DIRECT_PROMPT.format(symptoms=feature), chosen)
        routed_usd = usd_for(chosen, inp, COMPLETION_TOKENS[chosen]) * reqs
        routed.append({"feature": feature, "routed_model": chosen, "optimized_usd": round(routed_usd, 4)})

    routed_df = pd.DataFrame(routed)
    out = all_4o_month.merge(routed_df, on="feature")
    canary = daily.groupby("feature", as_index=False)["usd"].sum().rename(columns={"usd": "canary_usd"})
    out = out.merge(canary, on="feature")
    out["savings_vs_all_gpt4o_usd"] = (out["all_gpt4o_usd"] - out["optimized_usd"]).round(4)
    out["savings_vs_canary_usd"] = (out["canary_usd"] - out["optimized_usd"]).round(4)
    out.to_csv(SAVINGS_CSV, index=False)
    return out, month_by_model_feature


def main() -> None:
    COST_DIR.mkdir(parents=True, exist_ok=True)
    prompts = prompt_comparison()
    print("Cost per request by prompt configuration")
    print(tabulate(prompts, headers="keys", tablefmt="grid", showindex=False))

    daily = simulate_30_days()
    by_model = daily.groupby("model", as_index=False)["usd"].sum()
    by_feature = daily.groupby("feature", as_index=False)["usd"].sum()
    print("\n30-day spend by model")
    print(tabulate(by_model, headers="keys", tablefmt="grid", showindex=False))
    print("\n30-day spend by feature")
    print(tabulate(by_feature, headers="keys", tablefmt="grid", showindex=False))

    total = daily["usd"].sum()
    print(f"\n30-day total: ${total:.2f}  (daily cap ${DAILY_CAP_USD:.2f}, monthly cap ${MONTHLY_CAP_USD:.2f})")
    print(f"Mean daily spend: ${total / SIMULATION_DAYS:.2f}")

    savings, _ = savings_from_gates(daily)
    print("\nRouting savings")
    print(tabulate(savings, headers="keys", tablefmt="grid", showindex=False))
    print(f"\nWrote {DAILY_COSTS_CSV}, {PROMPT_COST_CSV}, {SAVINGS_CSV}")


if __name__ == "__main__":
    main()
