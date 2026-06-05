from __future__ import annotations

import json
from pathlib import Path

from hephaion.study.exam_bank import (
    exam_bank_build_prompt,
    exam_bank_path,
    load_exam_bank,
    select_exam_bank_item,
)


def test_exam_bank_runtime_has_no_regex_label_lists() -> None:
    source = Path("packages/hephaion/src/hephaion/study/exam_bank.py").read_text(encoding="utf-8")

    assert "re.compile" not in source
    assert "_RESULT_LABELS" not in source


def test_load_exam_bank_keeps_only_structurally_valid_refs(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    bank_path = exam_bank_path(armory)
    bank_path.parent.mkdir(parents=True)
    bank_path.write_text(
        json.dumps(
            {
                "version": 1,
                "items": [
                    {
                        "id": "valid",
                        "question": "Explain the invariant.",
                        "question_source_refs": ["materials/sheet.md#chunk=0"],
                        "result_source_refs": [
                            "materials/sheet.md#chunk=1",
                            "not-a-source-ref",
                        ],
                        "support_source_refs": ["materials/notes.md#chunk=3"],
                        "topics": ["invariants"],
                        "marks": 6,
                    },
                    {
                        "id": "missing-question-ref",
                        "question": "Explain the transition.",
                        "question_source_refs": [],
                        "result_source_refs": ["materials/sheet.md#chunk=2"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    bank = load_exam_bank(armory)

    assert len(bank.items) == 1
    item = bank.items[0]
    assert item.id == "valid"
    assert item.result_source_refs == ("materials/sheet.md#chunk=1",)
    assert item.effective_time_limit_minutes == 8
    selected_item = select_exam_bank_item(bank)
    assert selected_item is not None
    assert selected_item.question == "Explain the invariant."


def test_exam_bank_item_without_result_refs_is_not_eligible(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    bank_path = exam_bank_path(armory)
    bank_path.parent.mkdir(parents=True)
    bank_path.write_text(
        json.dumps(
            {
                "version": 1,
                "items": [
                    {
                        "id": "question-only",
                        "question": "Explain the invariant.",
                        "question_source_refs": ["materials/sheet.md#chunk=0"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    bank = load_exam_bank(armory)

    assert bank.items
    assert bank.eligible_items == ()
    assert select_exam_bank_item(bank) is None


def test_exam_bank_build_prompt_describes_state_program() -> None:
    prompt = exam_bank_build_prompt()

    assert "Execute EXAM_BANK_BUILD." in prompt
    assert "`.hephaion/exam_bank.json`" in prompt
    assert "fixed label words" in prompt
    assert "Do not ask the learner a question" in prompt
