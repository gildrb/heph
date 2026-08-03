"""Public RAG configuration constants."""

from __future__ import annotations

import os

EMBED_MODEL_ENV = "HARNESS_EMBED_MODEL"
MAX_DENSE_QUERY_VARIANTS = 4
EMBEDDING_BATCH_SIZE = 64

__all__ = [
    "EMBEDDING_BATCH_SIZE",
    "EMBED_MODEL_ENV",
    "MAX_DENSE_QUERY_VARIANTS",
]


def configured_embedding_model() -> str | None:
    value = os.environ.get(EMBED_MODEL_ENV, "").strip()
    return value or None
