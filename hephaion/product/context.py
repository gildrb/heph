from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_MAX_CONTEXT_CHARS = 4000
_ASSISTANT_CONTEXT_PATH = Path("docs/developers/heph-context.md")


def _repo_readme_path() -> Path | None:
    package_root = Path(__file__).resolve().parents[1]
    for parent in (package_root, *package_root.parents):
        candidate = parent / "README.md"
        if candidate.is_file():
            return candidate
    return None


def _repo_root() -> Path | None:
    readme_path = _repo_readme_path()
    if readme_path is None:
        return None
    return readme_path.parent


@lru_cache(maxsize=1)
def heph_product_context() -> str:
    repo_root = _repo_root()
    if repo_root is None:
        return ""
    context_path = repo_root / _ASSISTANT_CONTEXT_PATH
    if not context_path.is_file():
        return ""
    return context_path.read_text(encoding="utf-8").strip()[:_MAX_CONTEXT_CHARS].strip()
