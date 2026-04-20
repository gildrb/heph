from __future__ import annotations

from pathlib import Path

from hephaistos.harness.persona import TUTOR
from hephaistos.harness.prompt import build_system_prompt


def test_build_system_prompt_includes_default_sections(armory: Path) -> None:
    prompt = build_system_prompt(armory_path=armory, source_files=["source/python.md"])

    assert prompt.startswith("Hephaistos. A drill instructor for exam preparation.")
    assert "## Study Loop" in prompt
    assert "## Accuracy Rules" in prompt
    assert "## Tools" in prompt
    assert "## Format" in prompt


def test_custom_system_prompt_replaces_default_role_block(armory: Path) -> None:
    prompt_file = armory / ".hephaistos" / "system_prompt.md"
    prompt_file.write_text("Custom persona.", encoding="utf-8")

    prompt = build_system_prompt(armory_path=armory, source_files=["source/python.md"])

    assert prompt.startswith("Custom persona.")
    assert "Hephaistos. A drill instructor for exam preparation." not in prompt
    assert "## Study Loop" not in prompt


def test_blank_custom_system_prompt_falls_back_to_default_persona(armory: Path) -> None:
    prompt_file = armory / ".hephaistos" / "system_prompt.md"
    prompt_file.write_text("   \n", encoding="utf-8")

    prompt = build_system_prompt(armory_path=armory, source_files=["source/python.md"])

    assert prompt.startswith("Hephaistos. A drill instructor for exam preparation.")
    assert "## Study Loop" in prompt


def test_build_system_prompt_truncates_source_file_list(armory: Path) -> None:
    source_files = [f"source/file_{i}.md" for i in range(60)]

    prompt = build_system_prompt(armory_path=armory, source_files=source_files)

    assert "Available source files:" in prompt
    assert "source/file_0.md" in prompt
    assert "source/file_49.md" in prompt
    assert "source/file_50.md" not in prompt


def test_build_system_prompt_appends_memory_context(armory: Path) -> None:
    prompt = build_system_prompt(
        armory_path=armory,
        source_files=["source/python.md"],
        memory_context="## Memory\n- Already studied binary search.",
    )

    assert "## Memory\n- Already studied binary search." in prompt


def test_build_system_prompt_without_armory_uses_persona_study_loop_and_date() -> None:
    prompt = build_system_prompt(persona=TUTOR)

    assert prompt.startswith(TUTOR.role_block)
    assert "## Study Loop" in prompt
    assert "Current date: " in prompt
    assert "Armory workspace:" not in prompt
