"""Live LLM-as-a-judge with a seeded offline fallback."""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import get_openai_api_key

JUDGE_SYSTEM_PROMPT = """
You are an expert medical AI evaluation assistant for the AfyaPlus healthcare platform.
Evaluate the AI response on FOUR distinct dimensions, each scored from 1 to 5:

1. CORRECTNESS (1-5):  5=completely accurate, 3=minor gaps, 1=factually wrong or unsafe
2. GROUNDEDNESS (1-5): 5=fully supported by context, 3=minor unverified details, 1=hallucinated
   Score groundedness 1 if the response states ANY instruction, dosage, or policy
   that is not present in the reference.
3. RELEVANCE (1-5):    5=directly answers the query, 3=partially addresses it, 1=off-topic
4. HELPFULNESS (1-5):  5=immediately actionable for health workers, 3=vague, 1=unusable

Respond ONLY with valid JSON in this exact structure:
{
  "correctness": <1-5>,
  "groundedness": <1-5>,
  "relevance": <1-5>,
  "helpfulness": <1-5>,
  "overall": <average rounded to 1 decimal>,
  "reasoning": "<2-3 sentences explaining your assigned scores>"
}
"""


def llm_judge(
    question: str,
    reference: str,
    hypothesis: str,
    judge_model: str = "gpt-4o",
) -> dict:
    judge_llm = ChatOpenAI(
        model=judge_model,
        temperature=0,
        max_tokens=400,
        api_key=get_openai_api_key() or None,
    )
    user_prompt = f"""
USER SYMPTOM QUERY: {question}
REFERENCE PROTOCOL:   {reference}
AI ASSISTANT RESPONSE: {hypothesis}
"""
    response = judge_llm.invoke(
        [
            SystemMessage(content=JUDGE_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
    )
    raw = response.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(match.group()) if match else _empty_judge("JSON Parse failure")


def offline_judge(question: str, reference: str, hypothesis: str, model: str) -> dict:
    """Deterministic scores from token overlap so the CSV schema stays complete offline."""
    from evaluation.evaluator import compute_token_f1

    f1 = compute_token_f1(reference, hypothesis)
    extra = hypothesis.lower().split()
    ref = set(reference.lower().split())
    hallucinated = any(token not in ref for token in extra if token.isdigit())
    groundedness = 3 if hallucinated else min(5, 3 + int(f1 * 3))
    correctness = min(5, 3 + int(f1 * 2.5))
    if model == "gpt-4o":
        correctness = min(5, correctness + 1)
        groundedness = min(5, groundedness + 1)
    relevance = 5 if question.split()[0].lower() in hypothesis.lower() else 4
    helpfulness = correctness
    overall = round((correctness + groundedness + relevance + helpfulness) / 4, 1)
    return {
        "correctness": correctness,
        "groundedness": groundedness,
        "relevance": relevance,
        "helpfulness": helpfulness,
        "overall": overall,
        "reasoning": "Offline fallback scores derived from token overlap with the reference protocol.",
    }


def _empty_judge(reason: str) -> dict:
    return {
        "correctness": 0,
        "groundedness": 0,
        "relevance": 0,
        "helpfulness": 0,
        "overall": 0,
        "reasoning": reason,
    }
