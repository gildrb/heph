"""Materialize a public benchmark manifest into an armory.

The manifest remains the reviewed source of truth. This command only fetches
documents with ``source_url`` into their declared ``materials/...`` paths so a
public corpus can be rebuilt without committing the documents.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from hephaistos.armory import storage

_ALLOWED_URL_SCHEMES = frozenset({"http", "https", "file"})
_DOWNLOAD_TIMEOUT_SECONDS = 60


@dataclass(frozen=True, slots=True)
class MaterializedDocument:
    source: str
    source_url: str
    output_path: str
    status: str
    bytes_written: int
    sha256: str = ""
    error: str = ""


@dataclass(frozen=True, slots=True)
class MaterializeReport:
    status: int
    manifest_path: str
    armory_path: str
    documents: tuple[MaterializedDocument, ...]
    failures: tuple[str, ...]


def materialize_corpus(
    manifest_path: Path,
    armory_path: Path,
    *,
    overwrite: bool = False,
) -> MaterializeReport:
    """Download/copy manifest documents with ``source_url`` into an armory."""
    manifest_path = manifest_path.expanduser().resolve()
    armory_path = armory_path.expanduser().resolve()
    storage.initialize(armory_path)
    materials_root = (armory_path / storage.MATERIALS_DIR).resolve()
    failures: list[str] = []
    materialized: list[MaterializedDocument] = []
    try:
        documents = _manifest_documents(manifest_path)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return MaterializeReport(
            status=2,
            manifest_path=str(manifest_path),
            armory_path=str(armory_path),
            documents=(),
            failures=(str(exc),),
        )

    for raw_document in documents:
        source = str(raw_document["source"])
        source_url = str(raw_document.get("source_url", "")).strip()
        try:
            output_path = _safe_material_path(materials_root, source)
            if not source_url:
                raise ValueError(f"{source} does not define source_url")
            if output_path.exists() and not overwrite:
                raise FileExistsError(f"{output_path} exists; pass --overwrite to replace it")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            bytes_written = _fetch_to_path(source_url, output_path)
            sha256 = _sha256(output_path)
            _verify_expected_file(raw_document, source, output_path, bytes_written, sha256)
            materialized.append(
                MaterializedDocument(
                    source=source,
                    source_url=source_url,
                    output_path=str(output_path),
                    status="written",
                    bytes_written=bytes_written,
                    sha256=sha256,
                )
            )
        except (OSError, ValueError, urllib.error.URLError) as exc:
            failures.append(f"{source}: {exc}")
            materialized.append(
                MaterializedDocument(
                    source=source,
                    source_url=source_url,
                    output_path=str(armory_path / source),
                    status="failed",
                    bytes_written=0,
                    error=str(exc),
                )
            )
    return MaterializeReport(
        status=1 if failures else 0,
        manifest_path=str(manifest_path),
        armory_path=str(armory_path),
        documents=tuple(materialized),
        failures=tuple(failures),
    )


def _manifest_documents(manifest_path: Path) -> list[dict[str, object]]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("manifest must be a JSON object")
    documents = payload.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ValueError("manifest must include non-empty documents")
    result: list[dict[str, object]] = []
    for index, raw_document in enumerate(documents, start=1):
        if not isinstance(raw_document, dict):
            raise TypeError(f"manifest document {index} must be an object")
        source = raw_document.get("source")
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"manifest document {index} must include source")
        result.append(cast("dict[str, object]", raw_document))
    return result


def _safe_material_path(materials_root: Path, source: str) -> Path:
    rel_path = Path(source)
    if rel_path.is_absolute() or not rel_path.parts or rel_path.parts[0] != storage.MATERIALS_DIR:
        raise ValueError(f"source must be a relative materials/ path: {source}")
    if any(part in ("", ".", "..") for part in rel_path.parts):
        raise ValueError(f"unsafe material source path: {source}")
    output_path = (materials_root.parent / rel_path).resolve()
    try:
        output_path.relative_to(materials_root)
    except ValueError as exc:
        raise ValueError(f"source escapes materials directory: {source}") from exc
    return output_path


def _fetch_to_path(source_url: str, output_path: Path) -> int:
    parsed = urllib.parse.urlparse(source_url)
    if parsed.scheme not in _ALLOWED_URL_SCHEMES:
        raise ValueError(f"unsupported source_url scheme: {parsed.scheme or '<none>'}")
    if parsed.scheme == "file":
        source_path = Path(urllib.request.url2pathname(parsed.path)).expanduser().resolve()
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        shutil.copyfile(source_path, output_path)
        return output_path.stat().st_size
    request = urllib.request.Request(source_url, headers={"User-Agent": "hephaistos-benchmark/1"})
    with (
        urllib.request.urlopen(  # nosec B310
            request,
            timeout=_DOWNLOAD_TIMEOUT_SECONDS,
        ) as response,
        output_path.open("wb") as handle,
    ):
        return int(shutil.copyfileobj(response, handle) or output_path.stat().st_size)


def _verify_expected_file(
    raw_document: dict[str, object],
    source: str,
    output_path: Path,
    bytes_written: int,
    sha256: str,
) -> None:
    expected_bytes = raw_document.get("bytes")
    if expected_bytes is not None:
        if not isinstance(expected_bytes, int) or expected_bytes <= 0:
            raise ValueError(f"{source} bytes must be a positive integer")
        if bytes_written != expected_bytes:
            output_path.unlink(missing_ok=True)
            raise ValueError(
                f"{source} byte count mismatch: expected {expected_bytes}, got {bytes_written}"
            )
    expected_sha256 = raw_document.get("sha256")
    if expected_sha256 is not None:
        if not isinstance(expected_sha256, str) or not expected_sha256.strip():
            raise ValueError(f"{source} sha256 must be a non-empty string")
        normalized_expected = expected_sha256.strip().lower()
        if sha256 != normalized_expected:
            output_path.unlink(missing_ok=True)
            raise ValueError(
                f"{source} sha256 mismatch: expected {normalized_expected}, got {sha256}"
            )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def print_text_report(report: MaterializeReport) -> None:
    print(f"Materialized public corpus: {report.manifest_path}")
    print(f"status={report.status}")
    print(f"armory={report.armory_path}")
    written = sum(1 for document in report.documents if document.status == "written")
    print(f"written={written}/{len(report.documents)}")
    if report.failures:
        print("failures:")
        for failure in report.failures:
            print(f"  - {failure}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Reviewed benchmark manifest JSON")
    parser.add_argument("armory", type=Path, help="Armory path to create/populate")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing files")
    parser.add_argument("--json-report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    report = materialize_corpus(
        cast("Path", args.manifest),
        cast("Path", args.armory),
        overwrite=cast("bool", args.overwrite),
    )
    print_text_report(report)
    json_report = cast("Path | None", args.json_report)
    if json_report is not None:
        json_report = json_report.expanduser().resolve()
        json_report.parent.mkdir(parents=True, exist_ok=True)
        json_report.write_text(
            json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return report.status


if __name__ == "__main__":
    raise SystemExit(main())
