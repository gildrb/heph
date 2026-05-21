from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

_MAX_CONTEXT_CHARS = 4000
_SECTION_RE = re.compile(r"^##\s+", re.MULTILINE)


def _repo_readme_path() -> Path | None:
    package_root = Path(__file__).resolve().parents[1]
    for parent in (package_root, *package_root.parents):
        candidate = parent / "README.md"
        if candidate.is_file():
            return candidate
    return None


def _trim_readme(text: str) -> str:
    text = text.replace("<!-- Managed by scripts/sync_docs.py. Do not edit directly. -->", "")
    match = _SECTION_RE.search(text)
    if match is not None:
        text = text[: match.start()]
    return text.strip()[:_MAX_CONTEXT_CHARS].strip()


@lru_cache(maxsize=1)
def heph_product_context() -> str:
    readme_path = _repo_readme_path()
    if readme_path is None:
        return ""
    return _trim_readme(readme_path.read_text(encoding="utf-8"))
