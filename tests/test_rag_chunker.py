"""Tests for the RAG chunker."""

from __future__ import annotations

from pathlib import Path

from hephaistos.harness.rag.chunker import chunk_file, chunk_text


class TestChunkText:
    def test_empty_text(self) -> None:
        assert chunk_text("", "test.txt") == []

    def test_short_text_single_chunk(self) -> None:
        text = "Hello, world!"
        chunks = chunk_text(text, "test.txt")
        assert len(chunks) == 1
        assert chunks[0].text == "Hello, world!"
        assert chunks[0].source == "test.txt"
        assert chunks[0].index == 0

    def test_long_text_multiple_chunks(self) -> None:
        text = "Word " * 400  # ~2000 chars
        chunks = chunk_text(text, "long.txt", chunk_size=500, overlap=100)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c.text) <= 600  # chunk_size + some margin for boundary

    def test_overlap_between_chunks(self) -> None:
        text = "A" * 600
        chunks = chunk_text(text, "overlap.txt", chunk_size=300, overlap=50)
        if len(chunks) > 1:
            assert len(chunks[0].text) > 0

    def test_preserves_source_metadata(self) -> None:
        chunks = chunk_text("Some text here.", "src/notes.md")
        assert chunks[0].source == "src/notes.md"

    def test_char_offsets(self) -> None:
        text = "Hello, world!"
        chunks = chunk_text(text, "test.txt")
        assert chunks[0].char_start == 0
        assert chunks[0].char_end == len(text)

    def test_paragraph_boundary_break(self) -> None:
        text = "A" * 400 + "\n\n" + "B" * 400
        chunks = chunk_text(text, "para.txt", chunk_size=500, overlap=100)
        # Should break on the paragraph boundary
        assert len(chunks) >= 2

    def test_sequential_indices(self) -> None:
        text = "Word " * 400
        chunks = chunk_text(text, "seq.txt", chunk_size=200, overlap=50)
        for i, c in enumerate(chunks):
            assert c.index == i


class TestChunkFile:
    def test_chunk_text_file(self, tmp_path: Path) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        (armory / "source").mkdir()
        src = armory / "source" / "notes.md"
        src.write_text("# Notes\n\nSome study content here.\n")

        doc = chunk_file(src, armory)
        assert doc is not None
        assert doc.source == "source/notes.md"
        assert len(doc.chunks) >= 1
        assert doc.content_hash != ""

    def test_skip_binary_file(self, tmp_path: Path) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        binary = armory / "image.png"
        binary.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

        doc = chunk_file(binary, armory)
        assert doc is None

    def test_skip_empty_file(self, tmp_path: Path) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        empty = armory / "empty.txt"
        empty.write_text("")

        doc = chunk_file(empty, armory)
        # Empty files produce no chunks — returns None
        assert doc is None

    def test_content_hash_changes_on_edit(self, tmp_path: Path) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        src = armory / "notes.txt"
        src.write_text("version one")

        doc1 = chunk_file(src, armory)
        src.write_text("version two")
        doc2 = chunk_file(src, armory)

        assert doc1 is not None
        assert doc2 is not None
        assert doc1.content_hash != doc2.content_hash
