from __future__ import annotations

from pathlib import Path

from hephaion import commands
from hephaion.armory.storage import initialize
from hephaion.chat.session import ChatSession
from hephaion.runtime import ChatConfig, Conversation


def test_registry_exposes_status_without_stats() -> None:
    registry = commands.get_registry()
    names = {suggestion.name for suggestion in registry.suggestions()}

    assert registry.find("status") is not None
    assert "status" in names
    assert registry.find("stats") is None
    assert "stats" not in names


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
