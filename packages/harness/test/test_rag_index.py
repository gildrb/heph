"""Tests for the RAG index."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

import pytest
from ai.providers.config import default_config
from ai.runtime import ChatConfig, Conversation
from harness.armory.storage import initialize
from harness.chat.session import ChatSession, create_plain_session
from harness.rag import index as rag_index
from harness.rag.chunker import Chunk, ChunkedDocument, ChunkStrategy
from harness.rag.context import EvidenceChunk, TurnEvidence
from harness.rag.index import (
    ArmoryIndex,
    build_index,
    load_or_build,
)
from heph import commands
from heph.commands import model as _commands_model
from interfaces.terminal.history import InputHistory
from interfaces.terminal.input import handle_input


@pytest.fixture
def armory(tmp_path: Path) -> Path:
    """Create a minimal armory with material files."""
    arm = tmp_path / "test-armory"
    initialize(arm)

    (arm / "materials" / "python.md").write_text(
        "# Python Basics\n\n"
        "Python is a high-level programming language.\n\n"
        "Variables are dynamically typed.\n\n"
        "Functions use the `def` keyword.\n"
    )
    (arm / "materials" / "rust.md").write_text(
        "# Rust Basics\n\n"
        "Rust is a systems programming language.\n\n"
        "Ownership and borrowing are core concepts.\n\n"
        "Cargo is the build tool.\n"
    )
    (arm / "materials" / "algorithms.md").write_text(
        "# Algorithms\n\n"
        "Binary search runs in O(log n) time.\n\n"
        "Quick sort has average O(n log n) complexity.\n\n"
        "Merge sort is stable and runs in O(n log n).\n"
    )
    return arm


def _save_cached_index(
    armory_path: Path,
    *,
    documents: list[ChunkedDocument],
    file_hashes: dict[str, str],
    strategy: ChunkStrategy = ChunkStrategy.AUTO,
) -> None:
    index = ArmoryIndex(armory_path, strategy=strategy)
    index.documents = documents
    index._file_hashes = file_hashes
    index.save()


def _converted_document(source: str, content_hash: str, text: str) -> ChunkedDocument:
    return ChunkedDocument(
        source=source,
        content_hash=content_hash,
        chunks=[
            Chunk(
                text=text,
                source=source,
                index=0,
                char_start=0,
                char_end=len(text),
                heading="Theorem",
                heading_level=1,
            )
        ],
    )


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits are not portable on Windows")
def test_cache_signing_key_uses_private_permissions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    key_path = tmp_path / "config" / "rag_cache.key"
    monkeypatch.setenv("HARNESS_RAG_CACHE_KEY_FILE", str(key_path))

    key = rag_index._cache_signing_key()

    assert key is not None
    assert stat.S_IMODE(key_path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(key_path.stat().st_mode) == 0o600


def test_file_hash_streams_without_read_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    material = tmp_path / "material.md"
    material.write_bytes(b"streamed")

    def fail_read_bytes(_path: Path) -> bytes:
        raise AssertionError("read_bytes should not be used for material hashes")

    monkeypatch.setattr(Path, "read_bytes", fail_read_bytes)

    assert rag_index._file_hash(material) == hashlib.sha256(b"streamed").hexdigest()[:16]


def test_file_hash_rejects_oversized_material(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    material = tmp_path / "large.md"
    material.write_bytes(b"12345")
    monkeypatch.setattr(rag_index, "_MAX_MATERIAL_HASH_BYTES", 4)

    assert rag_index._file_hash(material) is None


def test_docling_materials_have_default_index_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HARNESS_INDEX_FILE_TIMEOUT_SECONDS", raising=False)

    assert rag_index._file_timeout_seconds(Path("materials/report.pdf")) == 120
    assert rag_index._file_timeout_seconds(Path("materials/notes.md")) == 0


class TestArmoryIndexBuild:
    def test_build_finds_files(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        sources = {doc.source for doc in index.documents}
        assert "materials/python.md" in sources
        assert "materials/rust.md" in sources
        assert "materials/algorithms.md" in sources

    def test_build_creates_chunks(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        assert index.chunk_count > 0

    def test_build_reports_progress(self, armory: Path) -> None:
        events: list[tuple[str, str]] = []
        index = ArmoryIndex(armory)

        index.build(progress=lambda action, detail: events.append((action, detail)))

        assert any(action == "reading" for action, _detail in events)
        assert any(action == "indexed" for action, _detail in events)
        assert any("materials/python.md" in detail for _action, detail in events)

    def test_all_chunks_have_source(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        expected_sources = {
            "materials/python.md",
            "materials/rust.md",
            "materials/algorithms.md",
        }
        for chunk in index.all_chunks:
            assert chunk.source in expected_sources


class TestArmoryIndexPersist:
    def test_save_creates_file(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        path = index.save()
        assert path.exists()
        assert path.name == "rag_index.json"

    def test_save_creates_missing_state_root(self, tmp_path: Path) -> None:
        armory_path = tmp_path / "missing-armory"
        index = ArmoryIndex(armory_path)

        path = index.save()

        assert path == armory_path / ".harness" / "rag_index.json"
        assert path.is_file()

    def test_save_rejects_symlinked_index_file(self, armory: Path, tmp_path: Path) -> None:
        outside = tmp_path / "outside-index.json"
        outside.write_text("outside\n", encoding="utf-8")
        index_file = armory / ".harness" / "rag_index.json"
        try:
            index_file.symlink_to(outside)
        except OSError:
            pytest.skip("symlinks are not supported on this filesystem")
        index = ArmoryIndex(armory)
        index.build()

        with pytest.raises(OSError, match="must not be a symlink"):
            index.save()

        assert outside.read_text(encoding="utf-8") == "outside\n"

    def test_save_load_roundtrip(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        index.save()

        loaded = ArmoryIndex(armory)
        assert loaded.load()
        assert len(loaded.documents) == len(index.documents)
        assert loaded.chunk_count == index.chunk_count

    def test_load_validates_hashes_without_rechunking(
        self,
        armory: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        index = ArmoryIndex(armory)
        index.build()
        index.save()

        def fail_chunk_file(*_args: object, **_kwargs: object) -> None:
            raise AssertionError("load must not rebuild chunks")

        monkeypatch.setattr("harness.rag.index.chunk_file", fail_chunk_file)

        loaded = ArmoryIndex(armory)
        assert loaded.load()
        assert loaded.chunk_count == index.chunk_count

    def test_load_removes_legacy_embedding_caches(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        index.save()
        stale = armory / ".harness" / "embeddings_old-model.json"
        stale.write_text('{"embeddings": [[1.0]]}', encoding="utf-8")

        loaded = ArmoryIndex(armory)
        assert loaded.load()
        assert not stale.exists()
        assert not list((armory / ".harness").glob("embeddings_*.json"))

    def test_load_missing_returns_false(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        assert not index.load()

    def test_load_corrupt_returns_false(self, armory: Path) -> None:
        index_file = armory / ".harness" / "rag_index.json"
        index_file.parent.mkdir(parents=True, exist_ok=True)
        index_file.write_text("not valid json{{{")

        index = ArmoryIndex(armory)
        assert not index.load()

    def test_load_rejects_signed_cache_when_large_documents_are_tampered(
        self,
        armory: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv(
            "HARNESS_RAG_CACHE_KEY_FILE",
            str(tmp_path / "config" / "rag_cache.key"),
        )
        monkeypatch.setenv("HARNESS_INDEX_VERIFY_DOCUMENT_DIGEST_LIMIT", "0")
        index = ArmoryIndex(armory)
        index.build()
        index.save()
        index_file = armory / ".harness" / "rag_index.json"
        data = json.loads(index_file.read_text(encoding="utf-8"))
        data["documents"][0]["chunks"][0]["text"] = "hidden forged theorem"
        index_file.write_text(json.dumps(data), encoding="utf-8")

        loaded = ArmoryIndex(armory)

        assert not loaded.load()


class TestArmoryIndexStaleness:
    def test_empty_index_is_stale(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        assert index.is_stale()

    def test_fresh_index_is_not_stale(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        assert not index.is_stale()

    def test_new_file_makes_stale(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        assert not index.is_stale()

        (armory / "materials" / "new.md").write_text("# New content\n")
        assert index.is_stale()

    def test_edited_file_makes_stale(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        assert not index.is_stale()

        (armory / "materials" / "python.md").write_text("# Changed content\n")
        assert index.is_stale()

    def test_edited_file_makes_stale_above_legacy_digest_verify_limit(
        self,
        armory: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        index = ArmoryIndex(armory)
        index.build()
        monkeypatch.setenv("HARNESS_INDEX_VERIFY_DOCUMENT_DIGEST_LIMIT", "0")

        (armory / "materials" / "python.md").write_text("# Changed content\n")

        assert index.is_stale()

    def test_unsupported_file_does_not_make_fresh_index_stale(self, armory: Path) -> None:
        (armory / "materials" / "data.bin").write_bytes(b"\x00\x01\x02\x03")

        index = ArmoryIndex(armory)
        index.build()

        assert not index.is_stale()

        index.save()
        loaded = ArmoryIndex(armory)
        assert loaded.load()
        assert not loaded.is_stale()

    def test_docling_file_without_backend_does_not_make_fresh_index_stale(
        self,
        armory: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("harness.rag.index._can_convert_binary_file", lambda _path: False)
        (armory / "materials" / "doc.pdf").write_bytes(b"%PDF-1.4\x00fake pdf")

        index = ArmoryIndex(armory)
        index.build()

        assert not index.is_stale()

        index.save()
        loaded = ArmoryIndex(armory)
        assert loaded.load()
        assert not loaded.is_stale()

    def test_failed_binary_file_becomes_stale_when_converter_available(
        self,
        armory: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        pdf = armory / "materials" / "scan.pdf"
        pdf.write_bytes(b"%PDF-1.4\x00fake pdf")
        monkeypatch.setattr("harness.rag.index._can_convert_binary_file", lambda _path: False)

        index = ArmoryIndex(armory)
        index.build()
        assert not index.is_stale()

        monkeypatch.setattr("harness.rag.index._can_convert_binary_file", lambda _path: True)

        assert index.is_stale()


class TestBuildIndex:
    def test_build_index_returns_index(self, armory: Path) -> None:
        index = build_index(armory)
        assert isinstance(index, ArmoryIndex)
        assert index.chunk_count > 0

    def test_build_index_persists(self, armory: Path) -> None:
        build_index(armory)
        assert (armory / ".harness" / "rag_index.json").exists()


class TestIndexCommand:
    def test_refreshes_current_armory_material_index(
        self,
        armory: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        session = ChatSession(
            config=ChatConfig(api_key="test-key"),
            conversation=Conversation(),
            session_id="index-session",
            armory_path=armory,
        )

        result = commands.IndexCommand().handle(session, "")

        assert capsys.readouterr().out == ""
        assert result.output is not None
        assert session.rag_index is not None
        assert result.output == (
            f"Index refreshed: 3 sources, {session.rag_index.chunk_count} chunks; "
            "cache 0 reused, 3 rebuilt, 0 skipped."
        )
        assert "@python.md" not in result.output
        assert session.rag_index.chunk_count > 0
        assert (armory / ".harness" / "rag_index.json").is_file()

    def test_summarizes_reused_materials(
        self,
        armory: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        session = ChatSession(
            config=ChatConfig(api_key="test-key"),
            conversation=Conversation(),
            session_id="index-session",
            armory_path=armory,
        )
        first_result = commands.IndexCommand().handle(session, "")
        assert first_result.output is not None
        capsys.readouterr()

        result = commands.IndexCommand().handle(session, "")

        assert capsys.readouterr().out == ""
        assert result.output is not None
        assert "cache 3 reused, 0 rebuilt, 0 skipped" in result.output
        assert "\n" not in result.output
        assert "@python.md" not in result.output

    def test_dispatch_prints_summary_without_info_prefix(
        self,
        armory: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        session = ChatSession(
            config=ChatConfig(api_key="test-key"),
            conversation=Conversation(),
            session_id="index-session",
            armory_path=armory,
        )

        handle_input(session, "/index", InputHistory([]))

        out = capsys.readouterr().out
        assert "Index refreshed: 3 sources" in out
        assert "cache 0 reused, 3 rebuilt, 0 skipped" in out
        assert "info:" not in out
        assert "error:" not in out

    def test_requires_armory_for_material_index(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        session = create_plain_session(ChatConfig(api_key="test-key"))

        commands.IndexCommand().handle(session, "")

        out = capsys.readouterr().out
        assert "No armory attached" in out
        assert "Use /armory" in out

    def test_list_reports_available_armories(
        self,
        armory: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        session = create_plain_session(ChatConfig(api_key="test-key"))
        monkeypatch.setenv("HARNESS_ARMORY_HOME", str(armory.parent))

        commands.IndexCommand().handle(session, "list")

        out = capsys.readouterr().out
        assert f"Armories in {armory.parent}" in out
        assert str(armory) in out


class TestEvidenceCommand:
    def test_overview_is_compact(
        self,
        armory: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        session = ChatSession(
            config=ChatConfig(api_key="test-key"),
            conversation=Conversation(),
            session_id="evidence-session",
            armory_path=armory,
        )
        content = "Python is a high-level programming language."
        chunk = Chunk(
            text=content,
            source="materials/python.md",
            index=0,
            char_start=16,
            char_end=16 + len(content),
        )
        session.last_turn_evidence = TurnEvidence(
            items=(EvidenceChunk(evidence_id="E1", chunk=chunk, score=0.91, content=content),)
        )

        commands.EvidenceCommand().handle(session, "")

        out = capsys.readouterr().out
        assert "Last turn sources:" in out
        assert "materials/python.md" in out
        assert "E1  lines 2-3; score=0.910" in out
        assert "expand: /evidence E1" in out
        assert "open:   /evidence E1 open" in out
        assert "line" in out
        assert content not in out

    def test_detail_shows_source_text_with_relevance_score(
        self,
        armory: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        session = ChatSession(
            config=ChatConfig(api_key="test-key"),
            conversation=Conversation(),
            session_id="evidence-session",
            armory_path=armory,
        )
        content = "Python is a high-level programming language."
        chunk = Chunk(
            text=content,
            source="materials/python.md",
            index=0,
            char_start=16,
            char_end=16 + len(content),
        )
        session.last_turn_evidence = TurnEvidence(
            items=(EvidenceChunk(evidence_id="E1", chunk=chunk, score=0.91, content=content),)
        )

        commands.EvidenceCommand().handle(session, "E1")

        out = capsys.readouterr().out
        assert "Source text:" in out
        assert content in out
        assert "score=0.910" in out


class TestRemovedUsageCommand:
    def test_usage_command_is_not_exported(self) -> None:
        registry = commands.get_registry()

        assert registry.find("usage") is None
        assert not any(suggestion.name == "usage" for suggestion in registry.suggestions())
        assert not hasattr(commands, "UsageCommand")

    def test_status_outputs_session_usage(self) -> None:
        session = create_plain_session(ChatConfig(api_key="test-key"))
        session.usage.estimate_from_chars(400, 200, "gpt-5.4-mini")

        result = commands.StatusCommand().handle(session, "")

        assert result.output is not None
        assert "API calls: 1" in result.output
        assert "Tokens:    150 (prompt: 100, completion: 50)" in result.output

    def test_dispatch_reports_usage_as_unknown_command(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        session = create_plain_session(ChatConfig(api_key="test-key"))
        session.usage.estimate_from_chars(400, 200, "gpt-5.4-mini")

        handle_input(session, "/usage", InputHistory([]))

        out = capsys.readouterr().out
        assert "Unknown command: /usage" in out
        assert "Type /help for available commands." in out


class TestCompactCommandStatus:
    def test_memory_command_is_registered(self) -> None:
        registry = commands.get_registry()

        assert registry.find("memory") is not None
        assert any(suggestion.name == "memory" for suggestion in registry.suggestions())
        assert hasattr(commands, "MemoryCommand")

    def test_settings_fallback_is_single_plain_line(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        session = create_plain_session(ChatConfig(api_key="test-key"))

        result = commands.SettingsCommand().handle(session, "")

        out = capsys.readouterr().out
        assert result.output is None
        assert out.count("\n") == 1
        assert out.startswith("Settings are managed in the TUI with /settings.")
        assert "Theme:" in out
        assert "Activity trace:" in out
        assert "info:" not in out

    def test_models_no_match_is_single_plain_line(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        session = ChatSession(
            config=ChatConfig(
                api_key="test-key",
                base_url="https://api.openai.com/v1",
                model="gpt-5.4",
            ),
            conversation=Conversation(),
            session_id="models-session",
        )
        monkeypatch.setattr(
            _commands_model.ProviderConfig,
            "load",
            classmethod(lambda _cls: default_config()),
        )

        result = commands.ModelsCommand().handle(session, "does-not-exist")

        out = capsys.readouterr().out
        assert result.output is None
        assert out.count("\n") == 1
        assert out.startswith("No matching models available.")
        assert "Current model: gpt-5.4" in out
        assert "Use /login" in out

    def test_vocabulary_status_is_single_plain_line(
        self,
        armory: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        session = ChatSession(
            config=ChatConfig(api_key="test-key"),
            conversation=Conversation(),
            session_id="vocabulary-session",
            armory_path=armory,
        )

        result = commands.VocabCommand().handle(session, "status")

        out = capsys.readouterr().out
        assert result.output is None
        assert out.count("\n") == 1
        assert out.startswith("Vocabulary: Total cards")
        assert "material files:" in out
        assert "info:" not in out


class TestArmoryIndexSkips:
    def test_skips_dotfiles(self, armory: Path) -> None:
        (armory / "materials" / ".hidden.md").write_text("hidden content\n")
        index = ArmoryIndex(armory)
        index.build()
        sources = {doc.source for doc in index.documents}
        assert "materials/.hidden.md" not in sources

    def test_skips_armory_ignore_patterns(self, armory: Path) -> None:
        (armory / ".harnessignore").write_text("materials/ignored.md\nmaterials/private/\n")
        (armory / "materials" / "ignored.md").write_text("ignored content\n")
        private = armory / "materials" / "private"
        private.mkdir()
        (private / "notes.md").write_text("private content\n")

        index = ArmoryIndex(armory)
        index.build()

        sources = {doc.source for doc in index.documents}
        assert "materials/ignored.md" not in sources
        assert "materials/private/notes.md" not in sources

    def test_skips_binary(self, armory: Path) -> None:
        (armory / "materials" / "data.bin").write_bytes(b"\x00\x01\x02\x03")
        index = ArmoryIndex(armory)
        index.build()
        sources = {doc.source for doc in index.documents}
        assert "materials/data.bin" not in sources

    def test_skips_symlinked_materials(self, armory: Path, tmp_path: Path) -> None:
        outside = tmp_path / "outside-secret.md"
        outside.write_text("# Secret\n\nDo not index me.\n", encoding="utf-8")
        link = armory / "materials" / "linked.md"
        try:
            link.symlink_to(outside)
        except OSError:
            pytest.skip("symlinks are not supported on this filesystem")

        index = ArmoryIndex(armory)
        index.build()

        sources = {doc.source for doc in index.documents}
        assert "materials/linked.md" not in sources
        assert all("Do not index me" not in chunk.text for chunk in index.all_chunks)

    def test_skips_symlinked_material_directory(self, armory: Path, tmp_path: Path) -> None:
        outside_materials = tmp_path / "outside-materials"
        outside_materials.mkdir()
        (outside_materials / "secret.md").write_text("# Secret\n\nDo not index me.\n")
        materials = armory / "materials"
        for child in materials.iterdir():
            child.unlink()
        materials.rmdir()
        try:
            materials.symlink_to(outside_materials, target_is_directory=True)
        except OSError:
            pytest.skip("symlinks are not supported on this filesystem")

        index = ArmoryIndex(armory)
        index.build()

        assert index.documents == []

    @pytest.mark.skipif(
        not hasattr(os, "O_NOFOLLOW"),
        reason="O_NOFOLLOW is required to reject symlink swaps after validation",
    )
    def test_skips_material_swapped_to_symlink_after_validation(
        self,
        armory: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        target = armory / "materials" / "race.md"
        target.write_text("# Race\n\npublic content\n", encoding="utf-8")
        outside = tmp_path / "outside-secret.md"
        outside.write_text("# Secret\n\noutside secret\n", encoding="utf-8")
        original_resolve = rag_index._resolved_path_within_materials
        swapped = False

        def swap_after_validation(path: Path, armory_path: Path) -> Path | None:
            nonlocal swapped
            resolved = original_resolve(path, armory_path)
            if resolved is not None and path == target and not swapped:
                swapped = True
                target.unlink()
                target.symlink_to(outside)
            return resolved

        monkeypatch.setattr(
            rag_index,
            "_resolved_path_within_materials",
            swap_after_validation,
        )

        index = ArmoryIndex(armory)
        index.build()

        assert "materials/race.md" not in {document.source for document in index.documents}
        assert all("outside secret" not in chunk.text for chunk in index.all_chunks)

    @pytest.mark.skipif(
        not hasattr(os, "O_NOFOLLOW"),
        reason="O_NOFOLLOW is required to reject symlink swaps after validation",
    )
    def test_skips_material_parent_swapped_to_symlink_after_validation(
        self,
        armory: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        nested = armory / "materials" / "nested"
        nested.mkdir()
        target = nested / "race.md"
        target.write_text("# Race\n\npublic content\n", encoding="utf-8")
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        (outside_dir / "race.md").write_text("# Secret\n\noutside secret\n", encoding="utf-8")
        original_resolve = rag_index._resolved_path_within_materials
        swapped = False

        def swap_parent_after_validation(path: Path, armory_path: Path) -> Path | None:
            nonlocal swapped
            resolved = original_resolve(path, armory_path)
            if resolved is not None and path == target and not swapped:
                swapped = True
                target.unlink()
                nested.rmdir()
                nested.symlink_to(outside_dir, target_is_directory=True)
            return resolved

        monkeypatch.setattr(
            rag_index,
            "_resolved_path_within_materials",
            swap_parent_after_validation,
        )

        index = ArmoryIndex(armory)
        index.build()

        assert "materials/nested/race.md" not in {document.source for document in index.documents}
        assert all("outside secret" not in chunk.text for chunk in index.all_chunks)

    def test_skips_oversized_unknown_material_before_chunking(
        self,
        armory: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        target = armory / "materials" / "large.unknown"
        target.write_bytes(b"x" * 8)

        def fail_chunk_file(*_args: object, **_kwargs: object) -> ChunkedDocument | None:
            raise AssertionError("oversized material should not be chunked")

        monkeypatch.setattr(rag_index, "_MAX_MATERIAL_HASH_BYTES", 4)
        monkeypatch.setattr(rag_index, "chunk_file", fail_chunk_file)

        index = ArmoryIndex(armory)
        index.build()

        assert "materials/large.unknown" not in {document.source for document in index.documents}
        assert index.unindexable_files["materials/large.unknown"] == (
            "material exceeded size limit or could not be opened safely"
        )

    def test_handles_empty_dirs(self, tmp_path: Path) -> None:
        arm = tmp_path / "empty-armory"
        (arm / "materials").mkdir(parents=True)
        (arm / ".harness").mkdir(parents=True)

        index = ArmoryIndex(arm)
        index.build()
        assert index.chunk_count == 0


class TestArmoryIndexHeadingMetadata:
    """Verify heading/heading_level survive save → load roundtrip."""

    def test_heading_preserved_on_save_load(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        index.save()

        loaded = ArmoryIndex(armory)
        assert loaded.load()
        for chunk in loaded.all_chunks:
            # All test fixtures have headings
            assert chunk.heading != ""
            assert chunk.heading_level >= 1

    def test_strategy_preserved_on_save_load(self, armory: Path) -> None:
        index = ArmoryIndex(armory, strategy=ChunkStrategy.SEMANTIC)
        index.build()
        index.save()

        loaded = ArmoryIndex(armory)
        assert loaded.load()
        assert loaded.strategy == ChunkStrategy.SEMANTIC


class TestArmoryIndexStrategy:
    """Verify strategy parameter threads through build pipeline."""

    def test_build_with_text_strategy(self, armory: Path) -> None:
        index = ArmoryIndex(armory, strategy=ChunkStrategy.TEXT)
        index.build()
        # TEXT strategy never sets heading metadata
        for chunk in index.all_chunks:
            assert chunk.heading == ""
            assert chunk.heading_level == 0

    def test_build_index_accepts_strategy(self, armory: Path) -> None:
        index = build_index(armory, strategy=ChunkStrategy.MARKDOWN)
        # All .md files should have heading metadata
        for chunk in index.all_chunks:
            assert chunk.heading != ""

    def test_load_or_build_accepts_strategy(self, armory: Path) -> None:
        index = load_or_build(armory, strategy=ChunkStrategy.TEXT)
        assert index.chunk_count > 0
        assert index.strategy == ChunkStrategy.TEXT

    def test_load_or_build_rebuilds_when_strategy_changes(
        self,
        armory: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        build_index(armory, strategy=ChunkStrategy.MARKDOWN)
        calls: list[str] = []
        original = rag_index._chunk_file_with_timeout

        def wrapped_chunk_file(
            file_path: Path,
            armory_path: Path,
            *,
            strategy: ChunkStrategy,
            timeout_seconds: int,
        ) -> tuple[ChunkedDocument | None, bool]:
            calls.append(str(file_path.relative_to(armory_path)))
            return original(
                file_path,
                armory_path,
                strategy=strategy,
                timeout_seconds=timeout_seconds,
            )

        monkeypatch.setattr(rag_index, "_chunk_file_with_timeout", wrapped_chunk_file)

        index = load_or_build(armory, strategy=ChunkStrategy.TEXT)

        assert set(calls) == {
            "materials/python.md",
            "materials/rust.md",
            "materials/algorithms.md",
        }
        assert index.strategy == ChunkStrategy.TEXT
        assert all(chunk.heading == "" for chunk in index.all_chunks)

    def test_v1_index_still_loads(self, armory: Path) -> None:
        """A v1 index (without heading fields) should still load gracefully."""
        index = ArmoryIndex(armory)
        index.build()
        index.save()

        # Manually downgrade to v1 format (strip heading fields)
        index_path = armory / ".harness" / "rag_index.json"
        data = json.loads(index_path.read_text())
        data["version"] = 1
        for doc in data["documents"]:
            for c in doc["chunks"]:
                c.pop("heading", None)
                c.pop("heading_level", None)
        index_path.write_text(json.dumps(data))

        loaded = ArmoryIndex(armory)
        assert loaded.load()
        # Defaults should fill in
        for chunk in loaded.all_chunks:
            assert chunk.heading == ""
            assert chunk.heading_level == 0

    def test_load_normalizes_legacy_extracted_text(self, armory: Path) -> None:
        legacy_text = "Administrative Header <!-- formula-not-decoded --> <!-- image -->"
        (armory / "materials" / "python.md").write_text(legacy_text, encoding="utf-8")
        index = ArmoryIndex(armory)
        index.build()
        index.save()

        index_path = armory / ".harness" / "rag_index.json"
        data = json.loads(index_path.read_text())
        for document in data["documents"]:
            if document["source"] == "materials/python.md":
                document["chunks"][0]["text"] = legacy_text
                break
        data["documents_digest"] = "legacy-digest"
        data["version"] = 3
        index_path.write_text(json.dumps(data))

        loaded = ArmoryIndex(armory)

        assert loaded.load()
        chunk_text = next(
            chunk.text for chunk in loaded.all_chunks if chunk.source == "materials/python.md"
        )
        assert "Administrative Header" in chunk_text
        assert "formula-not-decoded" not in chunk_text
        assert "<!-- image -->" not in chunk_text
