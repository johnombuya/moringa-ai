"""LlamaIndex knowledge vault ingestion and persistence."""

from __future__ import annotations

from pathlib import Path

from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.settings import Settings
from llama_index.embeddings.openai import OpenAIEmbedding

from src.config import KNOWLEDGE_MANUAL_DIR, STORAGE_DIR, get_embed_model, get_openai_api_key

CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
SIMILARITY_TOP_K = 3


def _configure_settings() -> None:
    Settings.embed_model = OpenAIEmbedding(
        model=get_embed_model(),
        api_key=get_openai_api_key(),
    )


def _storage_is_ready(storage_dir: Path) -> bool:
    return storage_dir.exists() and any(storage_dir.iterdir())


def build_or_load_index(
    knowledge_dir: Path | None = None,
    storage_dir: Path | None = None,
    *,
    force_rebuild: bool = False,
) -> VectorStoreIndex:
    """Build a fresh index or reload a persisted local vector store."""
    _configure_settings()
    knowledge_path = knowledge_dir or KNOWLEDGE_MANUAL_DIR
    storage_path = storage_dir or STORAGE_DIR

    if not force_rebuild and _storage_is_ready(storage_path):
        storage_context = StorageContext.from_defaults(persist_dir=str(storage_path))
        return load_index_from_storage(storage_context)

    if not knowledge_path.exists():
        raise FileNotFoundError(f"Knowledge manual directory not found: {knowledge_path}")

    documents = SimpleDirectoryReader(str(knowledge_path)).load_data()
    parser = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    nodes = parser.get_nodes_from_documents(documents)

    index = VectorStoreIndex(nodes)
    storage_path.mkdir(parents=True, exist_ok=True)
    index.storage_context.persist(persist_dir=str(storage_path))
    return index


def verify_openai_connectivity() -> None:
    """Confirm embeddings can be generated against the direct OpenAI API."""
    embed_model = OpenAIEmbedding(
        model=get_embed_model(),
        api_key=get_openai_api_key(),
    )
    vector = embed_model.get_text_embedding("AfyaPlus connectivity check")
    if not vector:
        raise RuntimeError("OpenAI embedding call returned an empty vector.")
