"""Cross-armory search: index and search across multiple armories."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from hephaistos.armory.storage import MARKER_FILE
from hephaistos.materials import MATERIALS_DIR, iter_material_files
from hephaistos.parameters.settings import load_raw_settings, save_setting

_SETTINGS_KEY = "known_armories"
_RECENT_SETTINGS_KEY = "recent_armories"


@dataclass(frozen=True, slots=True)
class KnownArmory:
    """Persisted armory path with current filesystem status."""

    path: Path
    exists: bool
    valid: bool

    @property
    def missing(self) -> bool:
        return not self.exists


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A single search hit from a cross-armory query."""

    armory_path: Path
    source_rel: str
    chunk_index: int
    chunk_text: str
    score: float

    @property
    def source_path(self) -> Path:
        if self.source_rel.startswith(f"{MATERIALS_DIR}/"):
            return self.armory_path / self.source_rel
        return self.armory_path / MATERIALS_DIR / self.source_rel

    @property
    def armory_name(self) -> str:
        return self.armory_path.name


def _load_armory_entries(key: str) -> list[KnownArmory]:
    """Load persisted armory paths for *key* with current filesystem status."""
    raw = load_raw_settings()
    entries = raw.get(key)
    if not isinstance(entries, list):
        return []
    armories: list[KnownArmory] = []
    seen: set[Path] = set()
    for entry in entries:  # type: ignore[reportUnknownVariableType]
        path = Path(str(entry)).expanduser().resolve()
        if path in seen:
            continue
        seen.add(path)
        exists = path.is_dir()
        valid = exists and (path / MARKER_FILE).is_file()
        armories.append(KnownArmory(path=path, exists=exists, valid=valid))
    return armories


def load_known_armory_entries() -> list[KnownArmory]:
    """Load persisted armory paths with current filesystem status."""
    return _load_armory_entries(_SETTINGS_KEY)


def load_recent_armory_entries() -> list[KnownArmory]:
    """Load recently opened armory paths with current filesystem status."""
    return _load_armory_entries(_RECENT_SETTINGS_KEY)


def load_known_armories() -> list[Path]:
    """Load known armory paths that still exist on disk."""
    return [entry.path for entry in load_known_armory_entries() if entry.exists]


def save_known_armories(paths: list[Path]) -> None:
    """Persist the list of known armory paths."""
    save_setting(_SETTINGS_KEY, [str(p) for p in paths])


def add_known_armory(path: Path) -> list[Path]:
    """Add an armory to the known list. Returns the updated list."""
    path = path.expanduser().resolve()
    paths = [entry.path for entry in load_known_armory_entries()]
    if path not in paths:
        paths.insert(0, path)
        save_known_armories(paths)
    return paths


def remove_known_armory(path: Path) -> list[Path]:
    """Remove an armory from the known list. Returns the updated list."""
    path = path.expanduser().resolve()
    paths = [entry.path for entry in load_known_armory_entries()]
    paths = [p for p in paths if p != path]
    save_known_armories(paths)
    return paths


def get_last_armory() -> Path | None:
    """Return the last-opened armory path, or None if unset or invalid."""
    raw = load_raw_settings().get("last_armory_path")
    if not isinstance(raw, str) or not raw.strip():
        return None
    path = Path(raw).expanduser().resolve()
    if path.is_dir() and (path / MARKER_FILE).is_file():
        return path
    return None


def set_last_armory(path: Path) -> None:
    """Persist *path* as the most-recently-opened armory."""
    resolved = path.expanduser().resolve()
    save_setting("last_armory_path", str(resolved))
    recent_paths = [entry.path for entry in _load_armory_entries(_RECENT_SETTINGS_KEY)]
    save_setting(
        _RECENT_SETTINGS_KEY,
        [str(p) for p in [resolved, *[p for p in recent_paths if p != resolved]]],
    )


@dataclass
class CrossArmoryIndex:
    """Lightweight search index across multiple armories.

    Builds a simple keyword-frequency index over material chunks.
    For production use, this would be replaced with embedding-based search.
    """

    entries: list[SearchResult] = field(default_factory=list)

    def build(self, armories: list[Path]) -> None:
        """Build the index from a list of armory paths."""
        self.entries.clear()
        for armory_path in armories:
            try:
                self._index_armory(armory_path)
            except Exception:  # nosec B112
                continue

    def _index_armory(self, armory_path: Path) -> None:
        """Index material files from a single armory."""
        for material_file in iter_material_files(armory_path):
            try:
                text = material_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = str(material_file.relative_to(armory_path))
            chunks = _chunk_text(text, max_chars=500, overlap=100)
            for idx, chunk in enumerate(chunks):
                self.entries.append(
                    SearchResult(
                        armory_path=armory_path,
                        source_rel=rel,
                        chunk_index=idx,
                        chunk_text=chunk,
                        score=0.0,
                    )
                )

    def search(self, query: str, limit: int = 20) -> list[SearchResult]:
        """Search across all indexed armories. Returns results sorted by score."""
        if not query.strip():
            return []
        terms = [t.lower() for t in query.split() if len(t) >= 2]
        if not terms:
            return []
        scored: list[SearchResult] = []
        for entry in self.entries:
            text_lower = entry.chunk_text.lower()
            score = sum(1.0 for term in terms if term in text_lower)
            if score > 0:
                scored.append(
                    SearchResult(
                        armory_path=entry.armory_path,
                        source_rel=entry.source_rel,
                        chunk_index=entry.chunk_index,
                        chunk_text=entry.chunk_text,
                        score=score / len(terms),
                    )
                )
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:limit]


def _chunk_text(text: str, max_chars: int = 500, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks by paragraph boundaries."""
    if len(text) <= max_chars:
        return [text] if text.strip() else []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            last_nl = text.rfind("\n", start, end)
            if last_nl > start:
                end = last_nl
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
        if start <= (end - max_chars):
            start = end
    return chunks
