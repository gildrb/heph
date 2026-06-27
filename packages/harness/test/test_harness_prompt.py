from __future__ import annotations

from pathlib import Path

import pytest
from harness.agent.prompt import build_system_prompt, build_system_prompt_sections
from harness.rag.context import estimate_tokens
from harness.rag.health import ExtractionHealthIssue
from harness.study import LearningPhase, LearningState, plan_turn


def test_build_system_prompt_includes_default_sections(armory: Path) -> None:
    prompt = build_system_prompt(armory_path=armory, source_files=["materials/python.md"])

    assert prompt.startswith("You are running inside Heph.")
    assert "Available tools:" in prompt
    assert "## Guidelines" in prompt
    assert "## Verification-First Operating Mode" not in prompt
    assert "## Tool Contract" not in prompt
    assert "## Recall Loop" not in prompt
    assert "## Accuracy" not in prompt
    assert "## Heph Operations" not in prompt
    assert "## Format" not in prompt


def test_default_prompt_and_common_steering_fit_token_budget() -> None:
    prompt = build_system_prompt()
    assert estimate_tokens(prompt) <= 600

    common_steering = [
        plan_turn(LearningState(), "what is this material about").prompt,
        plan_turn(LearningState(), "what do the notes say about this topic?").prompt,
        plan_turn(LearningState(), "explain the selected concept").prompt,
        plan_turn(
            LearningState(
                phase=LearningPhase.WAITING_FOR_READY,
                current_item="the selected concept",
            ),
            "ready",
        ).prompt,
    ]
    for steering in common_steering:
        assert estimate_tokens(f"{prompt}\n\n{steering}") <= 1000


def test_custom_system_prompt_is_skipped_without_path_trust(armory: Path) -> None:
    prompt_file = armory / ".harness" / "system_prompt.md"
    prompt_file.write_text("Custom system prompt.", encoding="utf-8")

    prompt = build_system_prompt(armory_path=armory, source_files=["materials/python.md"])

    assert prompt.startswith("You are running inside Heph.")
    assert "Custom system prompt." not in prompt


