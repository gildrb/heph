"""Tests for the RAG chunker."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from harness.rag import chunker as rag_chunker
from harness.rag.chunker import (
    _DOCLING_EXTENSIONS,
    ChunkStrategy,
    _convert_pdf_to_text,
    _convert_pdf_with_ocr,
    _convert_to_markdown,
    _is_docling_available,
    _is_docling_file,
    _is_text_file,
    _normalize_extracted_text,
    chunk_file,
    chunk_markdown,
    chunk_semantic,
    chunk_text,
)


def _docling_completed(
    stdout: str = "",
    *,
    returncode: int = 0,
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["docling-worker"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
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
        src.write_text("# Notes\n\nSome source content here.\n")

        doc = chunk_file(src, armory)
        assert doc is not None
        assert doc.source == "materials/notes.md"
        assert len(doc.chunks) >= 1
        assert doc.content_hash != ""

    def test_chunk_text_file_skips_oversized_text(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        src = armory / "notes.txt"
        src.write_text("oversized")
        monkeypatch.setattr("harness.rag.chunker._MAX_INDEXABLE_TEXT_BYTES", 2)

        doc = chunk_file(src, armory)

        assert doc is None

    def test_unknown_extension_probe_does_not_read_entire_file(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        src = armory / "notes.unknown"
        src.write_text("# Notes\n\npublic material", encoding="utf-8")

        def fail_read_bytes(_path: Path) -> bytes:
            raise AssertionError("read_bytes should not be used for type probing")

        monkeypatch.setattr(Path, "read_bytes", fail_read_bytes)

        doc = chunk_file(src, armory)

        assert doc is not None
        assert doc.chunks

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
        # Empty files produce no chunks - returns None
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

    def test_chunk_html_file_extracts_readable_body_text(self, tmp_path: Path) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        src = armory / "syllabus.html"
        src.write_text(
            """
            <!doctype html>
            <html>
              <head><title>Noise</title><script>window.tracker = true;</script></head>
              <body>
                <h1>Course Syllabus</h1>
                <p>Prerequisites include calculus and linear algebra.</p>
                <style>.hidden { display: none; }</style>
              </body>
            </html>
            """,
            encoding="utf-8",
        )

        doc = chunk_file(src, armory)

        assert doc is not None
        combined = "\n".join(chunk.text for chunk in doc.chunks)
        assert "Course Syllabus" in combined
        assert "Prerequisites include calculus and linear algebra." in combined
        assert "<html" not in combined
        assert "window.tracker" not in combined

    def test_skips_symlinked_file(self, tmp_path: Path) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        (armory / "materials").mkdir()
        outside = tmp_path / "outside-secret.md"
        outside.write_text("# Secret\n\nDo not index me.\n")
        link = armory / "materials" / "linked.md"
        try:
            link.symlink_to(outside)
        except OSError:
            pytest.skip("symlinks are not supported on this filesystem")

        assert chunk_file(link, armory) is None

    @pytest.mark.skipif(
        not hasattr(os, "O_NOFOLLOW"),
        reason="O_NOFOLLOW is required to reject symlink swaps after validation",
    )
    def test_rejects_symlink_swap_after_validation(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        armory = tmp_path / "armory"
        materials = armory / "materials"
        materials.mkdir(parents=True)
        src = materials / "notes.txt"
        src.write_text("public material", encoding="utf-8")
        outside = tmp_path / "outside-secret.txt"
        outside.write_text("outside secret", encoding="utf-8")
        original_resolve = rag_chunker._resolved_path_within_armory
        swapped = False

        def swap_after_validation(path: Path, root: Path) -> Path | None:
            nonlocal swapped
            resolved = original_resolve(path, root)
            if resolved is not None and not swapped:
                swapped = True
                src.unlink()
                src.symlink_to(outside)
            return resolved

        monkeypatch.setattr(
            rag_chunker,
            "_resolved_path_within_armory",
            swap_after_validation,
        )

        assert chunk_file(src, armory) is None

    @pytest.mark.skipif(
        not hasattr(os, "O_NOFOLLOW"),
        reason="O_NOFOLLOW is required to reject symlink swaps after validation",
    )
    def test_rejects_parent_directory_symlink_swap_after_validation(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        armory = tmp_path / "armory"
        materials = armory / "materials"
        nested = materials / "nested"
        nested.mkdir(parents=True)
        src = nested / "notes.txt"
        src.write_text("public material", encoding="utf-8")
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        (outside_dir / "notes.txt").write_text("outside secret", encoding="utf-8")
        original_resolve = rag_chunker._resolved_path_within_armory
        swapped = False

        def swap_parent_after_validation(path: Path, root: Path) -> Path | None:
            nonlocal swapped
            resolved = original_resolve(path, root)
            if resolved is not None and not swapped:
                swapped = True
                src.unlink()
                nested.rmdir()
                nested.symlink_to(outside_dir, target_is_directory=True)
            return resolved

        monkeypatch.setattr(
            rag_chunker,
            "_resolved_path_within_armory",
            swap_parent_after_validation,
        )

        assert chunk_file(src, armory) is None


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

    def test_semantic_breakpoints_keep_original_source_offsets(self) -> None:
        text = "First sentence.\n    Indented second sentence.\n\nFinal sentence."
        sentence_spans = rag_chunker._split_sentence_spans(text)

        chunks = rag_chunker._semantic_chunks_from_breakpoints(
            sentence_spans,
            [0, 2, 3],
            source="notes.txt",
            min_chunk=0,
        )

        assert chunks[0].text == "First sentence. Indented second sentence."
        assert chunks[0].char_start == text.index("First")
        assert chunks[0].char_end == text.index("sentence.", text.index("Indented")) + len(
            "sentence."
        )
        assert chunks[1].char_start == text.index("Final")


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
        # Semantic or text fallback - both produce chunks
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

    def test_known_document_extension_is_not_guessed_as_text(self, tmp_path: Path) -> None:
        pdf = tmp_path / "scan.pdf"
        pdf.write_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n")

        assert not _is_text_file(pdf)

    def test_docling_extensions_covered(self) -> None:
        assert ".pdf" in _DOCLING_EXTENSIONS
        assert ".docx" in _DOCLING_EXTENSIONS
        assert ".pptx" in _DOCLING_EXTENSIONS
        assert ".xlsx" in _DOCLING_EXTENSIONS
        assert ".odt" in _DOCLING_EXTENSIONS

    def test_is_docling_available_without_package(self) -> None:
        with patch("harness.rag.chunker._DocumentConverter", None):
            assert not _is_docling_available()

    def test_convert_to_markdown_success(self, tmp_path: Path) -> None:
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\x00fake pdf")

        with patch(
            "harness.rag.chunker._run_docling_worker",
            return_value=_docling_completed("# Report\n\nSome content from the PDF.\n"),
        ):
            md = _convert_to_markdown(pdf)

        assert md is not None
        assert "# Report" in md

    def test_convert_to_markdown_repairs_misplaced_german_umlauts(
        self,
        tmp_path: Path,
    ) -> None:
        pdf = tmp_path / "math-benchmark.pdf"
        pdf.write_bytes(b"%PDF-1.4\x00fake pdf")

        with patch(
            "harness.rag.chunker._run_docling_worker",
            return_value=_docling_completed(
                "Administrative Header\nAdministrative header\n¨ Ubersicht"
            ),
        ):
            md = _convert_to_markdown(pdf)

        assert md == "Administrative Header\nAdministrative header\nÜbersicht"

    def test_normalize_extracted_text_repairs_misplaced_umlauts(self) -> None:
        text = "f¨ ur beschr¨ ankt ¨ Ubung Administrative header"
        assert _normalize_extracted_text(text) == ("für beschränkt Übung Administrative header")

    def test_normalize_extracted_text_repairs_common_latin_ocr_words(self) -> None:
        text = "Begriinden Sie Ihre Antwort. Die Begrundung ist wichtig fiir die Bewertung."
        assert _normalize_extracted_text(text) == (
            "Begründen Sie Ihre Antwort. Die Begründung ist wichtig für die Bewertung."
        )

    def test_normalize_extracted_text_removes_extraction_placeholders(self) -> None:
        text = "Definition\nFormula-not-decoded.\nImage not decoded.\nNext fact"
        assert _normalize_extracted_text(text) == "Definition\n\n\nNext fact"
        assert _normalize_extracted_text("Formula-not-decoded. Image not decoded. OCR noise.") == (
            "  OCR noise."
        )
        assert _normalize_extracted_text("Before <!-- formula-not-decoded --> after") == (
            "Before  after"
        )
        assert _normalize_extracted_text("Before <!-- image --> after") == "Before  after"

    def test_convert_to_markdown_failure_returns_none(self, tmp_path: Path) -> None:
        pdf = tmp_path / "bad.pdf"
        pdf.write_bytes(b"%PDF\x00corrupt")

        with patch(
            "harness.rag.chunker._run_docling_worker",
            return_value=_docling_completed(returncode=1, stderr="conversion failed"),
        ):
            md = _convert_to_markdown(pdf)

        assert md is None

    def test_convert_to_markdown_timeout_returns_none(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        pdf = tmp_path / "slow.pdf"
        pdf.write_bytes(b"%PDF\x00slow")

        def timeout(_path: Path) -> subprocess.CompletedProcess[str]:
            raise subprocess.TimeoutExpired("docling", timeout=1)

        monkeypatch.setattr("harness.rag.chunker._run_docling_worker", timeout)

        assert _convert_to_markdown(pdf) is None

    def test_convert_pdf_to_text_uses_pdftotext_when_available(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        pdf = tmp_path / "plain.pdf"
        pdf.write_bytes(b"%PDF\x00content")

        completed = MagicMock()
        completed.returncode = 0
        completed.stdout = "Plain extracted text."
        completed.stderr = ""
        monkeypatch.setattr("harness.rag.chunker.shutil.which", lambda _name: "pdftotext")
        run = MagicMock(return_value=completed)
        monkeypatch.setattr("harness.rag.chunker.subprocess.run", run)

        text = _convert_pdf_to_text(pdf)

        assert text == "Plain extracted text."
        assert run.call_args.args[0] == [
            "pdftotext",
            "-layout",
            "-enc",
            "UTF-8",
            str(pdf),
            "-",
        ]

    def test_convert_pdf_with_ocr_uses_local_tesseract(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        pdf = tmp_path / "scan.pdf"
        pdf.write_bytes(b"%PDF\x00image")
        commands: list[list[str]] = []
        caplog.set_level(logging.WARNING, logger="harness.rag.chunker")

        def fake_run(args: list[str], **_kwargs: object) -> MagicMock:
            commands.append(args)
            completed = MagicMock()
            completed.stderr = ""
            if args[0] == "pdftoppm":
                completed.returncode = 0 if args[4] == "1" else 1
                if completed.returncode != 0:
                    completed.stderr = "page out of range"
                    return completed
                Path(f"{args[-1]}-1.png").write_bytes(b"png")
                completed.stdout = ""
                return completed
            completed.returncode = 0
            completed.stdout = "OCR extracted theorem text."
            return completed

        def fake_which(name: str) -> str | None:
            if name in {"pdftoppm", "tesseract"}:
                return "/usr/bin/tool"
            return None

        monkeypatch.setattr("harness.rag.chunker.shutil.which", fake_which)
        monkeypatch.setattr("harness.rag.chunker.subprocess.run", fake_run)

        text = _convert_pdf_with_ocr(pdf)

        assert text == "OCR extracted theorem text."
        assert commands[0][:9] == [
            "pdftoppm",
            "-r",
            str(rag_chunker._PDF_OCR_DPI),
            "-f",
            "1",
            "-l",
            "1",
            "-png",
            str(pdf),
        ]
        assert commands[1][0] == "pdftoppm"
        assert commands[2][0] == "tesseract"
        assert not [
            record for record in caplog.records if record.message == "pdf OCR render failed"
        ]

    def test_convert_pdf_with_ocr_uses_pdfinfo_page_count(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        pdf = tmp_path / "scan.pdf"
        pdf.write_bytes(b"%PDF\x00image")
        commands: list[list[str]] = []

        def fake_run(args: list[str], **_kwargs: object) -> MagicMock:
            commands.append(args)
            completed = MagicMock()
            completed.returncode = 0
            completed.stderr = ""
            if args[0] == "pdfinfo":
                completed.stdout = "Pages: 1\n"
                return completed
            if args[0] == "pdftoppm":
                assert args[4] == "1"
                Path(f"{args[-1]}-1.png").write_bytes(b"png")
                completed.stdout = ""
                return completed
            completed.stdout = "OCR extracted theorem text."
            return completed

        monkeypatch.setattr("harness.rag.chunker.shutil.which", lambda _name: "/usr/bin/tool")
        monkeypatch.setattr("harness.rag.chunker.subprocess.run", fake_run)

        text = _convert_pdf_with_ocr(pdf)

        assert text == "OCR extracted theorem text."
        assert [command[0] for command in commands] == ["pdfinfo", "pdftoppm", "tesseract"]

    def test_convert_pdf_with_ocr_skips_oversized_rendered_pages(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        pdf = tmp_path / "scan.pdf"
        pdf.write_bytes(b"%PDF\x00image")
        commands: list[list[str]] = []

        def fake_run(args: list[str], **_kwargs: object) -> MagicMock:
            commands.append(args)
            completed = MagicMock()
            completed.returncode = 0
            completed.stderr = ""
            if args[0] == "pdftoppm":
                Path(f"{args[-1]}-1.png").write_bytes(b"png")
                completed.stdout = ""
                return completed
            raise AssertionError("oversized OCR render should not invoke tesseract")

        monkeypatch.setattr("harness.rag.chunker._PDF_OCR_MAX_RENDERED_BYTES", 2)
        monkeypatch.setattr(
            "harness.rag.chunker.shutil.which",
            lambda name: "/usr/bin/tool" if name in {"pdftoppm", "tesseract"} else None,
        )
        monkeypatch.setattr("harness.rag.chunker.subprocess.run", fake_run)

        assert _convert_pdf_with_ocr(pdf) is None
        assert len(commands) == 1

    def test_convert_pdf_with_ocr_skips_oversized_source(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        pdf = tmp_path / "scan.pdf"
        pdf.write_bytes(b"%PDF\x00image")
        monkeypatch.setattr("harness.rag.chunker._PDF_OCR_MAX_SOURCE_BYTES", 2)
        monkeypatch.setattr("harness.rag.chunker.shutil.which", lambda _name: "/usr/bin/tool")
        run = MagicMock()
        monkeypatch.setattr("harness.rag.chunker.subprocess.run", run)

        assert _convert_pdf_with_ocr(pdf) is None
        run.assert_not_called()

    def test_convert_pdf_with_ocr_honors_total_deadline(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        pdf = tmp_path / "scan.pdf"
        pdf.write_bytes(b"%PDF\x00image")
        commands: list[list[str]] = []

        def fake_run(args: list[str], **_kwargs: object) -> MagicMock:
            commands.append(args)
            completed = MagicMock()
            completed.returncode = 0
            completed.stderr = ""
            if args[0] == "pdftoppm":
                Path(f"{args[-1]}-1.png").write_bytes(b"png")
                completed.stdout = ""
                return completed
            raise AssertionError("expired OCR budget should not invoke tesseract")

        monkeypatch.setattr("harness.rag.chunker._PDF_OCR_TOTAL_TIMEOUT_SECONDS", 0)
        monkeypatch.setattr(
            "harness.rag.chunker.shutil.which",
            lambda name: "/usr/bin/tool" if name in {"pdftoppm", "tesseract"} else None,
        )
        monkeypatch.setattr("harness.rag.chunker.subprocess.run", fake_run)

        assert _convert_pdf_with_ocr(pdf) is None
        assert commands == []

    def test_chunk_pdf_falls_back_to_pdftotext_when_docling_fails(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        pdf = armory / "lecture.pdf"
        pdf.write_bytes(b"%PDF\x00content")

        monkeypatch.setattr("harness.rag.chunker._is_docling_available", lambda: True)
        monkeypatch.setattr("harness.rag.chunker._convert_to_markdown", lambda _path: None)
        monkeypatch.setattr(
            "harness.rag.chunker._convert_pdf_to_text",
            lambda _path: "# Lecture\n\nPlain extracted fallback text.",
        )

        doc = chunk_file(pdf, armory)

        assert doc is not None
        assert doc.source == "lecture.pdf"
        assert any("Plain extracted fallback text" in chunk.text for chunk in doc.chunks)

    def test_chunk_pdf_prefers_pdftotext_before_docling(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        pdf = armory / "lecture.pdf"
        pdf.write_bytes(b"%PDF\x00content")
        docling = MagicMock(return_value="# Lecture\n\nSlow docling text.")

        monkeypatch.setattr("harness.rag.chunker._is_docling_available", lambda: True)
        monkeypatch.setattr("harness.rag.chunker._convert_to_markdown", docling)
        monkeypatch.setattr("harness.rag.chunker._convert_pdf_with_ocr", lambda _path: None)
        monkeypatch.setattr(
            "harness.rag.chunker._convert_pdf_to_text",
            lambda _path: "# Lecture\n\nFast pdftotext text.",
        )

        doc = chunk_file(pdf, armory)

        assert doc is not None
        assert any("Fast pdftotext text" in chunk.text for chunk in doc.chunks)
        docling.assert_not_called()

    def test_convert_to_markdown_failure_suppresses_converter_output(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        pdf = tmp_path / "bad.pdf"
        pdf.write_bytes(b"%PDF\x00corrupt")

        warnings: list[tuple[str, object]] = []
        monkeypatch.setattr(
            "harness.rag.chunker._log.warning",
            lambda message, **kwargs: warnings.append((message, kwargs)),
        )

        with patch(
            "harness.rag.chunker._run_docling_worker",
            return_value=_docling_completed(
                returncode=1,
                stderr="third-party stderr traceback",
            ),
        ):
            md = _convert_to_markdown(pdf)

        captured = capsys.readouterr()
        assert md is None
        assert captured.out == ""
        assert captured.err == ""
        assert warnings

    def test_chunk_docling_file_via_chunk_file(self, tmp_path: Path) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        src = armory / "materials"
        src.mkdir()
        pdf = src / "report.pdf"
        pdf.write_bytes(b"%PDF-1.4\x00binary content")

        with (
            patch(
                "harness.rag.chunker._is_docling_available",
                return_value=True,
            ),
            patch(
                "harness.rag.chunker._convert_pdf_to_text",
                return_value=None,
            ),
            patch(
                "harness.rag.chunker._convert_pdf_with_ocr",
                return_value=None,
            ),
            patch(
                "harness.rag.chunker._run_docling_worker",
                return_value=_docling_completed(
                    "# Chapter 1\n\nContent from PDF.\n\n## Section\n\nMore details."
                ),
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

        with (
            patch(
                "harness.rag.chunker._is_docling_available",
                return_value=False,
            ),
            patch("harness.rag.chunker._is_pdftotext_available", return_value=False),
            patch(
                "harness.rag.chunker._is_pdf_ocr_available",
                return_value=False,
            ),
        ):
            doc = chunk_file(pdf, armory)

        assert doc is None

    def test_chunk_docling_empty_conversion_returns_none(self, tmp_path: Path) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        pdf = armory / "blank.pdf"
        pdf.write_bytes(b"%PDF\x00fake")

        with (
            patch(
                "harness.rag.chunker._is_docling_available",
                return_value=True,
            ),
            patch(
                "harness.rag.chunker._convert_pdf_to_text",
                return_value=None,
            ),
            patch(
                "harness.rag.chunker._convert_pdf_with_ocr",
                return_value=None,
            ),
            patch(
                "harness.rag.chunker._run_docling_worker",
                return_value=_docling_completed("   \n  \n"),
            ),
        ):
            doc = chunk_file(pdf, armory)

        assert doc is None

    def test_chunk_docling_file_rejects_oversized_source(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        src = armory / "report.docx"
        src.write_bytes(b"x" * 8)
        worker = MagicMock()

        monkeypatch.setattr("harness.rag.chunker._MAX_DOCLING_SOURCE_BYTES", 4)
        monkeypatch.setattr("harness.rag.chunker._is_docling_available", lambda: True)
        monkeypatch.setattr("harness.rag.chunker._run_docling_worker", worker)

        assert chunk_file(src, armory) is None
        worker.assert_not_called()

    def test_chunk_docling_file_rejects_oversized_markdown_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        armory = tmp_path / "armory"
        armory.mkdir()
        src = armory / "report.docx"
        src.write_bytes(b"docx")

        monkeypatch.setattr("harness.rag.chunker._MAX_DOCLING_MARKDOWN_CHARS", 4)
        monkeypatch.setattr("harness.rag.chunker._is_docling_available", lambda: True)
        monkeypatch.setattr(
            "harness.rag.chunker._run_docling_worker",
            lambda _path: _docling_completed("x" * 8),
        )

        assert chunk_file(src, armory) is None
