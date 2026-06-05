"""Vocabulary file parser — scans armories for markdown vocab tables."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ai.logging import get_logger

from hephaion.materials import MATERIALS_DIR

_log = get_logger("hephaion.vocab.parser")

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
    normalized = [_normalize_header(header) for header in headers]
    front_idx = _first_matching_column(normalized, _FRONT_ALIASES)
    back_idx = _first_matching_column(normalized, _BACK_ALIASES)
    if front_idx is not None and back_idx is not None:
        return front_idx, back_idx
    return None


def _normalize_header(header: str) -> str:
    return header.strip().lower().replace(" ", "_").replace("-", "_")


def _first_matching_column(headers: list[str], aliases: set[str]) -> int | None:
    return next((index for index, header in enumerate(headers) if header in aliases), None)


def _table_cells(line: str) -> list[str] | None:
    row_match = _TABLE_ROW_RE.match(line.strip())
    if row_match is None:
        return None
    return [cell.strip() for cell in row_match.group(1).split("|")]


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
    line_index = 0

    while line_index < len(lines):
        table_cards, line_index = _parse_vocab_table(lines, line_index, rel)
        cards.extend(table_cards)

    if cards:
        _log.info(
            "vocab file parsed",
            extra={"fields": {"file": rel, "cards": len(cards)}},
        )
    return cards


def _parse_vocab_table(
    lines: list[str],
    header_index: int,
    source_file: str,
) -> tuple[list[VocabCard], int]:
    header_cells = _table_cells(lines[header_index])
    if header_cells is None:
        return [], header_index + 1

    col_indices = _detect_vocab_columns(header_cells)
    if col_indices is None:
        return [], header_index + 1

    row_index = header_index + 1
    if row_index >= len(lines):
        return [], row_index
    if not _TABLE_SEP_RE.match(lines[row_index].strip()):
        return [], row_index

    return _parse_vocab_rows(
        lines,
        row_index + 1,
        source_file=source_file,
        front_idx=col_indices[0],
        back_idx=col_indices[1],
    )


def _parse_vocab_rows(
    lines: list[str],
    row_index: int,
    *,
    source_file: str,
    front_idx: int,
    back_idx: int,
) -> tuple[list[VocabCard], int]:
    cards: list[VocabCard] = []
    while row_index < len(lines):
        cells = _table_cells(lines[row_index])
        if cells is None:
            break
        if card := _card_from_cells(
            cells,
            front_idx=front_idx,
            back_idx=back_idx,
            source_file=source_file,
        ):
            cards.append(card)
        row_index += 1
    return cards, row_index


def _card_from_cells(
    cells: list[str],
    *,
    front_idx: int,
    back_idx: int,
    source_file: str,
) -> VocabCard | None:
    if front_idx >= len(cells) or back_idx >= len(cells):
        return None
    front = cells[front_idx]
    back = cells[back_idx]
    if not front or not back:
        return None
    return VocabCard(front=front, back=back, source_file=source_file)


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
