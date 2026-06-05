from __future__ import annotations

import contextlib
import json
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from hephaion._types import is_object_list, is_string_mapping

_EXAM_BANK_FILE = "exam_bank.json"
_EXAM_BANK_VERSION = 1


@dataclass(frozen=True, slots=True)
class ExamBankItem:
    id: str
    question: str
    question_source_refs: tuple[str, ...]
    result_source_refs: tuple[str, ...]
    support_source_refs: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    marks: int | None = None
    time_limit_minutes: int | None = None

    @property
    def source_refs(self) -> list[str]:
        return list(
            dict.fromkeys(
                (
                    *self.question_source_refs,
                    *self.result_source_refs,
                    *self.support_source_refs,
                )
            )
        )

    @property
    def effective_time_limit_minutes(self) -> int:
        if self.time_limit_minutes is not None:
            return self.time_limit_minutes
        if self.marks is None:
            return 5
        if self.marks <= 4:
            return 3
        if self.marks <= 10:
            return 8
        return 12


@dataclass(frozen=True, slots=True)
class ExamBank:
    items: tuple[ExamBankItem, ...]

    @property
    def eligible_items(self) -> tuple[ExamBankItem, ...]:
        return tuple(item for item in self.items if item.question and item.result_source_refs)


def exam_bank_path(armory_path: Path) -> Path:
    return armory_path / ".hephaion" / _EXAM_BANK_FILE


def load_exam_bank(armory_path: Path) -> ExamBank:
    path = exam_bank_path(armory_path)
    if not path.is_file():
        return ExamBank(items=())
    with contextlib.suppress(json.JSONDecodeError, OSError):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if is_string_mapping(payload):
            return _exam_bank_from_payload(payload)
    return ExamBank(items=())


def select_exam_bank_item(
    bank: ExamBank,
    *,
    topic: str = "",
    rng: random.Random | None = None,
) -> ExamBankItem | None:
    items = _focused_items(bank.eligible_items, topic)
    if not items:
        return None
    chooser = rng or random.SystemRandom()
    return chooser.choice(list(items))


def exam_bank_build_prompt() -> str:
    return (
        "Execute EXAM_BANK_BUILD.\n"
        "Program:\n"
        "1. Inspect the indexed armory materials with material tools.\n"
        "2. Build a structured JSON state file at `.hephaion/exam_bank.json`.\n"
        "3. The file format is exactly:\n"
        "{\n"
        '  "version": 1,\n'
        '  "items": [\n'
        "    {\n"
        '      "id": "stable unique id",\n'
        '      "question": "learner-facing prompt copied or faithfully transcribed",\n'
        '      "question_source_refs": ["materials/...#chunk=N"],\n'
        '      "result_source_refs": ["materials/...#chunk=N"],\n'
        '      "support_source_refs": ["materials/...#chunk=N"],\n'
        '      "topics": ["short topic labels"],\n'
        '      "marks": 0,\n'
        '      "time_limit_minutes": 0\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Rules:\n"
        "- Treat this as state generation, not a chat answer.\n"
        "- Use document structure, layout, cross-references, and semantic relationship between "
        "a prompt and its source-provided evaluation material. Do not implement or rely on "
        "fixed label words, filename words, course names, or private corpus vocabulary.\n"
        "- Include an item only when the material provides both the prompt and source-backed "
        "material that can assess an attempt at that prompt.\n"
        "- If no eligible items exist, write version 1 with an empty items array.\n"
        "- Every source ref must be an indexed `source#chunk=N` ref returned by material tools.\n"
        "- Do not ask the learner a question during this build step.\n"
        "- After writing the file, report how many eligible items were written and tell the "
        "user to run `/exam` again."
    )


def _exam_bank_from_payload(payload: Mapping[str, object]) -> ExamBank:
    if payload.get("version") != _EXAM_BANK_VERSION:
        return ExamBank(items=())
    raw_items = payload.get("items")
    if not is_object_list(raw_items):
        return ExamBank(items=())
    items: list[ExamBankItem] = []
    for raw_item in raw_items:
        if not is_string_mapping(raw_item):
            continue
        item = _item_from_payload(raw_item)
        if item is not None:
            items.append(item)
    return ExamBank(items=tuple(items))


def _item_from_payload(data: Mapping[str, object]) -> ExamBankItem | None:
    question = _string_field(data, "question")
    question_refs = _source_ref_list(data.get("question_source_refs"))
    result_refs = _source_ref_list(data.get("result_source_refs"))
    if not question or not question_refs:
        return None
    return ExamBankItem(
        id=_string_field(data, "id") or _fallback_id(question, question_refs),
        question=question,
        question_source_refs=tuple(question_refs),
        result_source_refs=tuple(result_refs),
        support_source_refs=tuple(_source_ref_list(data.get("support_source_refs"))),
        topics=tuple(_string_list(data.get("topics"))),
        marks=_positive_int_or_none(data.get("marks")),
        time_limit_minutes=_positive_int_or_none(data.get("time_limit_minutes")),
    )


def _focused_items(items: Sequence[ExamBankItem], topic: str) -> tuple[ExamBankItem, ...]:
    if not topic:
        return tuple(items)
    normalized_topic = topic.casefold()
    focused = [
        item
        for item in items
        if normalized_topic in item.question.casefold()
        or any(normalized_topic in item_topic.casefold() for item_topic in item.topics)
    ]
    return tuple(focused or items)


def _string_field(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    return value.strip() if isinstance(value, str) else ""


def _string_list(value: object) -> list[str]:
    if not is_object_list(value):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _source_ref_list(value: object) -> list[str]:
    return list(dict.fromkeys(ref for ref in _string_list(value) if _source_ref_parts(ref)))


def _source_ref_parts(value: str) -> tuple[str, int] | None:
    source, separator, suffix = value.partition("#chunk=")
    if not separator or not source:
        return None
    with contextlib.suppress(ValueError):
        chunk_index = int(suffix)
        if chunk_index >= 0:
            return source, chunk_index
    return None


def _positive_int_or_none(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return None


def _fallback_id(question: str, question_refs: Sequence[str]) -> str:
    return f"{question_refs[0]}:{question[:80]}"


__all__ = [
    "ExamBank",
    "ExamBankItem",
    "exam_bank_build_prompt",
    "exam_bank_path",
    "load_exam_bank",
    "select_exam_bank_item",
]
