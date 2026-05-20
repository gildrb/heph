"""Vocabulary file parser — scans armories for markdown vocab tables."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from hephaistos.logging import get_logger
from hephaistos.materials import MATERIALS_DIR

_log = get_logger("vocab.parser")

# Column name pairs that indicate a vocabulary table.
# Each tuple is (front_aliases, back_aliases).
_FRONT_ALIASES = {
    "word",
    "front",
    "term",
    "source",
    "foreign",
    "question",
    "prompt",
    "l1",
    "source_word",
}

_BACK_ALIASES = {
    "translation",
    "back",
    "definition",
    "target",
    "answer",
    "meaning",
    "l2",
    "target_word",
}

_TABLE_ROW_RE = re.compile(r"^\|\s*(.+?)\s*\|$")
_TABLE_SEP_RE = re.compile(r"^\|[\s\-:|]+\|$")


@dataclass(frozen=True, slots=True)
class VocabCard:
    front: str
    back: str
    source_file: str


@dataclass(slots=True)
class VocabDeck:
    cards: list[VocabCard] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.cards)


def _detect_vocab_columns(headers: list[str]) -> tuple[int, int] | None:
    front_idx: int | None = None
    back_idx: int | None = None
    for i, h in enumerate(headers):
        norm = h.strip().lower().replace(" ", "_").replace("-", "_")
        if front_idx is None and norm in _FRONT_ALIASES:
            front_idx = i
        elif back_idx is None and norm in _BACK_ALIASES:
            back_idx = i
    if front_idx is not None and back_idx is not None:
        return front_idx, back_idx
    return None


def parse_vocab_file(file_path: Path, armory_root: Path) -> list[VocabCard]:
    """Parse a single markdown file and extract vocab cards.

    Returns an empty list if the file contains no recognizable vocab tables.
    """
    try:
        text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    rel = str(file_path.relative_to(armory_root))
    cards: list[VocabCard] = []
    lines = text.splitlines()
    i = 0

    while i < len(lines):
        # Look for a table header row.
        row_match = _TABLE_ROW_RE.match(lines[i].strip())
        if not row_match:
            i += 1
            continue

        header_cells = [c.strip() for c in row_match.group(1).split("|")]
        col_indices = _detect_vocab_columns(header_cells)
        if col_indices is None:
            i += 1
            continue

        front_idx, back_idx = col_indices

        # Next line must be a separator.
        i += 1
        if i >= len(lines):
            break
        if not _TABLE_SEP_RE.match(lines[i].strip()):
            continue
        i += 1

        # Read data rows.
        while i < len(lines):
            m = _TABLE_ROW_RE.match(lines[i].strip())
            if not m:
                break
            cells = [c.strip() for c in m.group(1).split("|")]
            if front_idx < len(cells) and back_idx < len(cells):
                front = cells[front_idx]
                back = cells[back_idx]
                if front and back:
                    cards.append(VocabCard(front=front, back=back, source_file=rel))
            i += 1

    if cards:
        _log.info(
            "vocab file parsed",
            extra={"fields": {"file": rel, "cards": len(cards)}},
        )
    return cards


def scan_armory(armory_path: Path) -> VocabDeck:
    """Scan an armory for vocabulary markdown files.

    Searches the armory ``materials/`` directory for ``*.md`` files containing
    recognizable vocabulary tables.
    """
    deck = VocabDeck()
    materials_dir = armory_path / MATERIALS_DIR

    if materials_dir.is_dir():
        for md_file in sorted(materials_dir.rglob("*.md")):
            if md_file.name.startswith("."):
                continue
            cards = parse_vocab_file(md_file, armory_path)
            if cards:
                rel = str(md_file.relative_to(armory_path))
                deck.source_files.append(rel)
                deck.cards.extend(cards)

    _log.info(
        "armory vocab scan complete",
        extra={
            "fields": {
                "armory": str(armory_path),
                "files": len(deck.source_files),
                "cards": deck.size,
            }
        },
    )
    return deck
