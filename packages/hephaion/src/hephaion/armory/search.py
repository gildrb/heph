"""Cross-armory search: index and search across multiple armories."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from hephaion.armory.storage import MARKER_FILE, default_armory_home
from hephaion.materials import MATERIALS_DIR, iter_material_files
from hephaion.parameters.settings import load_raw_settings, save_setting

_SETTINGS_KEY = "known_armories"
_RECENT_SETTINGS_KEY = "recent_armories"
MAX_RECENT_ARMORIES = 3


@dataclass(frozen=True, slots=True)
class KnownArmory:
    path: Path
    exists: bool
    valid: bool

    @property
    def missing(self) -> bool:
        return not self.exists


@dataclass(frozen=True, slots=True)
class SearchResult:
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
    raw = load_raw_settings()
    entries = raw.get(key)
    if not isinstance(entries, list):
        return []
    armories: list[KnownArmory] = []
    seen: set[Path] = set()
    for entry in entries:
        path = Path(str(entry)).expanduser().resolve()
        if path in seen:
            continue
        seen.add(path)
        exists = path.is_dir()
        valid = exists and (path / MARKER_FILE).is_file()
        armories.append(KnownArmory(path=path, exists=exists, valid=valid))
    return armories


def load_known_armory_entries() -> list[KnownArmory]:
    return _load_armory_entries(_SETTINGS_KEY)


def load_recent_armory_entries() -> list[KnownArmory]:
    return _load_armory_entries(_RECENT_SETTINGS_KEY)


def load_known_armories() -> list[Path]:
    return [entry.path for entry in load_known_armory_entries() if entry.exists]


def load_available_armory_entries() -> list[KnownArmory]:
    armory_home = _resolved_armory_home()
    entries = [
        entry
        for entry in load_known_armory_entries()
        if entry.valid and _path_is_in_armory_home(entry.path, armory_home)
    ]
    seen = {entry.path for entry in entries}
    for entry in _discover_armory_home_entries(armory_home):
        if entry.path in seen:
            continue
        seen.add(entry.path)
        entries.append(entry)
    return entries


def load_available_armories() -> list[Path]:
    return [entry.path for entry in load_available_armory_entries()]


def discover_armory_home_entries() -> list[KnownArmory]:
    return _discover_armory_home_entries(_resolved_armory_home())


def _discover_armory_home_entries(armory_home: Path) -> list[KnownArmory]:
    if not armory_home.is_dir():
        return []
    entries: list[KnownArmory] = []
    try:
        children = sorted(armory_home.iterdir(), key=lambda path: path.name.lower())
    except OSError:
        return []
    for child in children:
        if child.name.startswith("."):
            continue
        try:
            resolved = child.resolve(strict=False)
        except (OSError, RuntimeError, ValueError):
            continue
        if not _path_is_in_armory_home(resolved, armory_home):
            continue
        if resolved.is_dir() and (resolved / MARKER_FILE).is_file():
            entries.append(KnownArmory(path=resolved, exists=True, valid=True))
    return entries


def _resolved_armory_home() -> Path:
    return default_armory_home().expanduser().resolve()


def _path_is_in_armory_home(path: Path, armory_home: Path) -> bool:
    try:
        path.expanduser().resolve(strict=False).relative_to(armory_home)
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def save_known_armories(paths: list[Path]) -> None:
    save_setting(_SETTINGS_KEY, [str(p) for p in paths])


def add_known_armory(path: Path) -> list[Path]:
    path = path.expanduser().resolve()
    paths = [entry.path for entry in load_known_armory_entries()]
    if path not in paths:
        paths.insert(0, path)
        save_known_armories(paths)
    return paths


def remove_known_armory(path: Path) -> list[Path]:
    path = path.expanduser().resolve()
    paths = [entry.path for entry in load_known_armory_entries()]
    paths = [p for p in paths if p != path]
    save_known_armories(paths)
    return paths


def get_last_armory() -> Path | None:
    raw = load_raw_settings().get("last_armory_path")
    if not isinstance(raw, str) or not raw.strip():
        return None
    path = Path(raw).expanduser().resolve()
    if path.is_dir() and (path / MARKER_FILE).is_file():
        return path
    return None


def set_last_armory(path: Path) -> None:
    resolved = path.expanduser().resolve()
    save_setting("last_armory_path", str(resolved))
    recent_paths = [entry.path for entry in _load_armory_entries(_RECENT_SETTINGS_KEY)]
    save_setting(
        _RECENT_SETTINGS_KEY,
        [
            str(p)
            for p in [resolved, *[p for p in recent_paths if p != resolved]][:MAX_RECENT_ARMORIES]
        ],
    )


@dataclass
class CrossArmoryIndex:
    """Lightweight search index across multiple armories.

    Builds a simple keyword-frequency index over material chunks.
    For production use, this would be replaced with embedding-based search.
    """

    entries: list[SearchResult] = field(default_factory=list)

    def build(self, armories: list[Path]) -> None:
        self.entries.clear()
        for armory_path in armories:
            try:
                for material_file in iter_material_files(armory_path):
                    try:
                        text = material_file.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    rel = str(material_file.relative_to(armory_path))
                    for idx, chunk in enumerate(_chunk_text(text, max_chars=500, overlap=100)):
                        self.entries.append(
                            SearchResult(
                                armory_path=armory_path,
                                source_rel=rel,
                                chunk_index=idx,
                                chunk_text=chunk,
                                score=0.0,
                            )
                        )
            except Exception:  # nosec B112
                continue

    def search(self, query: str, limit: int = 20) -> list[SearchResult]:
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
