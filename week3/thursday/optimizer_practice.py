from quality_cost_optimizer import evaluate_candidates, ModelCandidate, TaskRequirements

candidates = [
    ModelCandidate("gpt-4o",      0.95, 0.45, 1900, 0.04),
    ModelCandidate("gpt-4o-mini", 0.88, 0.03,  600, 0.07),
]
faq = TaskRequirements("faq", 0.80, 2000, 0.50, 0.10, "low", 15_000)
df = evaluate_candidates(candidates, faq)
print(df.to_string(index=False))
eligible = df[df["eligible"] == "ELIGIBLE"]
print("Cheapest eligible:", eligible.iloc[0]["model"] if len(eligible) else "none")