"""Materialize a public benchmark manifest into an armory.

The manifest remains the reviewed source of truth. This command only fetches
documents with ``source_url`` into their declared ``materials/...`` paths so a
public corpus can be rebuilt without committing the documents.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import http.client
import ipaddress
import json
import socket
import ssl
import tempfile
import urllib.error
import urllib.parse
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol, cast

from armory import storage

_ALLOWED_URL_SCHEMES = frozenset({"https"})
_DOWNLOAD_TIMEOUT_SECONDS = 60
_DEFAULT_MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
_DOWNLOAD_CHUNK_BYTES = 1024 * 1024
_PROVENANCE_METADATA_NAME = "public_corpus_provenance.json"

type _IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address


class _Readable(Protocol):
    def read(self, size: int = -1, /) -> bytes: ...


class _Writable(Protocol):
    def write(self, data: bytes, /) -> object: ...


@dataclass(frozen=True, slots=True)
class MaterializedDocument:
    source: str
    source_url: str
    output_path: str
    status: str
    bytes_written: int
    sha256: str = ""
    error: str = ""
    document_id: str = ""
    title: str = ""
    source_organization: str = ""
    license: str = ""
    license_url: str = ""
    attribution: str = ""
    expected_bytes: int = 0
    expected_sha256: str = ""


@dataclass(frozen=True, slots=True)
class MaterializeReport:
    status: int
    manifest_path: str
    armory_path: str
    documents: tuple[MaterializedDocument, ...]
    failures: tuple[str, ...]
    benchmark_ready: bool = False
    provenance_path: str = ""


@dataclass(frozen=True, slots=True)
class _ValidatedSourceUrl:
    parsed: urllib.parse.ParseResult
    hostname: str
    port: int
    addresses: tuple[_IPAddress, ...]


@dataclass(slots=True)
class _PinnedHttpsResponse:
    connection: http.client.HTTPConnection
    response: http.client.HTTPResponse

    def close(self) -> None:
        self.response.close()
        self.connection.close()


def materialize_corpus(
    manifest_path: Path,
    armory_path: Path,
    *,
    overwrite: bool = False,
) -> MaterializeReport:
    """Download/copy manifest documents with ``source_url`` into an armory."""
    manifest_path = manifest_path.expanduser().resolve()
    raw_armory_path = armory_path.expanduser()
    if raw_armory_path.is_symlink():
        return MaterializeReport(
            status=2,
            manifest_path=str(manifest_path),
            armory_path=str(raw_armory_path),
            documents=(),
            failures=(f"armory path must not be a symlink: {raw_armory_path}",),
        )
    armory_path = raw_armory_path.resolve()
    failures: list[str] = []
    materialized: list[MaterializedDocument] = []
    try:
        _reject_symlinked_materials_root(armory_path)
        storage.initialize(armory_path)
        _reject_symlinked_materials_root(armory_path)
        materials_root = (armory_path / storage.MATERIALS_DIR).resolve()
    except (OSError, ValueError) as exc:
        return MaterializeReport(
            status=2,
            manifest_path=str(manifest_path),
            armory_path=str(armory_path),
            documents=(),
            failures=(str(exc),),
        )
    try:
        manifest_payload = _manifest_payload(manifest_path)
        documents = _documents_from_payload(manifest_payload)
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
            max_bytes = _max_download_bytes(raw_document, source)
            download_path = _temporary_download_path(output_path)
            try:
                bytes_written = _fetch_to_path(
                    source_url,
                    download_path,
                    max_bytes=max_bytes,
                )
                sha256 = _sha256(download_path)
                _verify_expected_file(
                    raw_document,
                    source,
                    download_path,
                    bytes_written,
                    sha256,
                )
                download_path.replace(output_path)
            except Exception:
                download_path.unlink(missing_ok=True)
                raise
            materialized.append(
                _materialized_document(
                    raw_document,
                    source=source,
                    source_url=source_url,
                    output_path=output_path,
                    status="written",
                    bytes_written=bytes_written,
                    sha256=sha256,
                )
            )
        except (OSError, ValueError, urllib.error.URLError) as exc:
            failures.append(f"{source}: {exc}")
            materialized.append(
                _materialized_document(
                    raw_document,
                    source=source,
                    source_url=source_url,
                    output_path=armory_path / source,
                    status="failed",
                    bytes_written=0,
                    error=str(exc),
                )
            )
    provenance_path = ""
    if not failures:
        try:
            provenance_path = str(
                _write_provenance_metadata(
                    manifest_payload,
                    documents,
                    tuple(materialized),
                    manifest_path=manifest_path,
                    armory_path=armory_path,
                    overwrite=overwrite,
                )
            )
        except (OSError, ValueError) as exc:
            failures.append(f"provenance metadata: {exc}")
            provenance_path = ""
    return MaterializeReport(
        status=1 if failures else 0,
        manifest_path=str(manifest_path),
        armory_path=str(armory_path),
        documents=tuple(materialized),
        failures=tuple(failures),
        benchmark_ready=not failures,
        provenance_path=provenance_path,
    )


def _manifest_payload(manifest_path: Path) -> dict[str, object]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("manifest must be a JSON object")
    return cast("dict[str, object]", payload)


def _documents_from_payload(payload: dict[str, object]) -> list[dict[str, object]]:
    documents = payload.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ValueError("manifest must include non-empty documents")
    result: list[dict[str, object]] = []
    for index, raw_document in enumerate(documents, start=1):
        if not isinstance(raw_document, dict):
            raise TypeError(f"manifest document {index} must be an object")
        raw_mapping = cast("dict[object, object]", raw_document)
        source = raw_mapping.get("source")
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"manifest document {index} must include source")
        result.append(cast("dict[str, object]", raw_mapping))
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


def _reject_symlinked_materials_root(armory_path: Path) -> None:
    materials_path = armory_path / storage.MATERIALS_DIR
    if materials_path.is_symlink():
        raise ValueError(f"materials directory must not be a symlink: {materials_path}")


def _temporary_download_path(output_path: Path) -> Path:
    with tempfile.NamedTemporaryFile(
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        dir=output_path.parent,
        delete=False,
    ) as handle:
        return Path(handle.name)


def _resolve_source_host_ips(
    hostname: str,
    port: int | None,
) -> tuple[_IPAddress, ...]:
    try:
        infos = socket.getaddrinfo(hostname, port or 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"source_url host cannot be resolved: {hostname}") from exc

    addresses: set[_IPAddress] = set()
    for info in infos:
        raw_address = str(info[4][0])
        with contextlib.suppress(ValueError):
            address = ipaddress.ip_address(raw_address)
            if isinstance(address, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
                addresses.add(address)
    if not addresses:
        raise ValueError(f"source_url host has no usable IP addresses: {hostname}")
    return cast("tuple[_IPAddress, ...]", tuple(sorted(addresses, key=str)))


def _validate_source_url(source_url: str) -> _ValidatedSourceUrl:
    parsed = urllib.parse.urlparse(source_url)
    if parsed.scheme not in _ALLOWED_URL_SCHEMES:
        allowed = ", ".join(sorted(_ALLOWED_URL_SCHEMES))
        raise ValueError(
            f"unsupported source_url scheme: {parsed.scheme or '<none>'}; expected {allowed}"
        )
    if not parsed.hostname:
        raise ValueError("source_url must include a hostname")
    port = parsed.port or 443
    addresses = _resolve_source_host_ips(parsed.hostname, port)
    for address in addresses:
        if not address.is_global:
            raise ValueError(f"source_url host resolves to a non-public address: {address}")
    return _ValidatedSourceUrl(
        parsed=parsed,
        hostname=parsed.hostname,
        port=port,
        addresses=addresses,
    )


def _fetch_to_path(source_url: str, output_path: Path, *, max_bytes: int) -> int:
    validated = _validate_source_url(source_url)
    with _open_validated_https(validated) as response, output_path.open("wb") as handle:
        return _copy_response_limited(response, handle, max_bytes=max_bytes)


@contextlib.contextmanager
def _open_validated_https(validated: _ValidatedSourceUrl) -> Iterator[_Readable]:
    pinned_response = _request_validated_https(validated)
    try:
        yield pinned_response.response
    finally:
        pinned_response.close()


def _request_validated_https(validated: _ValidatedSourceUrl) -> _PinnedHttpsResponse:
    last_error: Exception | None = None
    for address in validated.addresses:
        try:
            return _request_validated_https_address(validated, address)
        except (OSError, http.client.HTTPException) as exc:
            last_error = exc
    if last_error is None:
        raise ValueError(
            f"source_url host has no validated public addresses: {validated.hostname}"
        )
    raise ValueError(
        f"failed to fetch source_url from validated addresses: {last_error}"
    ) from last_error


def _request_validated_https_address(
    validated: _ValidatedSourceUrl,
    address: _IPAddress,
) -> _PinnedHttpsResponse:
    raw_socket = socket.create_connection(
        (str(address), validated.port),
        timeout=_DOWNLOAD_TIMEOUT_SECONDS,
    )
    try:
        tls_context = ssl.create_default_context()
        tls_socket = tls_context.wrap_socket(raw_socket, server_hostname=validated.hostname)
    except Exception:
        raw_socket.close()
        raise

    connection = http.client.HTTPConnection(
        validated.hostname,
        port=validated.port,
        timeout=_DOWNLOAD_TIMEOUT_SECONDS,
    )
    connection.sock = tls_socket
    try:
        connection.putrequest(
            "GET",
            _request_target(validated.parsed),
            skip_host=True,
            skip_accept_encoding=True,
        )
        connection.putheader("Host", _host_header(validated.parsed))
        connection.putheader("User-Agent", "hephaion-benchmark/1")
        connection.putheader("Accept", "*/*")
        connection.putheader("Accept-Encoding", "identity")
        connection.putheader("Connection", "close")
        connection.endheaders()
        response = connection.getresponse()
        try:
            _raise_for_unaccepted_status(
                response.status,
                response.reason,
                response.getheader("Location"),
                validated.parsed.geturl(),
            )
        except ValueError:
            response.close()
            raise
        return _PinnedHttpsResponse(connection=connection, response=response)
    except Exception:
        connection.close()
        raise


def _request_target(parsed: urllib.parse.ParseResult) -> str:
    path = parsed.path or "/"
    if parsed.params:
        path = f"{path};{parsed.params}"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return path


def _host_header(parsed: urllib.parse.ParseResult) -> str:
    if not parsed.hostname:
        raise ValueError("source_url must include a hostname")
    host = parsed.hostname
    with contextlib.suppress(ValueError):
        if isinstance(ipaddress.ip_address(host), ipaddress.IPv6Address):
            host = f"[{host}]"
    if parsed.port is not None and parsed.port != 443:
        return f"{host}:{parsed.port}"
    return host


def _raise_for_unaccepted_status(
    status: int,
    reason: str,
    location: str | None,
    source_url: str,
) -> None:
    if 300 <= status < 400:
        if location:
            raise ValueError(f"source_url redirects are not allowed: {location}")
        raise ValueError("source_url redirects are not allowed")
    if status >= 400:
        response_reason = reason or "HTTP error"
        raise ValueError(f"{source_url} returned HTTP {status}: {response_reason}")


def _copy_response_limited(response: _Readable, handle: _Writable, *, max_bytes: int) -> int:
    total = 0
    while True:
        chunk = response.read(_DOWNLOAD_CHUNK_BYTES)
        if not chunk:
            return total
        total += len(chunk)
        if total > max_bytes:
            raise ValueError(f"download exceeds maximum size of {max_bytes} bytes")
        handle.write(chunk)


def _max_download_bytes(raw_document: dict[str, object], source: str) -> int:
    expected_bytes = raw_document.get("bytes")
    if expected_bytes is None:
        return _DEFAULT_MAX_DOWNLOAD_BYTES
    if not isinstance(expected_bytes, int) or expected_bytes <= 0:
        raise ValueError(f"{source} bytes must be a positive integer")
    if expected_bytes > _DEFAULT_MAX_DOWNLOAD_BYTES:
        raise ValueError(
            f"{source} bytes exceeds maximum supported size: {_DEFAULT_MAX_DOWNLOAD_BYTES}"
        )
    return expected_bytes


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


def _materialized_document(
    raw_document: dict[str, object],
    *,
    source: str,
    source_url: str,
    output_path: Path,
    status: str,
    bytes_written: int,
    sha256: str = "",
    error: str = "",
) -> MaterializedDocument:
    return MaterializedDocument(
        source=source,
        source_url=source_url,
        output_path=str(output_path),
        status=status,
        bytes_written=bytes_written,
        sha256=sha256,
        error=error,
        document_id=_string_field(raw_document, "id"),
        title=_string_field(raw_document, "title"),
        source_organization=_string_field(raw_document, "source_organization"),
        license=_string_field(raw_document, "license"),
        license_url=_string_field(raw_document, "license_url"),
        attribution=_string_field(raw_document, "attribution"),
        expected_bytes=_expected_bytes(raw_document),
        expected_sha256=_string_field(raw_document, "sha256").lower(),
    )


def _write_provenance_metadata(
    manifest_payload: dict[str, object],
    raw_documents: list[dict[str, object]],
    documents: tuple[MaterializedDocument, ...],
    *,
    manifest_path: Path,
    armory_path: Path,
    overwrite: bool,
) -> Path:
    metadata_path = armory_path / storage.INTERNAL_DIR / _PROVENANCE_METADATA_NAME
    if metadata_path.exists() and not overwrite:
        raise FileExistsError(f"{metadata_path} exists; pass --overwrite to replace it")

    by_source = {document.source: document for document in documents}
    metadata_documents: list[dict[str, object]] = []
    for raw_document in raw_documents:
        source = str(raw_document["source"])
        document = by_source[source]
        metadata_documents.append(
            {
                "id": document.document_id,
                "title": document.title,
                "source": document.source,
                "source_url": document.source_url,
                "output_path": document.output_path,
                "bytes": document.bytes_written,
                "sha256": document.sha256,
                "expected_bytes": document.expected_bytes,
                "expected_sha256": document.expected_sha256,
                "source_organization": document.source_organization,
                "license": document.license,
                "license_url": document.license_url,
                "attribution": document.attribution,
                "domain": _string_field(raw_document, "domain"),
                "role": _string_field(raw_document, "role"),
                "document_type": _string_field(raw_document, "document_type"),
                "stressors": _string_list_field(raw_document, "stressors"),
            }
        )

    payload = {
        "schema_version": 1,
        "benchmark_ready": True,
        "manifest_path": str(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
        "armory_path": str(armory_path),
        "corpus_kind": _string_field(manifest_payload, "corpus_kind"),
        "document_count": len(metadata_documents),
        "documents": metadata_documents,
    }
    metadata_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata_path


def _string_field(mapping: dict[str, object], key: str) -> str:
    value = mapping.get(key)
    if isinstance(value, str):
        return value.strip()
    return ""


def _string_list_field(mapping: dict[str, object], key: str) -> list[str]:
    value = mapping.get(key)
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _expected_bytes(raw_document: dict[str, object]) -> int:
    value = raw_document.get("bytes")
    if isinstance(value, int) and value > 0:
        return value
    return 0


def print_text_report(report: MaterializeReport) -> None:
    print(f"Materialized public corpus: {report.manifest_path}")
    print(f"status={report.status}")
    print(f"armory={report.armory_path}")
    print(f"benchmark_ready={str(report.benchmark_ready).lower()}")
    if report.provenance_path:
        print(f"provenance={report.provenance_path}")
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
