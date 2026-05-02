from __future__ import annotations

from pathlib import Path

from hephaistos.agent.persona import TUTOR
from hephaistos.agent.prompt import build_system_prompt, build_system_prompt_sections


def test_build_system_prompt_includes_default_sections(armory: Path) -> None:
    prompt = build_system_prompt(armory_path=armory, source_files=["materials/python.md"])

    assert prompt.startswith("Hephaistos. A study drill engine.")
    assert "## Study Loop" in prompt
    assert "## Accuracy Rules" in prompt
    assert "## Verification-First Operating Mode" in prompt
    assert "## Tools" in prompt
    assert "## Hephaistos Operations" in prompt
    assert "## Format" in prompt


def test_custom_system_prompt_replaces_default_role_block(armory: Path) -> None:
    prompt_file = armory / ".hephaistos" / "system_prompt.md"
    prompt_file.write_text("Custom persona.", encoding="utf-8")

    prompt = build_system_prompt(armory_path=armory, source_files=["materials/python.md"])

    assert prompt.startswith("Custom persona.")
    assert "Hephaistos. A study drill engine." not in prompt
    assert "## Study Loop" not in prompt


def test_blank_custom_system_prompt_falls_back_to_default_persona(armory: Path) -> None:
    prompt_file = armory / ".hephaistos" / "system_prompt.md"
    prompt_file.write_text("   \n", encoding="utf-8")

    prompt = build_system_prompt(armory_path=armory, source_files=["materials/python.md"])

    assert prompt.startswith("Hephaistos. A study drill engine.")
    assert "## Study Loop" in prompt


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


def test_build_system_prompt_without_armory_uses_persona_study_loop_and_date() -> None:
    prompt = build_system_prompt(persona=TUTOR)

    assert prompt.startswith(TUTOR.role_block)
    assert "## Study Loop" in prompt
    assert "Current date: " in prompt
    assert "Armory workspace:" not in prompt


def test_build_system_prompt_instructs_citation_inspection(armory: Path) -> None:
    prompt = build_system_prompt(armory_path=armory, source_files=["materials/python.md"])

    assert "If the user asks what a citation like `[E1]` means" in prompt
    assert "quote the matching evidence text" in prompt


def test_build_system_prompt_sections_render_matches_string_builder(armory: Path) -> None:
    sections = build_system_prompt_sections(
        armory_path=armory,
        source_files=["materials/python.md"],
    )

    assert sections.render() == build_system_prompt(
        armory_path=armory,
        source_files=["materials/python.md"],
    )
    assert sections.tool_docs.startswith("## Tools")
    assert "### read_file" in sections.tool_docs
    assert "materials/" in sections.hephaistos_operations


def test_tool_docs_are_generated_from_registry_schema() -> None:
    prompt = build_system_prompt()

    assert "### web_fetch" in prompt
    assert "### create_armory" in prompt
    assert "### validate_armory" in prompt
    assert "- `url` (required): The URL to fetch" in prompt


def test_hephaistos_operations_teaches_armory_contract() -> None:
    prompt = build_system_prompt()

    assert "A Hephaistos armory is a portable study workspace" in prompt
    assert "materials/" in prompt
    assert "Do not create `source/`, `library/`, or `notes/` folders" in prompt
    assert "use `create_armory` or `validate_armory`" in prompt
