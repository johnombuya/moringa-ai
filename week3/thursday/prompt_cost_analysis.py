import tiktoken

def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

# Prompt Engineering techniques from Week 1
COT_PROMPT = """You are a clinical assistant. Think through the patient's symptoms step-by-step:
1. Identify key indicators.
2. Compare against triage protocols.
3. Formulate a safe recommendation.
Respond concisely."""

DIRECT_PROMPT = "You are a clinical assistant. Provide a safe triage recommendation: {symptoms}"

INPUT_COST_PER_TOKEN = 0.15 / 1_000_000   # gpt-4o-mini input rate
DAILY_REQS = 50_000

for name, prompt in [("Chain-of-Thought", COT_PROMPT), ("Direct", DIRECT_PROMPT)]:
    toks          = count_tokens(prompt)
    monthly_spend = (toks * INPUT_COST_PER_TOKEN) * DAILY_REQS * 30
    print(f"Technique: {name:<16} | Tokens: {toks:<4} | Monthly Cost: ${monthly_spend:.2f}")