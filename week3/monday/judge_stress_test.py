from llm_judge import llm_judge

reference = "Give 5ml of oral rehydration solution after each loose stool."
hypothesis = (reference + " You may also double the dose if symptoms persist.")  # fabricated

before = llm_judge("Summarise the protocol", reference, hypothesis)

# Tighten the groundedness anchor (one line) in JUDGE_SYSTEM_PROMPT:
#   "Score groundedness 1 if the response states ANY instruction, dosage, or
#    policy that is not present in the reference."
after = llm_judge("Summarise the protocol", reference, hypothesis)

print(f"groundedness before: {before.get('groundedness')}  after: {after.get('groundedness')}")
# Typically correctness/relevance stay high both times (most text matches),
# but groundedness drops to 1-2 only AFTER the anchor explicitly bans
# unsupported claims - proving the rubric does the catching, not the model alone.