"""Tests for the RAG chunker."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from hephaistos.rag.chunker import (
    _DOCLING_EXTENSIONS,  # type: ignore[reportPrivateUsage]
    ChunkStrategy,
    _convert_to_markdown,  # type: ignore[reportPrivateUsage]
    _is_docling_available,  # type: ignore[reportPrivateUsage]
    _is_docling_file,  # type: ignore[reportPrivateUsage]
    chunk_file,
    chunk_markdown,
    chunk_semantic,
    chunk_text,
)


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
        (armory / "materials").mkdir()
        src = armory / "materials" / "notes.md"
        src.write_text("# Notes\n\nSome study content here.\n")

        doc = chunk_file(src, armory)
        assert doc is not None
        assert doc.source == "materials/notes.md"
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


class TestChunkMarkdown:
    def test_empty_input(self) -> None:
        assert chunk_markdown("", "test.md") == []
        assert chunk_markdown("   ", "test.md") == []

    def test_single_section_no_headings(self) -> None:
        text = "Just some plain text without headings."
        chunks = chunk_markdown(text, "plain.md")
        assert len(chunks) == 1
        assert chunks[0].heading == ""
        assert chunks[0].heading_level == 0

    def test_splits_on_headings(self) -> None:
        text = (
            "# Title\n\nIntro paragraph.\n\n"
            "## Section A\n\nContent A.\n\n"
            "## Section B\n\nContent B."
        )
        chunks = chunk_markdown(text, "doc.md")
        assert len(chunks) == 3
        assert chunks[0].heading == "Title"
        assert chunks[0].heading_level == 1
        assert chunks[1].heading == "Section A"
        assert chunks[1].heading_level == 2
        assert chunks[2].heading == "Section B"
        assert chunks[2].heading_level == 2

    def test_preamble_before_first_heading(self) -> None:
        text = "Preamble text.\n\n# First Heading\n\nContent."
        chunks = chunk_markdown(text, "pre.md")
        assert len(chunks) == 2
        assert chunks[0].heading == ""
        assert chunks[0].heading_level == 0
        assert "Preamble" in chunks[0].text
        assert chunks[1].heading == "First Heading"

    def test_oversized_section_splits_at_paragraphs(self) -> None:
        # Section larger than chunk_size should split at paragraph breaks
        section_body = "\n\n".join(f"Paragraph {i}. " + "x" * 80 for i in range(20))
        text = f"# Big Section\n\n{section_body}"
        chunks = chunk_markdown(text, "big.md", chunk_size=300)
        assert len(chunks) > 1
        # All chunks should carry the parent heading
        for c in chunks:
            assert c.heading == "Big Section"
            assert c.heading_level == 1


class TestChunkSemantic:
    def test_empty_input(self) -> None:
        assert chunk_semantic("", "test.txt") == []
        assert chunk_semantic("   ", "test.txt") == []

    def test_short_text_single_chunk(self) -> None:
        # With or without sentence-transformers, a short text yields 1 chunk
        chunks = chunk_semantic("Hello world.", "short.txt")
        assert len(chunks) >= 1
        assert chunks[0].source == "short.txt"

    def test_falls_back_to_chunk_text_without_st(self) -> None:
        # chunk_semantic always works (falls back to chunk_text)
        text = "A. " * 200
        chunks = chunk_semantic(text, "fallback.txt", chunk_size=500)
        assert len(chunks) >= 1


class TestChunkStrategy:
    def test_auto_uses_markdown_for_md(self, tmp_path: Path) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        md = armory / "doc.md"
        md.write_text("# Heading\n\nContent paragraph.\n")

        doc = chunk_file(md, armory, strategy=ChunkStrategy.AUTO)
        assert doc is not None
        # chunk_markdown sets heading metadata
        assert doc.chunks[0].heading == "Heading"
        assert doc.chunks[0].heading_level == 1

    def test_auto_uses_semantic_for_txt(self, tmp_path: Path) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        txt = armory / "notes.txt"
        txt.write_text("Some plain text. More text here.")

        doc = chunk_file(txt, armory, strategy=ChunkStrategy.AUTO)
        assert doc is not None
        # Semantic or text fallback — both produce chunks
        assert len(doc.chunks) >= 1

    def test_explicit_text_strategy(self, tmp_path: Path) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        md = armory / "doc.md"
        md.write_text("# Heading\n\nContent paragraph.\n")

        # Forcing TEXT strategy on .md should NOT set heading metadata
        doc = chunk_file(md, armory, strategy=ChunkStrategy.TEXT)
        assert doc is not None
        assert doc.chunks[0].heading == ""  # chunk_text never sets headings

    def test_explicit_markdown_strategy_on_txt(self, tmp_path: Path) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        txt = armory / "notes.txt"
        txt.write_text("# Heading\n\nContent.\n")

        # Forcing MARKDOWN on .txt should still parse headings
        doc = chunk_file(txt, armory, strategy=ChunkStrategy.MARKDOWN)
        assert doc is not None
        assert doc.chunks[0].heading == "Heading"

    def test_explicit_semantic_strategy(self, tmp_path: Path) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        txt = armory / "data.txt"
        txt.write_text("First sentence. Second sentence. Third sentence.")

        doc = chunk_file(txt, armory, strategy=ChunkStrategy.SEMANTIC)
        assert doc is not None
        assert len(doc.chunks) >= 1


class TestDoclingIntegration:
    """Tests for the Docling binary-document conversion path."""

    def test_is_docling_file(self) -> None:
        assert _is_docling_file(Path("report.pdf"))
        assert _is_docling_file(Path("slides.PPTX"))
        assert _is_docling_file(Path("data.Xlsx"))
        assert not _is_docling_file(Path("notes.txt"))
        assert not _is_docling_file(Path("code.py"))
        assert not _is_docling_file(Path("image.png"))

    def test_docling_extensions_covered(self) -> None:
        assert ".pdf" in _DOCLING_EXTENSIONS
        assert ".docx" in _DOCLING_EXTENSIONS
        assert ".pptx" in _DOCLING_EXTENSIONS
        assert ".xlsx" in _DOCLING_EXTENSIONS
        assert ".odt" in _DOCLING_EXTENSIONS

    def test_is_docling_available_without_package(self) -> None:
        with (
            patch.dict("sys.modules", {"docling": None}),
            patch("builtins.__import__", side_effect=ImportError("no docling")),
        ):
            assert not _is_docling_available()

    def test_convert_to_markdown_success(self, tmp_path: Path) -> None:
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\x00fake pdf")

        mock_result = MagicMock()
        mock_result.document.export_to_markdown.return_value = (
            "# Report\n\nSome content from the PDF.\n"
        )
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result

        with patch(
            "hephaistos.rag.chunker._get_docling_converter",
            return_value=mock_converter,
        ):
            md = _convert_to_markdown(pdf)

        assert md is not None
        assert "# Report" in md

    def test_convert_to_markdown_failure_returns_none(self, tmp_path: Path) -> None:
        pdf = tmp_path / "bad.pdf"
        pdf.write_bytes(b"%PDF\x00corrupt")

        mock_converter = MagicMock()
        mock_converter.convert.side_effect = RuntimeError("conversion failed")

        with patch(
            "hephaistos.rag.chunker._get_docling_converter",
            return_value=mock_converter,
        ):
            md = _convert_to_markdown(pdf)

        assert md is None

    def test_chunk_docling_file_via_chunk_file(self, tmp_path: Path) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        src = armory / "materials"
        src.mkdir()
        pdf = src / "report.pdf"
        pdf.write_bytes(b"%PDF-1.4\x00binary content")

        mock_result = MagicMock()
        mock_result.document.export_to_markdown.return_value = (
            "# Chapter 1\n\nContent from PDF.\n\n## Section\n\nMore details."
        )
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result

        with (
            patch(
                "hephaistos.rag.chunker._is_docling_available",
                return_value=True,
            ),
            patch(
                "hephaistos.rag.chunker._get_docling_converter",
                return_value=mock_converter,
            ),
        ):
            doc = chunk_file(pdf, armory)

        assert doc is not None
        assert doc.source == "materials/report.pdf"
        assert len(doc.chunks) >= 1
        assert doc.content_hash != ""
        # Markdown heading chunking should have run
        assert any(c.heading for c in doc.chunks)

    def test_chunk_file_skips_pdf_without_docling(self, tmp_path: Path) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        pdf = armory / "doc.pdf"
        pdf.write_bytes(b"%PDF-1.4\x00binary")

        with patch(
            "hephaistos.rag.chunker._is_docling_available",
            return_value=False,
        ):
            doc = chunk_file(pdf, armory)

        assert doc is None

    def test_chunk_docling_empty_conversion_returns_none(self, tmp_path: Path) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        pdf = armory / "blank.pdf"
        pdf.write_bytes(b"%PDF\x00fake")

        mock_result = MagicMock()
        mock_result.document.export_to_markdown.return_value = "   \n  \n"
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result

        with (
            patch(
                "hephaistos.rag.chunker._is_docling_available",
                return_value=True,
            ),
            patch(
                "hephaistos.rag.chunker._get_docling_converter",
                return_value=mock_converter,
            ),
        ):
            doc = chunk_file(pdf, armory)

        assert doc is None
