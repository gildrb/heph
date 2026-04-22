"""Tests for the RAG index."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hephaistos.harness.rag.chunker import ChunkStrategy
from hephaistos.harness.rag.index import ArmoryIndex, build_index, load_or_build


@pytest.fixture
def armory(tmp_path: Path) -> Path:
    """Create a minimal armory with source files."""
    arm = tmp_path / "test-armory"
    (arm / "source").mkdir(parents=True)
    (arm / "library").mkdir(parents=True)
    (arm / ".hephaistos").mkdir(parents=True)

    (arm / "source" / "python.md").write_text(
        "# Python Basics\n\n"
        "Python is a high-level programming language.\n\n"
        "Variables are dynamically typed.\n\n"
        "Functions use the `def` keyword.\n"
    )
    (arm / "source" / "rust.md").write_text(
        "# Rust Basics\n\n"
        "Rust is a systems programming language.\n\n"
        "Ownership and borrowing are core concepts.\n\n"
        "Cargo is the build tool.\n"
    )
    (arm / "library" / "algorithms.md").write_text(
        "# Algorithms\n\n"
        "Binary search runs in O(log n) time.\n\n"
        "Quick sort has average O(n log n) complexity.\n\n"
        "Merge sort is stable and runs in O(n log n).\n"
    )
    return arm


class TestArmoryIndexBuild:
    def test_build_finds_files(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        sources = {doc.source for doc in index.documents}
        assert "source/python.md" in sources
        assert "source/rust.md" in sources
        assert "library/algorithms.md" in sources

    def test_build_creates_chunks(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        assert index.chunk_count > 0

    def test_all_chunks_have_source(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        for chunk in index.all_chunks:
            assert chunk.source in ("source/python.md", "source/rust.md", "library/algorithms.md")


class TestArmoryIndexPersist:
    def test_save_creates_file(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        path = index.save()
        assert path.exists()
        assert path.name == "rag_index.json"

    def test_save_load_roundtrip(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        index.save()

        loaded = ArmoryIndex(armory)
        assert loaded.load()
        assert len(loaded.documents) == len(index.documents)
        assert loaded.chunk_count == index.chunk_count

    def test_load_missing_returns_false(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        assert not index.load()

    def test_load_corrupt_returns_false(self, armory: Path) -> None:
        index_file = armory / ".hephaistos" / "rag_index.json"
        index_file.parent.mkdir(parents=True, exist_ok=True)
        index_file.write_text("not valid json{{{")

        index = ArmoryIndex(armory)
        assert not index.load()


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

        (armory / "source" / "new.md").write_text("# New content\n")
        assert index.is_stale()

    def test_edited_file_makes_stale(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        assert not index.is_stale()

        (armory / "source" / "python.md").write_text("# Changed content\n")
        assert index.is_stale()

    def test_unsupported_file_does_not_make_fresh_index_stale(self, armory: Path) -> None:
        (armory / "source" / "data.bin").write_bytes(b"\x00\x01\x02\x03")

        index = ArmoryIndex(armory)
        index.build()

        assert not index.is_stale()

        index.save()
        loaded = ArmoryIndex(armory)
        assert loaded.load()
        assert not loaded.is_stale()


class TestBuildIndex:
    def test_build_index_returns_index(self, armory: Path) -> None:
        index = build_index(armory)
        assert isinstance(index, ArmoryIndex)
        assert index.chunk_count > 0

    def test_build_index_persists(self, armory: Path) -> None:
        build_index(armory)
        assert (armory / ".hephaistos" / "rag_index.json").exists()


class TestLoadOrBuild:
    def test_loads_existing_fresh(self, armory: Path) -> None:
        build_index(armory)
        index = load_or_build(armory)
        assert index.chunk_count > 0

    def test_rebuilds_when_stale(self, armory: Path) -> None:
        build_index(armory)
        (armory / "source" / "extra.md").write_text("# Extra\n")
        index = load_or_build(armory)
        sources = {doc.source for doc in index.documents}
        assert "source/extra.md" in sources

    def test_builds_when_no_index(self, armory: Path) -> None:
        index = load_or_build(armory)
        assert index.chunk_count > 0


class TestArmoryIndexSkips:
    def test_skips_dotfiles(self, armory: Path) -> None:
        (armory / "source" / ".hidden.md").write_text("hidden content\n")
        index = ArmoryIndex(armory)
        index.build()
        sources = {doc.source for doc in index.documents}
        assert "source/.hidden.md" not in sources

    def test_skips_binary(self, armory: Path) -> None:
        (armory / "source" / "data.bin").write_bytes(b"\x00\x01\x02\x03")
        index = ArmoryIndex(armory)
        index.build()
        sources = {doc.source for doc in index.documents}
        assert "source/data.bin" not in sources

    def test_handles_empty_dirs(self, tmp_path: Path) -> None:
        arm = tmp_path / "empty-armory"
        (arm / "source").mkdir(parents=True)
        (arm / ".hephaistos").mkdir(parents=True)

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

    def test_v1_index_still_loads(self, armory: Path) -> None:
        """A v1 index (without heading fields) should still load gracefully."""
        index = ArmoryIndex(armory)
        index.build()
        index.save()

        # Manually downgrade to v1 format (strip heading fields)
        index_path = armory / ".hephaistos" / "rag_index.json"
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