def test_custom_system_prompt_replaces_default_role_block_with_path_trust(
    armory: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompt_file = armory / ".harness" / "system_prompt.md"
    prompt_file.write_text("Custom system prompt.", encoding="utf-8")
    monkeypatch.setenv("HARNESS_TRUST_ARMORY_PROMPTS", str(armory.resolve()))

    prompt = build_system_prompt(armory_path=armory, source_files=["materials/python.md"])

    assert prompt.startswith("Custom system prompt.")
    assert "You are running inside Heph." not in prompt
    assert "## Recall Loop" not in prompt
    assert "## Guidelines" in prompt


def test_blank_custom_system_prompt_falls_back_to_default_role_block(
    armory: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompt_file = armory / ".harness" / "system_prompt.md"
    prompt_file.write_text("   \n", encoding="utf-8")
    monkeypatch.setenv("HARNESS_TRUST_ARMORY_PROMPTS", str(armory.resolve()))

    prompt = build_system_prompt(armory_path=armory, source_files=["materials/python.md"])

    assert prompt.startswith("You are running inside Heph.")
    assert "## Guidelines" in prompt


def test_build_system_prompt_truncates_material_file_list(armory: Path) -> None:
    material_files = [f"materials/file_{i}.md" for i in range(60)]

    prompt = build_system_prompt(armory_path=armory, source_files=material_files)

    assert "Available material files:" in prompt
    assert "materials/file_0.md" in prompt
    assert "materials/file_49.md" in prompt
    assert "materials/file_50.md" not in prompt


def test_build_system_prompt_includes_material_role_hints(armory: Path) -> None:
    prompt = build_system_prompt(
        armory_path=armory,
        source_files=[
            "materials/past-exams/2024.pdf",
            "materials/vocab/french.md",
            "materials/project/main.py",
        ],
    )

    assert "Material role hints:" in prompt
    assert "past exam: 1 file; e.g. materials/past-exams/2024.pdf" in prompt
    assert "vocabulary: 1 file; e.g. materials/vocab/french.md" in prompt
    assert "codebase: 1 file; e.g. materials/project/main.py" in prompt


def test_build_system_prompt_appends_memory_context(armory: Path) -> None:
    prompt = build_system_prompt(
        armory_path=armory,
        source_files=["materials/python.md"],
        memory_context="## Memory\n- Already studied binary search.",
    )

    assert "## Memory\n- Already studied binary search." in prompt


def test_build_system_prompt_without_armory_uses_default_role_block_and_date() -> None:
    prompt = build_system_prompt()

    assert prompt.startswith("You are running inside Heph.")
    assert "## Guidelines" in prompt
    assert "Current date: " in prompt
    assert "Armory workspace:" not in prompt


def test_build_system_prompt_instructs_citation_inspection(armory: Path) -> None:
    prompt = build_system_prompt(armory_path=armory, source_files=["materials/python.md"])

    assert "If asked what `[E1]` means" in prompt
    assert "quote that evidence" in prompt


def test_build_system_prompt_anchors_general_reasoning_to_material_evidence(
    armory: Path,
) -> None:
    prompt = build_system_prompt(armory_path=armory, source_files=["materials/python.md"])

    assert "For material-specific claims, reason from retrieved evidence" in prompt
    assert "Use general reasoning to explain evidence" in prompt
    assert "never as pretend file evidence" in prompt


def test_build_system_prompt_sections_render_matches_string_builder(armory: Path) -> None:
    sections = build_system_prompt_sections(
        armory_path=armory,
        source_files=["materials/python.md"],
    )

    assert sections.render() == build_system_prompt(
        armory_path=armory,
        source_files=["materials/python.md"],
    )
    assert sections.tool_docs.startswith("Available tools:")
    assert "Available tools:" in sections.tool_docs
    assert "- read_file: Read workspace file contents." in sections.tool_docs
    assert "Tool guidelines:" not in sections.tool_docs
    assert "Use edit_file for surgical changes" not in sections.guidelines
    assert "\nbash\n" not in sections.tool_docs
    assert "Tool arguments:" not in sections.tool_docs
    assert "materials/" in sections.guidelines


def test_system_prompt_has_single_pi_style_guidelines_section() -> None:
    prompt = build_system_prompt()

    assert prompt.count("## Guidelines") == 1
    assert "Tool guidelines:" not in prompt
    assert "## Tool Contract" not in prompt
    assert "## Accuracy" not in prompt
    assert "## Recall Loop" not in prompt


def test_system_prompt_keeps_output_blunt_without_decorative_style() -> None:
    prompt = build_system_prompt()

    assert "Answer with the minimum useful text" in prompt
    assert "No greetings, filler, praise, reassurance, emoji" in prompt
    assert "act professional" not in prompt.lower()


def test_tool_docs_are_generated_from_registry_schema() -> None:
    prompt = build_system_prompt()

    assert "- web_fetch: Fetch a web page when armory material is insufficient." in prompt
    assert "- create_armory: Create or repair a portable Heph armory." in prompt
    assert "- validate_armory: Validate" in prompt
    assert "  - url: The URL to fetch" not in prompt


def test_harness_operations_teaches_armory_contract() -> None:
    prompt = build_system_prompt()

    assert "Armory: portable workspace" in prompt
    assert "materials/" in prompt
    assert "User files go in `materials/`" in prompt
    assert "Use `create_armory` or `validate_armory`" in prompt


def test_unindexable_files_warning_in_prompt(armory: Path) -> None:
    prompt = build_system_prompt(
        armory_path=armory,
        source_files=["materials/python.md", "materials/slides.pdf"],
        unindexable_files={
            "materials/slides.pdf": "binary document; document conversion backend unavailable"
        },
    )

    assert "WARNING: The following files could not be indexed" in prompt
    assert "materials/slides.pdf" in prompt
    assert "document conversion backend unavailable" in prompt
    assert "Do NOT attempt to read them" in prompt
    assert "Do NOT answer questions about their contents" in prompt


def test_no_unindexable_warning_when_empty(armory: Path) -> None:
    prompt = build_system_prompt(
        armory_path=armory,
        source_files=["materials/python.md"],
        unindexable_files={},
    )

    assert "WARNING" not in prompt
    assert "could not be indexed" not in prompt


def test_extraction_health_warning_in_prompt(armory: Path) -> None:
    prompt = build_system_prompt(
        armory_path=armory,
        source_files=["materials/lecture.pdf"],
        extraction_health_issues=(
            ExtractionHealthIssue(
                source="materials/lecture.pdf",
                forbidden_text_present=("formula-not-decoded", "<!-- image -->"),
            ),
        ),
    )

    assert "WARNING: The following indexed files contain extraction health issues" in prompt
    assert "materials/lecture.pdf" in prompt
    assert "formula-not-decoded" in prompt
    assert "<!-- image -->" in prompt
    assert "Treat affected indexed chunks as unreliable extraction output" in prompt
    assert "Do NOT answer from affected files" in prompt
    assert "`heph health`" in prompt
