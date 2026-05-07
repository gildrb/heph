"""Tests for the RAG index."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from hephaistos.rag.chunker import Chunk, ChunkedDocument, ChunkStrategy
from hephaistos.rag.index import ArmoryIndex, build_index, load_or_build, scan_unindexable_files


@pytest.fixture
def armory(tmp_path: Path) -> Path:
    """Create a minimal armory with material files."""
    arm = tmp_path / "test-armory"
    (arm / "materials").mkdir(parents=True)
    (arm / ".hephaistos").mkdir(parents=True)

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

        (armory / "materials" / "new.md").write_text("# New content\n")
        assert index.is_stale()

    def test_edited_file_makes_stale(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        assert not index.is_stale()

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
        monkeypatch.setattr("hephaistos.rag.index._is_docling_available", lambda: False)
        (armory / "materials" / "doc.pdf").write_bytes(b"%PDF-1.4\x00fake pdf")

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
        (armory / "materials" / "extra.md").write_text("# Extra\n")
        index = load_or_build(armory)
        sources = {doc.source for doc in index.documents}
        assert "materials/extra.md" in sources

    def test_builds_when_no_index(self, armory: Path) -> None:
        index = load_or_build(armory)
        assert index.chunk_count > 0

    def test_rebuilds_poisoned_cached_chunks(self, armory: Path) -> None:
        build_index(armory)
        index_path = armory / ".hephaistos" / "rag_index.json"
        data = json.loads(index_path.read_text())
        data["documents"][0]["chunks"][0]["text"] = "hidden poisoned evidence"
        index_path.write_text(json.dumps(data), encoding="utf-8")

        index = load_or_build(armory)

        assert "hidden poisoned evidence" not in {chunk.text for chunk in index.all_chunks}

    def test_rebuilds_failed_pdf_index_when_conversion_unavailable(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("hephaistos.rag.index._is_docling_available", lambda: False)
        monkeypatch.setattr("hephaistos.rag.index.chunk_file", lambda *_args, **_kwargs: None)
        arm = tmp_path / "armory"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaistos").mkdir(parents=True)
        pdf = arm / "materials" / "theorem.pdf"
        pdf.write_bytes(b"%PDF-1.4\x00fake theorem")
        content_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()[:16]
        (arm / ".hephaistos" / "rag_index.json").write_text(
            json.dumps(
                {
                    "version": 4,
                    "chunk_size": 500,
                    "overlap": 100,
                    "strategy": "auto",
                    "file_hashes": {"materials/theorem.pdf": content_hash},
                    "documents": [],
                }
            ),
            encoding="utf-8",
        )

        index = load_or_build(arm)

        assert index.chunk_count == 0
        assert "materials/theorem.pdf" in index.unindexable_files
        assert "conversion backend unavailable" in index.unindexable_files["materials/theorem.pdf"]

    def test_loads_converted_pdf_index_when_conversion_becomes_unavailable(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("hephaistos.rag.index._is_docling_available", lambda: False)
        monkeypatch.setattr("hephaistos.rag.index.chunk_file", lambda *_args, **_kwargs: None)
        arm = tmp_path / "armory"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaistos").mkdir(parents=True)
        pdf = arm / "materials" / "theorem.pdf"
        pdf.write_bytes(b"%PDF-1.4\x00fake theorem")
        content_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()[:16]
        (arm / ".hephaistos" / "rag_index.json").write_text(
            json.dumps(
                {
                    "version": 4,
                    "chunk_size": 500,
                    "overlap": 100,
                    "strategy": "auto",
                    "file_hashes": {"materials/theorem.pdf": content_hash},
                    "documents": [
                        {
                            "source": "materials/theorem.pdf",
                            "content_hash": content_hash,
                            "chunks": [
                                {
                                    "text": "Already converted theorem text.",
                                    "source": "materials/theorem.pdf",
                                    "index": 0,
                                    "char_start": 0,
                                    "char_end": 31,
                                    "heading": "Theorem",
                                    "heading_level": 1,
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        index = load_or_build(arm)

        assert index.chunk_count == 1
        assert index.unindexable_files == {}
        assert index.all_chunks[0].text == "Already converted theorem text."

    def test_loads_converted_pdf_index_when_conversion_temporarily_fails(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("hephaistos.rag.index._is_docling_available", lambda: True)
        monkeypatch.setattr("hephaistos.rag.index.chunk_file", lambda *_args, **_kwargs: None)
        arm = tmp_path / "armory"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaistos").mkdir(parents=True)
        pdf = arm / "materials" / "theorem.pdf"
        pdf.write_bytes(b"%PDF-1.4\x00fake theorem")
        content_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()[:16]
        (arm / ".hephaistos" / "rag_index.json").write_text(
            json.dumps(
                {
                    "version": 4,
                    "chunk_size": 500,
                    "overlap": 100,
                    "strategy": "auto",
                    "file_hashes": {"materials/theorem.pdf": content_hash},
                    "documents": [
                        {
                            "source": "materials/theorem.pdf",
                            "content_hash": content_hash,
                            "chunks": [
                                {
                                    "text": "Previously converted theorem text.",
                                    "source": "materials/theorem.pdf",
                                    "index": 0,
                                    "char_start": 0,
                                    "char_end": 34,
                                    "heading": "Theorem",
                                    "heading_level": 1,
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        index = load_or_build(arm)

        assert index.chunk_count == 1
        assert index.unindexable_files == {}
        assert index.all_chunks[0].text == "Previously converted theorem text."

    def test_build_index_preserves_converted_pdf_when_conversion_unavailable(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("hephaistos.rag.index._is_docling_available", lambda: False)
        monkeypatch.setattr("hephaistos.rag.index.chunk_file", lambda *_args, **_kwargs: None)
        arm = tmp_path / "armory"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaistos").mkdir(parents=True)
        pdf = arm / "materials" / "theorem.pdf"
        pdf.write_bytes(b"%PDF-1.4\x00fake theorem")
        content_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()[:16]
        (arm / ".hephaistos" / "rag_index.json").write_text(
            json.dumps(
                {
                    "version": 4,
                    "chunk_size": 500,
                    "overlap": 100,
                    "strategy": "auto",
                    "file_hashes": {"materials/theorem.pdf": content_hash},
                    "documents": [
                        {
                            "source": "materials/theorem.pdf",
                            "content_hash": content_hash,
                            "chunks": [
                                {
                                    "text": "Persisted converted content.",
                                    "source": "materials/theorem.pdf",
                                    "index": 0,
                                    "char_start": 0,
                                    "char_end": 28,
                                    "heading": "Theorem",
                                    "heading_level": 1,
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        index = build_index(arm)

        assert index.chunk_count == 1
        assert index.unindexable_files == {}
        assert index.all_chunks[0].text == "Persisted converted content."

    def test_changed_pdf_is_stale_even_when_conversion_unavailable(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("hephaistos.rag.index._is_docling_available", lambda: False)
        arm = tmp_path / "armory"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaistos").mkdir(parents=True)
        pdf = arm / "materials" / "theorem.pdf"
        pdf.write_bytes(b"%PDF-1.4\x00old theorem")
        content_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()[:16]
        (arm / ".hephaistos" / "rag_index.json").write_text(
            json.dumps(
                {
                    "version": 4,
                    "chunk_size": 500,
                    "overlap": 100,
                    "strategy": "auto",
                    "file_hashes": {"materials/theorem.pdf": content_hash},
                    "documents": [
                        {
                            "source": "materials/theorem.pdf",
                            "content_hash": content_hash,
                            "chunks": [
                                {
                                    "text": "Old converted content.",
                                    "source": "materials/theorem.pdf",
                                    "index": 0,
                                    "char_start": 0,
                                    "char_end": 22,
                                    "heading": "Theorem",
                                    "heading_level": 1,
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        index = ArmoryIndex(arm)
        assert index.load()

        pdf.write_bytes(b"%PDF-1.4\x00new theorem")

        assert index.is_stale()

    def test_rebuilds_failed_pdf_index_when_conversion_becomes_available(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("hephaistos.rag.index._is_docling_available", lambda: True)
        arm = tmp_path / "armory"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaistos").mkdir(parents=True)
        pdf = arm / "materials" / "theorem.pdf"
        pdf.write_bytes(b"%PDF-1.4\x00fake theorem")
        content_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()[:16]
        (arm / ".hephaistos" / "rag_index.json").write_text(
            json.dumps(
                {
                    "version": 4,
                    "chunk_size": 500,
                    "overlap": 100,
                    "strategy": "auto",
                    "file_hashes": {"materials/theorem.pdf": content_hash},
                    "documents": [],
                }
            ),
            encoding="utf-8",
        )

        def fake_chunk_file(
            file_path: Path,
            armory_path: Path,
            _chunk_size: int,
            _overlap: int,
            *,
            strategy: ChunkStrategy,
        ) -> ChunkedDocument | None:
            rel = str(file_path.relative_to(armory_path))
            return ChunkedDocument(
                source=rel,
                content_hash=content_hash,
                chunks=[
                    Chunk(
                        text="The fundamentalsatz says prime factorization is unique.",
                        source=rel,
                        index=0,
                        char_start=0,
                        char_end=58,
                        heading="Fundamentalsatz",
                        heading_level=1,
                    )
                ],
            )

        monkeypatch.setattr("hephaistos.rag.index.chunk_file", fake_chunk_file)

        index = load_or_build(arm)

        assert index.chunk_count == 1
        assert index.unindexable_files == {}
        assert "prime factorization is unique" in index.all_chunks[0].text


class TestArmoryIndexSkips:
    def test_skips_dotfiles(self, armory: Path) -> None:
        (armory / "materials" / ".hidden.md").write_text("hidden content\n")
        index = ArmoryIndex(armory)
        index.build()
        sources = {doc.source for doc in index.documents}
        assert "materials/.hidden.md" not in sources

    def test_skips_armory_ignore_patterns(self, armory: Path) -> None:
        (armory / ".hephaistosignore").write_text("materials/ignored.md\nmaterials/private/\n")
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

    def test_handles_empty_dirs(self, tmp_path: Path) -> None:
        arm = tmp_path / "empty-armory"
        (arm / "materials").mkdir(parents=True)
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


class TestArmoryIndexUnindexable:
    """Verify that unindexable (binary) files are tracked."""

    def test_pdf_without_conversion_backend_tracked_as_unindexable(
        self,
        armory: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("hephaistos.rag.index._is_docling_available", lambda: False)
        (armory / "materials" / "doc.pdf").write_bytes(b"%PDF-1.4\x00fake pdf")
        index = ArmoryIndex(armory)
        index.build()
        assert "materials/doc.pdf" in index.unindexable_files
        assert "conversion backend unavailable" in index.unindexable_files["materials/doc.pdf"]

    def test_text_files_not_in_unindexable(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        index.build()
        assert index.unindexable_files == {}

    def test_unindexable_repopulated_on_load(
        self,
        armory: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("hephaistos.rag.index._is_docling_available", lambda: False)
        (armory / "materials" / "doc.pdf").write_bytes(b"%PDF-1.4\x00fake pdf")
        index = ArmoryIndex(armory)
        index.build()
        index.save()

        loaded = ArmoryIndex(armory)
        assert loaded.load()
        assert "materials/doc.pdf" in loaded.unindexable_files


class TestScanUnindexableFiles:
    """Test the lightweight scan_unindexable_files helper."""

    def test_detects_pdf_without_full_index(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("hephaistos.rag.index._is_docling_available", lambda: False)
        arm = tmp_path / "armory"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaistos").mkdir(parents=True)
        (arm / "materials" / "notes.md").write_text("# Notes")
        (arm / "materials" / "slides.pdf").write_bytes(b"%PDF-1.4\x00fake")

        result = scan_unindexable_files(arm)
        assert "materials/slides.pdf" in result
        assert "materials/notes.md" not in result

    def test_skips_docling_documents_when_conversion_backend_available(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("hephaistos.rag.index._is_docling_available", lambda: True)
        arm = tmp_path / "armory"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaistos").mkdir(parents=True)
        (arm / "materials" / "slides.pdf").write_bytes(b"%PDF-1.4\x00fake")

        assert scan_unindexable_files(arm) == {}

    def test_returns_empty_when_all_text(self, tmp_path: Path) -> None:
        arm = tmp_path / "armory"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaistos").mkdir(parents=True)
        (arm / "materials" / "notes.md").write_text("# Notes")

        assert scan_unindexable_files(arm) == {}

    def test_returns_empty_when_no_materials_dir(self, tmp_path: Path) -> None:
        arm = tmp_path / "armory"
        (arm / ".hephaistos").mkdir(parents=True)

        assert scan_unindexable_files(arm) == {}
