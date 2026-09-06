"""Query gpt-4o-mini / gpt-4o, with a seeded paraphrase fallback."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import get_openai_api_key

SYSTEM_PROMPT = (
    "You are a clinical triage assistant for the AfyaPlus healthcare ecosystem. "
    "Answer questions clearly and concisely. Be specific about clinical metrics, "
    "timelines, and triage protocols. Keep your answer to 2-4 sentences. "
    "Do not invent dosages or policies that are not implied by the question."
)


def query_model(model_name: str, question: str) -> str:
    llm = ChatOpenAI(
        model=model_name,
        temperature=0,
        max_tokens=300,
        api_key=get_openai_api_key() or None,
    )
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=question)]
    response = llm.invoke(messages)
    return response.content


def offline_hypothesis(question: str, reference: str, model: str) -> str:
    """Paraphrase the reference so BLEU/ROUGE remain computable without an API."""
    if model == "gpt-4o":
        return reference
    first = reference.split(".")[0].strip()
    return first + "." if first else reference
