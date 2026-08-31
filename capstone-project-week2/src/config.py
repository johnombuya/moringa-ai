"""Central configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_MANUAL_DIR = PROJECT_ROOT / "knowledge-manual"
STORAGE_DIR = PROJECT_ROOT / "storage"

load_dotenv(PROJECT_ROOT / ".env")


def get_openai_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise ValueError("OPENAI_API_KEY is not set. Copy .env.example to .env and add your key.")
    return key


def get_chat_model() -> str:
    return os.environ.get("CHAT_MODEL", "gpt-4o-mini").strip()


def get_embed_model() -> str:
    return os.environ.get("EMBED_MODEL", "text-embedding-3-small").strip()
