from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_MAX_CONTEXT_CHARS = 4000
_MAX_ROUTING_CONTEXT_CHARS = 360
_ASSISTANT_CONTEXT_PATH = Path("docs/developers/heph-context.md")
_ROUTING_CONTEXT_LINES = (
    "Heph is the product: the selected model plus the local validation harness.",
    "heph_help explains how Heph works, setup, commands, and settings.",
    "heph_action performs exact app ops: create/validate/import armories or materials.",
    "User-source/corpus-content intent stays material-scoped. App-help intents use no retrieval.",
)


def _repo_root() -> Path | None:
    package_root = Path(__file__).resolve().parents[1]
    for parent in (package_root, *package_root.parents):
        if (parent / _ASSISTANT_CONTEXT_PATH).is_file():
            return parent
    return None


@lru_cache(maxsize=1)
def heph_product_context() -> str:
    repo_root = _repo_root()
    if repo_root is None:
        return ""
    context_path = repo_root / _ASSISTANT_CONTEXT_PATH
    if not context_path.is_file():
        return ""
    return context_path.read_text(encoding="utf-8").strip()[:_MAX_CONTEXT_CHARS].strip()


@lru_cache(maxsize=1)
def heph_product_routing_context() -> str:
    context = "\n".join(f"- {line}" for line in _ROUTING_CONTEXT_LINES)
    if len(context) <= _MAX_ROUTING_CONTEXT_CHARS:
        return context
    return context[:_MAX_ROUTING_CONTEXT_CHARS].rstrip()
