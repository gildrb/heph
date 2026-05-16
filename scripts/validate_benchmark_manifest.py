"""Validate benchmark suite manifest breadth and dataset consistency."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TypedDict, cast

DEFAULT_MIN_DOMAINS = 5
DEFAULT_MIN_ROLES = 3
DEFAULT_MIN_DOCUMENT_TYPES = 5
DEFAULT_MIN_STRESSORS = 8
DEFAULT_MIN_DOCUMENTS = 1
PUBLIC_ACADEMIC_CORPUS_KIND = "public-academic"
_LOWER_HEX_DIGITS = frozenset("0123456789abcdef")


class ManifestDocument(TypedDict):
    id: str
    title: str
    source: str
    domain: str
    role: str
    document_type: str
    stressors: list[str]
    source_url: str
    permission_note: str
    bytes: int
    sha256: str
    source_organization: str
    license: str
    license_url: str
    attribution: str


class ManifestDataset(TypedDict):
    path: str
    kind: str


@dataclass(frozen=True, slots=True)
class ManifestReport:
    manifest: str
    suite: str
    corpus_kind: str
    documents: int
    datasets: int
    domains: tuple[str, ...]
    roles: tuple[str, ...]
    document_types: tuple[str, ...]
    stressors: tuple[str, ...]
    source_organizations: tuple[str, ...]
    known_limits: tuple[str, ...]


def _load_json_object(path: Path) -> Mapping[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"could not read benchmark manifest: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid benchmark manifest JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise TypeError("benchmark manifest must be a JSON object")
    return cast("Mapping[str, object]", payload)


def _as_non_empty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _as_string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be a list")
    items = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    if len(items) != len(value):
        raise ValueError(f"{label} must contain non-empty strings only")
    return items


def _documents(payload: Mapping[str, object]) -> list[ManifestDocument]:
    raw_documents = payload.get("documents")
    if not isinstance(raw_documents, list) or not raw_documents:
        raise ValueError("benchmark manifest must include non-empty documents")
    documents: list[ManifestDocument] = []
    for idx, raw in enumerate(raw_documents, start=1):
        if not isinstance(raw, dict):
            raise TypeError(f"document {idx} must be an object")
        documents.append(
            {
                "source": _as_non_empty_string(raw.get("source"), f"document {idx} source"),
                "id": _optional_string(raw.get("id")),
                "title": _optional_string(raw.get("title")),
                "domain": _as_non_empty_string(raw.get("domain"), f"document {idx} domain"),
                "role": _as_non_empty_string(raw.get("role"), f"document {idx} role"),
                "document_type": _as_non_empty_string(
                    raw.get("document_type"), f"document {idx} document_type"
                ),
                "stressors": _as_string_list(raw.get("stressors"), f"document {idx} stressors"),
                "source_url": _optional_string(raw.get("source_url")),
                "permission_note": _optional_string(raw.get("permission_note")),
                "bytes": _optional_positive_int(raw.get("bytes")),
                "sha256": _optional_string(raw.get("sha256")),
                "source_organization": _optional_string(raw.get("source_organization")),
                "license": _optional_string(raw.get("license")),
                "license_url": _optional_string(raw.get("license_url")),
                "attribution": _optional_string(raw.get("attribution")),
            }
        )
    return documents


def _optional_string(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _optional_positive_int(value: object) -> int:
    if isinstance(value, int) and value > 0:
        return value
    return 0


def _datasets(
    payload: Mapping[str, object],
    *,
    allow_empty: bool = False,
) -> list[ManifestDataset]:
    raw_datasets = payload.get("datasets")
    if raw_datasets is None and allow_empty:
        return []
    if not isinstance(raw_datasets, list):
        raise TypeError("benchmark manifest must include datasets as a list")
    if not raw_datasets:
        if allow_empty:
            return []
        raise ValueError("benchmark manifest must include non-empty datasets")
    datasets: list[ManifestDataset] = []
    for idx, raw in enumerate(raw_datasets, start=1):
        if not isinstance(raw, dict):
            raise TypeError(f"dataset {idx} must be an object")
        datasets.append(
            {
                "path": _as_non_empty_string(raw.get("path"), f"dataset {idx} path"),
                "kind": _as_non_empty_string(raw.get("kind"), f"dataset {idx} kind"),
            }
        )
    return datasets


def validate_manifest(
    manifest_path: Path,
    *,
    min_domains: int = DEFAULT_MIN_DOMAINS,
    min_roles: int = DEFAULT_MIN_ROLES,
    min_document_types: int = DEFAULT_MIN_DOCUMENT_TYPES,
    min_stressors: int = DEFAULT_MIN_STRESSORS,
    min_documents: int = DEFAULT_MIN_DOCUMENTS,
    require_corpus_kind: str = "",
    required_document_types: Sequence[str] = (),
    required_stressors: Sequence[str] = (),
    forbid_known_limit: Sequence[str] = (),
    require_document_provenance: bool = False,
) -> ManifestReport:
    """Validate manifest structure, referenced files, and breadth thresholds."""
    if min_documents <= 0:
        raise ValueError("manifest document threshold must be positive")
    if min_domains < 0 or min_roles < 0 or min_document_types < 0 or min_stressors < 0:
        raise ValueError("manifest breadth thresholds must be non-negative")
    manifest_path = manifest_path.resolve()
    suite_path = manifest_path.parent
    payload = _load_json_object(manifest_path)
    corpus_kind = _as_non_empty_string(payload.get("corpus_kind"), "corpus_kind")
    is_public_academic = corpus_kind == PUBLIC_ACADEMIC_CORPUS_KIND
    documents = _documents(payload)
    if is_public_academic:
        _validate_public_academic_documents(documents)
    datasets = _datasets(payload, allow_empty=is_public_academic)
    known_limits = tuple(_as_string_list(payload.get("known_limits", []), "known_limits"))

    for document in documents:
        source_path = suite_path / "armory" / document["source"]
        if not is_public_academic and not source_path.is_file():
            raise ValueError(f"manifest document source does not exist: {document['source']}")
        if (
            require_document_provenance
            and not document["source_url"]
            and not document["permission_note"]
        ):
            raise ValueError(
                "manifest document missing provenance: "
                f"{document['source']} must include source_url or permission_note"
            )
    for dataset in datasets:
        dataset_path = suite_path / dataset["path"]
        if not dataset_path.is_file():
            raise ValueError(f"manifest dataset does not exist: {dataset['path']}")

    domains = tuple(sorted({document["domain"] for document in documents}))
    roles = tuple(sorted({document["role"] for document in documents}))
    document_types = tuple(sorted({document["document_type"] for document in documents}))
    stressors = tuple(
        sorted({stressor for document in documents for stressor in document["stressors"]})
    )
    source_organizations = tuple(
        sorted(
            {
                document["source_organization"]
                for document in documents
                if document["source_organization"]
            }
        )
    )

    if len(documents) < min_documents:
        raise ValueError(
            f"manifest must cover at least {min_documents} documents; found {len(documents)}"
        )
    if require_corpus_kind and corpus_kind != require_corpus_kind:
        raise ValueError(
            f"manifest corpus_kind must be {require_corpus_kind!r}; found {corpus_kind!r}"
        )
    if len(domains) < min_domains:
        raise ValueError(
            f"manifest must cover at least {min_domains} domains; found {len(domains)}"
        )
    if len(roles) < min_roles:
        raise ValueError(f"manifest must cover at least {min_roles} roles; found {len(roles)}")
    if len(document_types) < min_document_types:
        raise ValueError(
            "manifest must cover at least "
            f"{min_document_types} document types; found {len(document_types)}"
        )
    if len(stressors) < min_stressors:
        raise ValueError(
            f"manifest must cover at least {min_stressors} stressors; found {len(stressors)}"
        )
    missing_document_types = tuple(
        sorted({item for item in required_document_types if item not in document_types})
    )
    if missing_document_types:
        raise ValueError(
            f"manifest missing required document type(s): {', '.join(missing_document_types)}"
        )
    missing_stressors = tuple(
        sorted({item for item in required_stressors if item not in stressors})
    )
    if missing_stressors:
        raise ValueError(f"manifest missing required stressor(s): {', '.join(missing_stressors)}")
    forbidden_limits = _matching_known_limits(known_limits, forbid_known_limit)
    if forbidden_limits:
        raise ValueError(
            "manifest known_limits include forbidden unresolved gap(s): "
            f"{'; '.join(forbidden_limits)}"
        )

    return ManifestReport(
        manifest=str(manifest_path),
        suite=str(suite_path),
        corpus_kind=corpus_kind,
        documents=len(documents),
        datasets=len(datasets),
        domains=domains,
        roles=roles,
        document_types=document_types,
        stressors=stressors,
        source_organizations=source_organizations,
        known_limits=known_limits,
    )


def print_text_report(report: ManifestReport) -> None:
    """Print a compact manifest validation report."""
    print(f"Benchmark manifest: {report.manifest}")
    print(f"corpus_kind={report.corpus_kind}")
    print(f"documents={report.documents} datasets={report.datasets}")
    print(f"domains={len(report.domains)} ({', '.join(report.domains)})")
    print(f"roles={len(report.roles)} ({', '.join(report.roles)})")
    print(f"document_types={len(report.document_types)} ({', '.join(report.document_types)})")
    print(f"stressors={len(report.stressors)} ({', '.join(report.stressors)})")
    if report.source_organizations:
        print(
            "source_organizations="
            f"{len(report.source_organizations)} ({', '.join(report.source_organizations)})"
        )
    if report.known_limits:
        print(f"known_limits={len(report.known_limits)}")


def _validate_public_academic_documents(documents: Sequence[ManifestDocument]) -> None:
    seen_ids: set[str] = set()
    seen_sources: set[str] = set()
    seen_urls: set[str] = set()
    for idx, document in enumerate(documents, start=1):
        document_id = document["id"]
        if not document_id:
            raise ValueError(f"document {idx} id must be a non-empty string")
        if document_id in seen_ids:
            raise ValueError(f"duplicate document id: {document_id}")
        seen_ids.add(document_id)

        source = document["source"]
        _validate_material_source(source, idx)
        if source in seen_sources:
            raise ValueError(f"duplicate document source: {source}")
        if document_id == source:
            raise ValueError(f"document {idx} id must be distinct from source path")
        seen_sources.add(source)

        if not document["title"]:
            raise ValueError(f"document {idx} title must be a non-empty string")
        if not document["source_organization"]:
            raise ValueError(f"document {idx} source_organization must be a non-empty string")
        if not document["license"] and not document["permission_note"]:
            raise ValueError(
                f"document {idx} license or permission_note must provide public-use attribution"
            )
        if document["bytes"] <= 0:
            raise ValueError(f"document {idx} bytes must be a positive integer")
        if not _is_lowercase_sha256(document["sha256"]):
            raise ValueError(f"document {idx} sha256 must be a lowercase 64-character hex digest")
        _validate_public_source_url(document["source_url"], idx)
        if document["source_url"] in seen_urls:
            raise ValueError(f"duplicate document source_url: {document['source_url']}")
        seen_urls.add(document["source_url"])


def _validate_material_source(source: str, document_index: int) -> None:
    rel_path = Path(source)
    if rel_path.is_absolute() or not rel_path.parts or rel_path.parts[0] != "materials":
        raise ValueError(f"document {document_index} source must be a relative materials/ path")
    if any(part in ("", ".", "..") for part in rel_path.parts):
        raise ValueError(f"document {document_index} source contains unsafe path segments")


def _is_lowercase_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in _LOWER_HEX_DIGITS for char in value)


def _validate_public_source_url(source_url: str, document_index: int) -> None:
    if not source_url:
        raise ValueError(f"document {document_index} source_url must be a non-empty string")
    parsed = urllib.parse.urlparse(source_url)
    if parsed.scheme != "https":
        raise ValueError(f"document {document_index} source_url must use https")
    if not parsed.hostname:
        raise ValueError(f"document {document_index} source_url must include a hostname")
    if parsed.username or parsed.password:
        raise ValueError(f"document {document_index} source_url must not include credentials")
    if parsed.fragment:
        raise ValueError(f"document {document_index} source_url must not include a fragment")


def _matching_known_limits(
    known_limits: Sequence[str],
    forbidden_patterns: Sequence[str],
) -> tuple[str, ...]:
    matches: list[str] = []
    normalized_limits = [(limit, limit.lower()) for limit in known_limits]
    for pattern in forbidden_patterns:
        normalized_pattern = pattern.strip().lower()
        if not normalized_pattern:
            continue
        matches.extend(
            limit
            for limit, normalized_limit in normalized_limits
            if normalized_pattern in normalized_limit
        )
    return tuple(dict.fromkeys(matches))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Benchmark suite manifest JSON")
    parser.add_argument("--min-domains", type=int, default=DEFAULT_MIN_DOMAINS)
    parser.add_argument("--min-roles", type=int, default=DEFAULT_MIN_ROLES)
    parser.add_argument("--min-document-types", type=int, default=DEFAULT_MIN_DOCUMENT_TYPES)
    parser.add_argument("--min-stressors", type=int, default=DEFAULT_MIN_STRESSORS)
    parser.add_argument("--min-documents", type=int, default=DEFAULT_MIN_DOCUMENTS)
    parser.add_argument(
        "--require-corpus-kind",
        default="",
        help="Require an exact corpus_kind value, for example public-pdfs",
    )
    parser.add_argument(
        "--require-document-type",
        action="append",
        default=[],
        help="Require a document_type to be present; may be repeated",
    )
    parser.add_argument(
        "--require-stressor",
        action="append",
        default=[],
        help="Require a stressor to be present; may be repeated",
    )
    parser.add_argument(
        "--forbid-known-limit",
        action="append",
        default=[],
        help="Fail if any known_limits entry contains this text; may be repeated",
    )
    parser.add_argument(
        "--require-document-provenance",
        action="store_true",
        help="Require each document to include source_url or permission_note.",
    )
    parser.add_argument("--json", action="store_true", help="Print report as JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    manifest = cast("Path", args.manifest).expanduser().resolve()
    try:
        report = validate_manifest(
            manifest,
            min_domains=cast("int", args.min_domains),
            min_roles=cast("int", args.min_roles),
            min_document_types=cast("int", args.min_document_types),
            min_stressors=cast("int", args.min_stressors),
            min_documents=cast("int", args.min_documents),
            require_corpus_kind=cast("str", args.require_corpus_kind),
            required_document_types=cast("list[str]", args.require_document_type),
            required_stressors=cast("list[str]", args.require_stressor),
            forbid_known_limit=cast("list[str]", args.forbid_known_limit),
            require_document_provenance=cast("bool", args.require_document_provenance),
        )
    except (OSError, TypeError, ValueError) as exc:
        print(f"benchmark manifest error: {exc}", file=sys.stderr)
        return 2
    if cast("bool", args.json):
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print_text_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
