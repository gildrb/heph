from __future__ import annotations

import json
from pathlib import Path

from scripts import materialize_public_corpus


def _write_manifest(path: Path, documents: list[dict[str, object]]) -> None:
    path.write_text(
        json.dumps(
            {
                "id": "public-test",
                "description": "Public test corpus",
                "corpus_kind": "public-pdfs",
                "documents": documents,
                "datasets": [],
                "known_limits": [],
            }
        ),
        encoding="utf-8",
    )


def test_materialize_corpus_copies_file_urls_into_armory(tmp_path: Path) -> None:
    source_doc = tmp_path / "source.pdf"
    source_doc.write_bytes(b"public pdf bytes")
    manifest = tmp_path / "manifest.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/public/source.pdf",
                "source_url": source_doc.as_uri(),
                "domain": "mathematics",
                "role": "lecture",
                "document_type": "pdf",
                "stressors": ["real-pdf"],
            }
        ],
    )
    armory = tmp_path / "armory"

    report = materialize_public_corpus.materialize_corpus(manifest, armory)

    output = armory / "materials" / "public" / "source.pdf"
    assert report.status == 0
    assert output.read_bytes() == b"public pdf bytes"
    assert report.documents[0].bytes_written == len(b"public pdf bytes")
    assert report.documents[0].sha256


def test_materialize_corpus_verifies_pinned_hash_and_size(tmp_path: Path) -> None:
    source_doc = tmp_path / "source.md"
    source_doc.write_text("stable material", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/source.md",
                "source_url": source_doc.as_uri(),
                "bytes": source_doc.stat().st_size,
                "sha256": ("ec5112e98274d45f90eda5fc3c5d255da4861971d8806a91e75622e7eb208d9f"),
                "domain": "general",
                "role": "reference",
                "document_type": "notes",
                "stressors": ["unicode"],
            }
        ],
    )

    report = materialize_public_corpus.materialize_corpus(manifest, tmp_path / "armory")

    assert report.status == 0
    assert report.documents[0].sha256 == (
        "ec5112e98274d45f90eda5fc3c5d255da4861971d8806a91e75622e7eb208d9f"
    )


def test_materialize_corpus_removes_file_on_hash_mismatch(tmp_path: Path) -> None:
    source_doc = tmp_path / "source.md"
    source_doc.write_text("changed material", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/source.md",
                "source_url": source_doc.as_uri(),
                "sha256": "0" * 64,
                "domain": "general",
                "role": "reference",
                "document_type": "notes",
                "stressors": ["unicode"],
            }
        ],
    )

    report = materialize_public_corpus.materialize_corpus(manifest, tmp_path / "armory")

    assert report.status == 1
    assert "sha256 mismatch" in report.failures[0]
    assert not (tmp_path / "armory" / "materials" / "source.md").exists()


def test_materialize_corpus_rejects_missing_source_url(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/permissioned.md",
                "permission_note": "available to enrolled students",
                "domain": "history",
                "role": "lecture",
                "document_type": "notes",
                "stressors": ["lecture"],
            }
        ],
    )

    report = materialize_public_corpus.materialize_corpus(manifest, tmp_path / "armory")

    assert report.status == 1
    assert "does not define source_url" in report.failures[0]


def test_materialize_corpus_rejects_path_traversal(tmp_path: Path) -> None:
    source_doc = tmp_path / "source.md"
    source_doc.write_text("secret", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/../escape.md",
                "source_url": source_doc.as_uri(),
                "domain": "general",
                "role": "reference",
                "document_type": "notes",
                "stressors": ["unicode"],
            }
        ],
    )

    report = materialize_public_corpus.materialize_corpus(manifest, tmp_path / "armory")

    assert report.status == 1
    assert "unsafe material source path" in report.failures[0]


def test_materialize_corpus_refuses_overwrite_without_flag(tmp_path: Path) -> None:
    source_doc = tmp_path / "source.md"
    source_doc.write_text("fresh", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/source.md",
                "source_url": source_doc.as_uri(),
                "domain": "general",
                "role": "reference",
                "document_type": "notes",
                "stressors": ["unicode"],
            }
        ],
    )
    armory = tmp_path / "armory"
    existing = armory / "materials" / "source.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("old", encoding="utf-8")

    report = materialize_public_corpus.materialize_corpus(manifest, armory)

    assert report.status == 1
    assert existing.read_text(encoding="utf-8") == "old"
    assert "pass --overwrite" in report.failures[0]


def test_materialize_corpus_cli_writes_json_report(tmp_path: Path) -> None:
    source_doc = tmp_path / "source.md"
    source_doc.write_text("material", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    report_path = tmp_path / "report.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/source.md",
                "source_url": source_doc.as_uri(),
                "domain": "general",
                "role": "reference",
                "document_type": "notes",
                "stressors": ["unicode"],
            }
        ],
    )

    status = materialize_public_corpus.main(
        [str(manifest), str(tmp_path / "armory"), "--json-report", str(report_path)]
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 0
    assert payload["status"] == 0
    assert payload["documents"][0]["status"] == "written"
