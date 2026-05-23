"""Tests for the RAG index."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import time
from pathlib import Path

import pytest

from hephaistos.rag import index as rag_index
from hephaistos.rag.chunker import Chunk, ChunkedDocument, ChunkStrategy
from hephaistos.rag.index import (
    ArmoryIndex,
    _documents_digest,
    build_index,
    load_or_build,
    scan_unindexable_files,
)


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
    monkeypatch.setenv("HEPHAISTOS_RAG_CACHE_KEY_FILE", str(key_path))

    key = rag_index._cache_signing_key()

    assert key is not None
    assert stat.S_IMODE(key_path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(key_path.stat().st_mode) == 0o600


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

    def test_build_marks_slow_binary_conversion_unindexable(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        arm = tmp_path / "armory"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaistos").mkdir()
        pdf = arm / "materials" / "slow.pdf"
        pdf.write_bytes(b"%PDF-1.4\n\x00")

        def slow_chunk_file(*_args: object, **_kwargs: object) -> ChunkedDocument | None:
            try:
                time.sleep(3)
            except Exception:
                return None
            return None

        monkeypatch.setenv("HEPHAISTOS_INDEX_FILE_TIMEOUT_SECONDS", "1")
        monkeypatch.setattr("hephaistos.rag.index._is_docling_available", lambda: True)
        monkeypatch.setattr("hephaistos.rag.index.chunk_file", slow_chunk_file)
        index = ArmoryIndex(arm)

        index.build()

        assert index.chunk_count == 0
        assert index.unindexable_files == {
            "materials/slow.pdf": "document conversion timed out after 1 second(s)"
        }

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

        monkeypatch.setattr("hephaistos.rag.index.chunk_file", fail_chunk_file)

        loaded = ArmoryIndex(armory)
        assert loaded.load()
        assert loaded.chunk_count == index.chunk_count

    def test_load_embeddings_treats_malformed_numeric_values_as_cache_miss(
        self,
        armory: Path,
    ) -> None:
        index = ArmoryIndex(armory)
        index.build()
        embed_path = index.save_embeddings([[1.0]], "test-model")
        assert embed_path is not None
        data = json.loads(embed_path.read_text(encoding="utf-8"))
        data["embeddings"] = [["not-a-float"]]
        embed_path.write_text(json.dumps(data), encoding="utf-8")

        assert index.load_embeddings("test-model") is None

    def test_load_missing_returns_false(self, armory: Path) -> None:
        index = ArmoryIndex(armory)
        assert not index.load()

    def test_load_corrupt_returns_false(self, armory: Path) -> None:
        index_file = armory / ".hephaistos" / "rag_index.json"
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
            "HEPHAISTOS_RAG_CACHE_KEY_FILE",
            str(tmp_path / "config" / "rag_cache.key"),
        )
        monkeypatch.setenv("HEPHAISTOS_INDEX_VERIFY_DOCUMENT_DIGEST_LIMIT", "0")
        index = ArmoryIndex(armory)
        index.build()
        index.save()
        index_file = armory / ".hephaistos" / "rag_index.json"
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
        monkeypatch.setenv("HEPHAISTOS_INDEX_VERIFY_DOCUMENT_DIGEST_LIMIT", "0")

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
        monkeypatch.setattr("hephaistos.rag.index._can_convert_binary_file", lambda _path: False)
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
        monkeypatch.setattr("hephaistos.rag.index._can_convert_binary_file", lambda _path: False)

        index = ArmoryIndex(armory)
        index.build()
        assert not index.is_stale()

        monkeypatch.setattr("hephaistos.rag.index._can_convert_binary_file", lambda _path: True)

        assert index.is_stale()


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

    def test_incremental_rebuild_only_rechunks_edited_file(
        self,
        armory: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        build_index(armory)
        (armory / "materials" / "python.md").write_text(
            "# Python Changed\n\nNew Python details.\n"
        )
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

        index = load_or_build(armory)

        assert calls == ["materials/python.md"]
        sources = {doc.source for doc in index.documents}
        assert sources == {
            "materials/python.md",
            "materials/rust.md",
            "materials/algorithms.md",
        }

    def test_incremental_rebuild_reuses_existing_documents_when_file_added(
        self,
        armory: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        build_index(armory)
        (armory / "materials" / "extra.md").write_text("# Extra\n\nAdditional material.\n")
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

        index = load_or_build(armory)

        assert calls == ["materials/extra.md"]
        sources = {doc.source for doc in index.documents}
        assert "materials/extra.md" in sources
        assert "materials/python.md" in sources

    def test_incremental_rebuild_removes_deleted_file(
        self,
        armory: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        build_index(armory)
        (armory / "materials" / "rust.md").unlink()
        calls: list[str] = []

        def fail_chunk_file(*_args: object, **_kwargs: object) -> tuple[None, bool]:
            calls.append("unexpected")
            return None, False

        monkeypatch.setattr(rag_index, "_chunk_file_with_timeout", fail_chunk_file)

        index = load_or_build(armory)

        assert calls == []
        sources = {doc.source for doc in index.documents}
        assert "materials/rust.md" not in sources
        assert sources == {"materials/python.md", "materials/algorithms.md"}

    def test_builds_when_no_index(self, armory: Path) -> None:
        index = load_or_build(armory)
        assert index.chunk_count > 0

    def test_rebuilds_poisoned_cached_chunks(self, armory: Path) -> None:
        build_index(armory)
        index_path = armory / ".hephaistos" / "rag_index.json"
        data = json.loads(index_path.read_text())
        data["documents"][0]["chunks"][0]["text"] = "hidden poisoned evidence"
        data["documents_digest"] = _documents_digest(data["documents"])
        index_path.write_text(json.dumps(data), encoding="utf-8")

        index = load_or_build(armory)

        assert "hidden poisoned evidence" not in {chunk.text for chunk in index.all_chunks}

    def test_rebuilds_failed_pdf_index_when_conversion_unavailable(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("hephaistos.rag.index._can_convert_binary_file", lambda _path: False)
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
                    "version": 6,
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
        monkeypatch.setattr("hephaistos.rag.index._can_convert_binary_file", lambda _path: False)
        monkeypatch.setattr("hephaistos.rag.index.chunk_file", lambda *_args, **_kwargs: None)
        arm = tmp_path / "armory"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaistos").mkdir(parents=True)
        pdf = arm / "materials" / "theorem.pdf"
        pdf.write_bytes(b"%PDF-1.4\x00fake theorem")
        content_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()[:16]
        _save_cached_index(
            arm,
            documents=[
                _converted_document(
                    "materials/theorem.pdf",
                    content_hash,
                    "Already converted theorem text.",
                )
            ],
            file_hashes={"materials/theorem.pdf": content_hash},
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
        _save_cached_index(
            arm,
            documents=[
                _converted_document(
                    "materials/theorem.pdf",
                    content_hash,
                    "Previously converted theorem text.",
                )
            ],
            file_hashes={"materials/theorem.pdf": content_hash},
        )

        index = load_or_build(arm)

        assert index.chunk_count == 1
        assert index.unindexable_files == {}
        assert index.all_chunks[0].text == "Previously converted theorem text."

    def test_rejects_unsigned_converted_pdf_cache(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("hephaistos.rag.index._can_convert_binary_file", lambda _path: False)
        arm = tmp_path / "armory"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaistos").mkdir(parents=True)
        pdf = arm / "materials" / "theorem.pdf"
        pdf.write_bytes(b"%PDF-1.4\x00fake theorem")
        content_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()[:16]
        documents = [
            {
                "source": "materials/theorem.pdf",
                "content_hash": content_hash,
                "chunks": [
                    {
                        "text": "Forged converted theorem text.",
                        "source": "materials/theorem.pdf",
                        "index": 0,
                        "char_start": 0,
                        "char_end": 30,
                        "heading": "Theorem",
                        "heading_level": 1,
                    }
                ],
            }
        ]
        (arm / ".hephaistos" / "rag_index.json").write_text(
            json.dumps(
                {
                    "version": 6,
                    "chunk_size": 500,
                    "overlap": 100,
                    "strategy": "auto",
                    "file_hashes": {"materials/theorem.pdf": content_hash},
                    "documents_digest": _documents_digest(documents),
                    "documents": documents,
                }
            ),
            encoding="utf-8",
        )

        index = ArmoryIndex(arm)

        assert not index.load()

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
        _save_cached_index(
            arm,
            documents=[
                _converted_document(
                    "materials/theorem.pdf",
                    content_hash,
                    "Persisted converted content.",
                )
            ],
            file_hashes={"materials/theorem.pdf": content_hash},
        )

        index = build_index(arm)

        assert index.chunk_count == 1
        assert index.unindexable_files == {}
        assert index.all_chunks[0].text == "Persisted converted content."

    def test_build_index_preserves_converted_pdf_when_conversion_temporarily_fails(
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
        _save_cached_index(
            arm,
            documents=[
                _converted_document(
                    "materials/theorem.pdf",
                    content_hash,
                    "Persisted converted content.",
                )
            ],
            file_hashes={"materials/theorem.pdf": content_hash},
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
        _save_cached_index(
            arm,
            documents=[
                _converted_document(
                    "materials/theorem.pdf",
                    content_hash,
                    "Old converted content.",
                )
            ],
            file_hashes={"materials/theorem.pdf": content_hash},
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
                    "version": 6,
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

    def test_load_normalizes_legacy_extracted_text(self, armory: Path) -> None:
        legacy_text = "Administrative Header <!-- formula-not-decoded --> <!-- image -->"
        (armory / "materials" / "python.md").write_text(legacy_text, encoding="utf-8")
        index = ArmoryIndex(armory)
        index.build()
        index.save()

        index_path = armory / ".hephaistos" / "rag_index.json"
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


class TestArmoryIndexUnindexable:
    """Verify that unindexable (binary) files are tracked."""

    def test_pdf_without_conversion_backend_tracked_as_unindexable(
        self,
        armory: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("hephaistos.rag.index._can_convert_binary_file", lambda _path: False)
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
        monkeypatch.setattr("hephaistos.rag.index._can_convert_binary_file", lambda _path: False)
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
        monkeypatch.setattr("hephaistos.rag.index._can_convert_binary_file", lambda _path: True)
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

    def test_skips_symlinked_unindexable_materials(self, tmp_path: Path) -> None:
        arm = tmp_path / "armory"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaistos").mkdir(parents=True)
        outside = tmp_path / "secret.pdf"
        outside.write_bytes(b"%PDF-1.4\x00outside")
        link = arm / "materials" / "linked.pdf"
        try:
            link.symlink_to(outside)
        except OSError:
            pytest.skip("symlinks are not supported on this filesystem")

        assert scan_unindexable_files(arm) == {}

    def test_respects_armory_ignore_patterns(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("hephaistos.rag.index._can_convert_binary_file", lambda _path: False)
        arm = tmp_path / "armory"
        (arm / "materials" / "private").mkdir(parents=True)
        (arm / ".hephaistos").mkdir(parents=True)
        (arm / ".hephaistosignore").write_text("materials/private/\n", encoding="utf-8")
        (arm / "materials" / "private" / "secret.pdf").write_bytes(b"%PDF-1.4\x00secret")
        (arm / "materials" / "public.pdf").write_bytes(b"%PDF-1.4\x00public")

        result = scan_unindexable_files(arm)

        assert "materials/private/secret.pdf" not in result
        assert "materials/public.pdf" in result

    def test_returns_empty_when_no_materials_dir(self, tmp_path: Path) -> None:
        arm = tmp_path / "armory"
        (arm / ".hephaistos").mkdir(parents=True)

        assert scan_unindexable_files(arm) == {}
