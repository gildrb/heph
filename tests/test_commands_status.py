from __future__ import annotations

from pathlib import Path

import pytest

from hephaion import commands
from hephaion.armory.storage import initialize
from hephaion.chat.session import ChatSession
from hephaion.materials.importing import import_material_files
from hephaion.runtime import ChatConfig, Conversation


def test_registry_exposes_status_and_stats() -> None:
    registry = commands.get_registry()
    names = {suggestion.name for suggestion in registry.suggestions()}

    assert registry.find("status") is not None
    assert "status" in names
    assert registry.find("stats") is not None
    assert "stats" in names


def test_status_includes_session_usage_and_armory_stats(tmp_path: Path) -> None:
    armory = tmp_path / "status-armory"
    initialize(armory)
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="status-1",
        armory_path=armory,
    )
    session.conversation.add("user", "hello")
    session.conversation.add("assistant", "hi")

    result = commands.StatusCommand().handle(session, "")

    assert result.output is not None
    assert "Current session:" in result.output
    assert "Model:" in result.output
    assert "Turns:     1" in result.output
    assert "Assistant: 1 messages" in result.output
    assert "API calls:" in result.output
    assert "Tokens:" in result.output
    assert "Armory:" in result.output
    assert "Saved:" in result.output
    assert "Vocabulary:" in result.output


def test_import_command_refreshes_running_session_sources(tmp_path: Path) -> None:
    armory = tmp_path / "import-armory"
    initialize(armory)
    first = armory / "materials" / "first.md"
    first.write_text("# First\n", encoding="utf-8")
    imported = tmp_path / "imported.md"
    imported.write_text("# Imported\n", encoding="utf-8")
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="import-session",
        armory_path=armory,
        source_file_count=1,
        source_files=("materials/first.md",),
    )

    commands.ImportCommand().handle(session, str(imported))

    assert session.source_file_count == 2
    assert "materials/imported.md" in session.source_files
    assert session.rag_index is None


def test_import_command_flattens_folder_files_into_materials_root(tmp_path: Path) -> None:
    armory = tmp_path / "import-armory"
    initialize(armory)
    source_dir = tmp_path / "source-folder"
    nested_dir = source_dir / "nested"
    nested_dir.mkdir(parents=True)
    hidden_dir = source_dir / ".hidden"
    hidden_dir.mkdir()
    (source_dir / "root.md").write_text("# Root\n", encoding="utf-8")
    (nested_dir / "nested.txt").write_text("Nested notes\n", encoding="utf-8")
    (nested_dir / "ignored.png").write_bytes(b"not imported")
    (hidden_dir / "secret.md").write_text("not indexed\n", encoding="utf-8")
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="import-session",
        armory_path=armory,
    )

    commands.ImportCommand().handle(session, str(source_dir))

    materials = armory / "materials"
    assert (materials / "root.md").read_text(encoding="utf-8") == "# Root\n"
    assert (materials / "nested.txt").read_text(encoding="utf-8") == "Nested notes\n"
    assert not (materials / "nested").exists()
    assert not (materials / "ignored.png").exists()
    assert not (materials / "secret.md").exists()
    assert session.source_files == ("materials/nested.txt", "materials/root.md")


def test_import_command_preserves_distinct_flattened_name_collisions(tmp_path: Path) -> None:
    armory = tmp_path / "import-armory"
    initialize(armory)
    source_dir = tmp_path / "source-folder"
    (source_dir / "a").mkdir(parents=True)
    (source_dir / "b").mkdir(parents=True)
    (source_dir / "a" / "notes.md").write_text("first\n", encoding="utf-8")
    (source_dir / "b" / "notes.md").write_text("second\n", encoding="utf-8")
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="import-session",
        armory_path=armory,
    )

    commands.ImportCommand().handle(session, str(source_dir))

    materials = armory / "materials"
    assert (materials / "notes.md").read_text(encoding="utf-8") == "first\n"
    assert (materials / "notes-2.md").read_text(encoding="utf-8") == "second\n"
    assert session.source_files == ("materials/notes-2.md", "materials/notes.md")


def test_import_command_accepts_quoted_file_path(tmp_path: Path) -> None:
    armory = tmp_path / "import-armory"
    initialize(armory)
    source_dir = tmp_path / "source folder"
    source_dir.mkdir()
    source_file = source_dir / "quoted.md"
    source_file.write_text("# Quoted\n", encoding="utf-8")
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="import-session",
        armory_path=armory,
    )

    commands.ImportCommand().handle(session, f'"{source_file}"')

    assert (armory / "materials" / "quoted.md").read_text(encoding="utf-8") == "# Quoted\n"


def test_import_material_files_skips_hidden_and_unsupported_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    nested = source / "nested"
    hidden = source / ".hidden"
    nested.mkdir(parents=True)
    hidden.mkdir()
    (source / "notes.md").write_text("notes", encoding="utf-8")
    (nested / "data.txt").write_text("data", encoding="utf-8")
    (source / "image.bin").write_bytes(b"\x00\x01")
    (hidden / "secret.md").write_text("secret", encoding="utf-8")
    dest = tmp_path / "armory" / "materials"

    result = import_material_files(source, dest)

    assert set(result.imported) == {"notes.md", "data.txt"}
    assert (dest / "notes.md").read_text(encoding="utf-8") == "notes"
    assert (dest / "data.txt").read_text(encoding="utf-8") == "data"
    assert not (dest / "secret.md").exists()
    assert result.skipped_unsupported >= 2


def test_import_material_files_preserves_collisions_and_skips_duplicates(
    tmp_path: Path,
) -> None:
    source = tmp_path / "notes.md"
    source.write_text("new", encoding="utf-8")
    dest = tmp_path / "materials"
    dest.mkdir()
    (dest / "notes.md").write_text("old", encoding="utf-8")

    first = import_material_files(source, dest)
    second = import_material_files(source, dest)

    assert first.imported == ("notes-2.md",)
    assert (dest / "notes.md").read_text(encoding="utf-8") == "old"
    assert (dest / "notes-2.md").read_text(encoding="utf-8") == "new"
    assert second.imported == ()
    assert second.skipped_duplicates == 1


def test_import_material_files_skips_symlink_targets(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    real = source / "real.md"
    real.write_text("real", encoding="utf-8")
    link = source / "linked.md"
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("symlinks are not supported on this filesystem")

    result = import_material_files(source, tmp_path / "materials")

    assert result.imported == ("real.md",)
    assert result.skipped_unsupported == 1
