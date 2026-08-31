from prompt_cost_analysis import count_tokens
PRICE_IN, REQ, DAYS, KSH = 0.15 / 1_000_000, 40_000, 30, 130

verbose = ("You are a careful clinical assistant. Think step by step. "
           "First restate the question, then reason, then answer.")
direct  = "Answer the clinical question concisely and accurately."
saved   = count_tokens(verbose) - count_tokens(direct)
monthly = saved * PRICE_IN * REQ * DAYS
print(f"Saved {saved} tokens/request -> ${monthly:.2f}/mo  (~Ksh {monthly * KSH:,.0f}/mo)")