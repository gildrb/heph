from __future__ import annotations

import ipaddress
import json
from io import BytesIO
from pathlib import Path
from typing import Self

import pytest

from scripts import materialize_public_corpus


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._buffer = BytesIO(body)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        _exc_type: object,
        _exc: object,
        _traceback: object,
    ) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        if size == 0:
            size = -1
        return self._buffer.read(size)


def _stub_https_download(monkeypatch: pytest.MonkeyPatch, body: bytes) -> None:
    def fake_resolve(
        _hostname: str,
        _port: int | None,
    ) -> tuple[materialize_public_corpus._IPAddress, ...]:
        return (ipaddress.ip_address("93.184.216.34"),)

    def fake_open(_validated: object) -> _FakeResponse:
        return _FakeResponse(body)

    monkeypatch.setattr(materialize_public_corpus, "_resolve_source_host_ips", fake_resolve)
    monkeypatch.setattr(materialize_public_corpus, "_open_validated_https", fake_open)


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


def test_materialize_corpus_downloads_https_urls_into_armory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_https_download(monkeypatch, b"public pdf bytes")
    manifest = tmp_path / "manifest.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/public/source.pdf",
                "source_url": "https://example.edu/source.pdf",
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


def test_materialize_corpus_verifies_pinned_hash_and_size(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = b"stable material"
    _stub_https_download(monkeypatch, body)
    manifest = tmp_path / "manifest.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/source.md",
                "source_url": "https://example.edu/source.md",
                "bytes": len(body),
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


def test_materialize_corpus_removes_file_on_hash_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_https_download(monkeypatch, b"changed material")
    manifest = tmp_path / "manifest.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/source.md",
                "source_url": "https://example.edu/source.md",
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


def test_materialize_corpus_removes_partial_download_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_fetch(_source_url: str, output_path: Path, *, max_bytes: int) -> int:
        _ = max_bytes
        output_path.write_bytes(b"partial")
        raise OSError("connection reset")

    monkeypatch.setattr(materialize_public_corpus, "_fetch_to_path", fake_fetch)
    manifest = tmp_path / "manifest.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/source.md",
                "source_url": "https://example.edu/source.md",
                "domain": "general",
                "role": "reference",
                "document_type": "notes",
                "stressors": ["unicode"],
            }
        ],
    )
    armory = tmp_path / "armory"

    report = materialize_public_corpus.materialize_corpus(manifest, armory)

    material_dir = armory / "materials"
    assert report.status == 1
    assert "connection reset" in report.failures[0]
    assert not (material_dir / "source.md").exists()
    assert list(material_dir.iterdir()) == []


def test_materialize_corpus_rejects_downloads_over_expected_size(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_https_download(monkeypatch, b"too much")
    manifest = tmp_path / "manifest.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/source.md",
                "source_url": "https://example.edu/source.md",
                "bytes": 4,
                "domain": "general",
                "role": "reference",
                "document_type": "notes",
                "stressors": ["unicode"],
            }
        ],
    )

    report = materialize_public_corpus.materialize_corpus(manifest, tmp_path / "armory")

    assert report.status == 1
    assert "download exceeds maximum size of 4 bytes" in report.failures[0]
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
    manifest = tmp_path / "manifest.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/../escape.md",
                "source_url": "https://example.edu/source.md",
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


def test_materialize_corpus_rejects_symlinked_materials_root(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    armory.mkdir()
    outside = tmp_path / "outside-materials"
    outside.mkdir()
    try:
        (armory / "materials").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are not supported on this filesystem")
    manifest = tmp_path / "manifest.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/source.md",
                "source_url": "https://example.edu/source.md",
                "domain": "general",
                "role": "reference",
                "document_type": "notes",
                "stressors": ["unicode"],
            }
        ],
    )

    report = materialize_public_corpus.materialize_corpus(manifest, armory)

    assert report.status == 2
    assert "materials directory must not be a symlink" in report.failures[0]
    assert list(outside.iterdir()) == []


def test_materialize_corpus_refuses_overwrite_without_flag(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/source.md",
                "source_url": "https://example.edu/source.md",
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


def test_materialize_corpus_rejects_file_urls(tmp_path: Path) -> None:
    source_doc = tmp_path / "source.md"
    source_doc.write_text("secret", encoding="utf-8")
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

    report = materialize_public_corpus.materialize_corpus(manifest, tmp_path / "armory")

    assert report.status == 1
    assert "unsupported source_url scheme: file" in report.failures[0]


def test_materialize_corpus_rejects_private_https_hosts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_resolve(
        _hostname: str,
        _port: int | None,
    ) -> tuple[ipaddress.IPv4Address | ipaddress.IPv6Address, ...]:
        return (ipaddress.ip_address("127.0.0.1"),)

    monkeypatch.setattr(materialize_public_corpus, "_resolve_source_host_ips", fake_resolve)
    manifest = tmp_path / "manifest.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/source.md",
                "source_url": "https://localhost/source.md",
                "domain": "general",
                "role": "reference",
                "document_type": "notes",
                "stressors": ["unicode"],
            }
        ],
    )

    report = materialize_public_corpus.materialize_corpus(manifest, tmp_path / "armory")

    assert report.status == 1
    assert "resolves to a non-public address" in report.failures[0]


def test_materialize_corpus_rejects_https_redirects() -> None:
    with pytest.raises(ValueError, match="redirects are not allowed"):
        materialize_public_corpus._raise_for_unaccepted_status(
            302,
            "Found",
            "https://example.edu/next.md",
            "https://example.edu/source.md",
        )


def test_materialize_corpus_cli_writes_json_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_https_download(monkeypatch, b"material")
    manifest = tmp_path / "manifest.json"
    report_path = tmp_path / "report.json"
    _write_manifest(
        manifest,
        [
            {
                "source": "materials/source.md",
                "source_url": "https://example.edu/source.md",
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
