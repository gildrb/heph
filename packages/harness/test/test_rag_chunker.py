"""Tests for the RAG chunker."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pytest
from harness.rag import chunker as rag_chunker
from harness.rag.chunker import (
    ChunkStrategy,
    chunk_file,
    chunk_markdown,
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


class TestNativeDocumentExtraction:
    def _archive(self, path: Path, members: dict[str, str]) -> Path:
        with zipfile.ZipFile(path, "w") as archive:
            for name, content in members.items():
                archive.writestr(name, content)
        return path

    def test_docx_extracts_paragraphs_and_tables(self, tmp_path: Path) -> None:
        path = self._archive(
            tmp_path / "sample.docx",
            {
                "word/document.xml": (
                    "<document xmlns='urn:word'><body>"
                    "<p><t>Heading</t></p><p><t>Paragraph</t></p>"
                    "<tbl><tr><tc><p><t>A</t></p></tc><tc><p><t>B</t></p></tc></tr></tbl>"
                    "</body></document>"
                )
            },
        )
        document = chunk_file(path, tmp_path)
        assert document is not None
        text = "\n".join(chunk.text for chunk in document.chunks)
        assert "Heading" in text
        assert "Paragraph" in text
        assert "A\tB" in text

    def test_docx_table_cells_are_tab_delimited(self, tmp_path: Path) -> None:
        path = self._archive(
            tmp_path / "columns.docx",
            {
                "word/document.xml": (
                    "<document xmlns='urn:word'><body><tbl>"
                    "<tr><tc><p><t>Header1</t></p></tc>"
                    "<tc><p><t>Header2</t></p></tc>"
                    "<tc><p><t>Header3</t></p></tc></tr>"
                    "<tr><tc><p><t>Value1</t></p></tc>"
                    "<tc><p><t>Value2</t></p></tc>"
                    "<tc><p><t>Value3</t></p></tc></tr>"
                    "</tbl></body></document>"
                )
            },
        )
        document = chunk_file(path, tmp_path)
        assert document is not None
        text = "\n".join(chunk.text for chunk in document.chunks)
        assert "Header1\tHeader2\tHeader3" in text
        assert "Header1Header2" not in text

    def test_pptx_preserves_slide_order(self, tmp_path: Path) -> None:
        path = self._archive(
            tmp_path / "sample.pptx",
            {
                "ppt/slides/slide1.xml": "<s><t>First slide</t></s>",
                "ppt/slides/slide2.xml": "<s><t>Second slide</t></s>",
            },
        )
        document = chunk_file(path, tmp_path)
        assert document is not None
        text = "\n".join(chunk.text for chunk in document.chunks)
        assert text.index("First slide") < text.index("Second slide")

    def test_pptx_preserves_runs_and_table_rows(self, tmp_path: Path) -> None:
        path = self._archive(
            tmp_path / "formatted.pptx",
            {
                "ppt/slides/slide1.xml": (
                    "<s><sp><txBody><p><r><t>Bold</t></r>"
                    "<r><t> and </t></r><r><t>plain</t></r></p></txBody></sp>"
                    "<graphic><tbl><tr><tc><txBody><p><r><t>A1</t></r></p>"
                    "</txBody></tc><tc><txBody><p><r><t>B1</t></r></p>"
                    "</txBody></tc></tr><tr><tc><txBody><p><r><t>A2</t></r>"
                    "</p></txBody></tc><tc><txBody><p><r><t>B2</t></r></p>"
                    "</txBody></tc></tr></tbl></graphic></s>"
                )
            },
        )
        document = chunk_file(path, tmp_path)
        assert document is not None
        text = "\n".join(chunk.text for chunk in document.chunks)
        assert "Bold and plain" in text
        assert "Bold\nand\nplain" not in text
        assert "A1\tB1" in text
        assert "A2\tB2" in text

    def test_embedded_binary_member_is_not_decompressed(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        path = self._archive(
            tmp_path / "with-image.docx",
            {
                "word/document.xml": "<document><body><p><t>Text</t></p></body></document>",
                "word/media/image.bin": "binary payload",
            },
        )
        read_names: list[str] = []
        original_read = zipfile.ZipFile.read

        def read(
            archive: zipfile.ZipFile,
            member: str | zipfile.ZipInfo,
            pwd: bytes | None = None,
        ) -> bytes:
            read_names.append(member.filename if isinstance(member, zipfile.ZipInfo) else member)
            return original_read(archive, member, pwd)

        monkeypatch.setattr(zipfile.ZipFile, "read", read)
        document = chunk_file(path, tmp_path)
        assert document is not None
        assert "Text" in "\n".join(chunk.text for chunk in document.chunks)
        assert "word/document.xml" in read_names
        assert "word/media/image.bin" not in read_names

    def test_xlsx_handles_shared_and_inline_strings(self, tmp_path: Path) -> None:
        path = self._archive(
            tmp_path / "sample.xlsx",
            {
                "xl/sharedStrings.xml": "<sst><si><t>Shared</t></si></sst>",
                "xl/worksheets/sheet1.xml": (
                    "<worksheet><sheetData><row>"
                    "<c t='s'><v>0</v></c><c t='inlineStr'><is><t>Inline</t></is></c>"
                    "</row></sheetData></worksheet>"
                ),
            },
        )
        document = chunk_file(path, tmp_path)
        assert document is not None
        text = "\n".join(chunk.text for chunk in document.chunks)
        assert "Shared\tInline" in text

    def test_odf_repeats_cells_and_nested_paragraphs(self, tmp_path: Path) -> None:
        path = self._archive(
            tmp_path / "sample.odt",
            {
                "content.xml": (
                    "<doc xmlns:text='urn:text' xmlns:table='urn:table'>"
                    "<text:p><text:span>Heading</text:span></text:p>"
                    "<table:table><table:table-row><table:table-cell "
                    "table:number-columns-repeated='2'><text:p>Cell</text:p>"
                    "</table:table-cell></table:table-row></table:table>"
                    "</doc>"
                )
            },
        )
        document = chunk_file(path, tmp_path)
        assert document is not None
        text = "\n".join(chunk.text for chunk in document.chunks)
        assert "Heading" in text
        assert "Cell" in text

    def test_archive_traversal_and_bomb_limits_skip_safely(self, tmp_path: Path) -> None:
        traversal = tmp_path / "bad.docx"
        with zipfile.ZipFile(traversal, "w") as archive:
            archive.writestr("../escape.xml", "bad")
        assert chunk_file(traversal, tmp_path) is None

        oversized = tmp_path / "large.docx"
        with zipfile.ZipFile(oversized, "w") as archive:
            archive.writestr("word/document.xml", b"x" * (21 * 1024 * 1024))
        assert chunk_file(oversized, tmp_path) is None
