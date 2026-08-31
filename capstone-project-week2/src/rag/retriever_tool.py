"""Grounded LangChain retriever tool over the AfyaPlus knowledge vault."""

from __future__ import annotations

from typing import Optional

from langchain_core.tools import tool
from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever

from src.rag.ingestion import SIMILARITY_TOP_K, build_or_load_index

REFUSAL_PHRASE = "Information not found."
SIMILARITY_FLOOR = 0.25

_index: Optional[VectorStoreIndex] = None


def get_vector_index() -> VectorStoreIndex:
    global _index
    if _index is None:
        _index = build_or_load_index()
    return _index


def reset_index_cache() -> None:
    """Clear cached index (useful for tests or forced rebuilds)."""
    global _index
    _index = None


@tool
def search_afyaplus_knowledge_manual(query: str) -> str:
    """Search AfyaPlus insurance verification and clinical routing policy documents.

    Use this tool for questions about insurance cover tiers, waiting periods,
    outpatient and dental benefits, clinical routing red flags, pre-authorization,
    and Kenya Data Protection Act compliance rules.

    Do not use for general knowledge, travel advice, or calculations.
    """
    index = get_vector_index()
    retriever = VectorIndexRetriever(index=index, similarity_top_k=SIMILARITY_TOP_K)
    nodes = retriever.retrieve(query)

    qualified = [
        node
        for node in nodes
        if node.score is None or node.score >= SIMILARITY_FLOOR
    ]
    if not qualified:
        return REFUSAL_PHRASE

    blocks: list[str] = []
    for position, node in enumerate(qualified, start=1):
        source = node.metadata.get("file_name", "unknown")
        score_text = f"{node.score:.3f}" if node.score is not None else "n/a"
        blocks.append(
            f"[Citation {position} | source={source} | score={score_text}]\n{node.get_content()}"
        )
    return "\n\n".join(blocks)
