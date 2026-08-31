# AfyaPlus Generative Layer — Engineering Decision Memorandum

**To:** CTO and Medical Director  
**From:** Platform Engineering (observability capstone)  
**Re:** Six weeks of production AI without automated evaluation, drift monitoring, or cost tracking  
**Evaluation run mode:** offline

## Executive summary

The AfyaPlus generative layer has been answering clinical and insurance queries without automated quality gates, drift reports, or token accounting. We evaluated both **gpt-4o-mini** and **gpt-4o** on a **15-question** clinical set (30 model rows), simulated three months of traffic, and projected 30-day spend at 2,000 requests/day. Mean judge overall is **4.23/5** for mini and **4.81/5** for gpt-4o; Month 3 mean ROUGE-L is **0.3389** versus **0.4064** in Month 1; 30-day generative spend is **$25.22** against a **$1500** cap.

## Quality performance breakdown

Automated overlap (BLEU / ROUGE-L / token F1) plus an LLM judge (correctness, groundedness, relevance, helpfulness) were scored for every row. gpt-4o-mini passed **2** of 3 feature gates; gpt-4o passed **3** of 3. Mean groundedness is **4.47** (mini) vs **5.00** (gpt-4o). Clinically this means mini is cheaper on overlap-heavy protocol restatements but is more likely to drop numbers, waiting periods, or red-flag lists — the details clinicians need for safe routing.

## Cost and efficiency analysis

At the documented 75/25 canary, 30-day token spend is **$25.22** (**$0.84/day** vs a **$50** daily cap). Routing each feature to the cheapest model that still **PASSES** the quality gate saves **$58.96** versus sending all traffic to gpt-4o and **$-5.91** versus the current canary. Human review of the same 59,940 tickets at an assumed **$2.50/ticket** would cost **$149,850** — token inference remains far cheaper than full human validation, but it does not replace a clinician on failed gates.

Recommended routing from this run: chronic_care_referral → gpt-4o; insurance_routing → gpt-4o-mini; pediatric_triage → gpt-4o-mini.

## Systemic operational risks

First detected drift: **Month 1**, column **input_length**. Month 3 latency mean is **1101.6 ms** with ROUGE-L **0.3389**. That pattern matches longer, more complex production questions than the pre-deploy baseline. Hallucination risk is highest where groundedness fails the 4.0 gate: unsupported dosages or cover terms must not ship. Waiting-period emergencies remain a policy exception (bypass cover checks) and must stay out of cost-only routing.

## Actionable engineering roadmap

1. **Route by feature, not by default canary.** Keep any FAIL feature on gpt-4o. Estimated 30-day saving vs all-gpt-4o: **$58.96**, with groundedness held at the 4.0 safety bar.
2. **Page on first-column drift.** Alert already isolates Month 1 / input_length. Wire the Prometheus `/metrics` gauges to the existing 80%/95% budget WARN/CRIT policy so spend and quality share one on-call path.
3. **Do not drop human review on pediatric_triage FAIL rows.** Token cost of the full 30-day corpus is **$25.22** versus **$149,850** for blanket human review; spend the human budget only on gate failures and Month 3 drifted slices.

*Coursework snapshot — not a live AfyaPlus production certification.*
