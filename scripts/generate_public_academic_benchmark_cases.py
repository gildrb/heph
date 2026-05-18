"""Generate deterministic benchmark cases for the public academic corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import cast

from hephaistos.armory import storage
from scripts import validate_benchmark_manifest

_PROVENANCE_METADATA_NAME = "public_corpus_provenance.json"
_PUBLIC_ACADEMIC_CORPUS_KIND = "public-academic"
_RAG_CASES_FILE = "rag.jsonl"
_MATERIAL_ROLE_CASES_FILE = "material_roles.jsonl"
_DOCUMENT_UNDERSTANDING_CASES_FILE = "document_understanding.jsonl"
_READINESS_REPORT_FILE = "readiness_report.json"
_DEFAULT_TOP_K = 5


@dataclass(frozen=True, slots=True)
class CaseGenerationMinimums:
    retrieval_cases: int = 25
    material_role_cases: int = 15
    document_understanding_cases: int = 10
    domains: int = 3
    material_roles: int = 4
    source_organizations: int = 3


_DEFAULT_MINIMUMS = CaseGenerationMinimums()


@dataclass(frozen=True, slots=True)
class PublicAcademicDocument:
    document_id: str
    title: str
    source: str
    source_url: str
    bytes: int
    sha256: str
    source_organization: str
    license: str
    license_url: str
    attribution: str
    domain: str
    role: str
    document_type: str
    stressors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RetrievalCase:
    id: str
    domain: str
    task: str
    query: str
    expected: tuple[str, ...]
    forbidden_before_expected: tuple[str, ...]
    top_k: int
    document_id: str
    expected_document_ids: tuple[str, ...]
    forbidden_document_ids: tuple[str, ...]
    source_organization: str
    title: str


@dataclass(frozen=True, slots=True)
class MaterialRoleCase:
    id: str
    domain: str
    source: str
    expected_role: str
    expected_material_role: str
    expected_public_academic_role: str
    document_id: str
    source_organization: str
    title: str
    document_type: str


@dataclass(frozen=True, slots=True)
class DocumentUnderstandingCase:
    id: str
    domain: str
    task: str
    prompt: str
    source: str
    document_id: str
    title: str
    source_organization: str
    expected_material_role: str
    expected_evidence: tuple[str, ...]
    expected_citation_targets: tuple[str, ...]
    expected_answer_criteria: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GeneratedCases:
    retrieval: tuple[RetrievalCase, ...]
    material_roles: tuple[MaterialRoleCase, ...]
    document_understanding: tuple[DocumentUnderstandingCase, ...]


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    schema_version: int
    status: str
    benchmark_ready: bool
    manifest_path: str
    armory_path: str
    provenance_path: str
    output_dir: str
    manifest_sha256: str
    manifest_document_count: int
    materialized_file_count: int
    safety_checks_status: str
    hash_verification_status: str
    byte_verification_status: str
    provenance_status: str
    deterministic_serialization_status: str
    case_counts_by_type: dict[str, int]
    breadth: dict[str, int]
    near_miss_retrieval_cases: int
    generated_files: dict[str, str]
    failures: tuple[str, ...]


def generate_cases(
    manifest_path: Path,
    armory_path: Path,
    output_dir: Path,
    *,
    minimums: CaseGenerationMinimums = _DEFAULT_MINIMUMS,
    overwrite: bool = False,
) -> ReadinessReport:
    """Validate a materialized public corpus and write deterministic case files."""
    _validate_minimums(minimums)
    manifest_path = manifest_path.expanduser().resolve()
    armory_path = armory_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    validate_benchmark_manifest.validate_manifest(
        manifest_path,
        min_domains=0,
        min_roles=0,
        min_document_types=0,
        min_stressors=0,
        require_corpus_kind=_PUBLIC_ACADEMIC_CORPUS_KIND,
    )
    documents = _load_manifest_documents(manifest_path)
    provenance_path = armory_path / storage.INTERNAL_DIR / _PROVENANCE_METADATA_NAME
    manifest_sha256 = _sha256(manifest_path)
    _verify_materialized_corpus(
        manifest_path,
        armory_path,
        provenance_path,
        documents,
        manifest_sha256=manifest_sha256,
    )
    cases = _generate_cases(documents)
    failures = _case_validation_failures(cases, documents, minimums)
    rendered = _render_artifacts(cases)
    deterministic_status = "passed" if rendered == _render_artifacts(cases) else "failed"
    if deterministic_status != "passed":
        failures.append("case serialization is not deterministic")
    if failures:
        raise ValueError("; ".join(failures))

    target_paths = _target_paths(output_dir)
    _prepare_output_paths(target_paths, overwrite=overwrite)
    for name, content in rendered.items():
        target_paths[name].write_text(content, encoding="utf-8")

    report = _readiness_report(
        manifest_path=manifest_path,
        armory_path=armory_path,
        provenance_path=provenance_path,
        output_dir=output_dir,
        manifest_sha256=manifest_sha256,
        documents=documents,
        cases=cases,
        deterministic_status=deterministic_status,
        failures=(),
    )
    target_paths[_READINESS_REPORT_FILE].write_text(
        _readiness_report_json(report),
        encoding="utf-8",
    )
    return report


def _validate_minimums(minimums: CaseGenerationMinimums) -> None:
    values = {
        "retrieval_cases": minimums.retrieval_cases,
        "material_role_cases": minimums.material_role_cases,
        "document_understanding_cases": minimums.document_understanding_cases,
        "domains": minimums.domains,
        "material_roles": minimums.material_roles,
        "source_organizations": minimums.source_organizations,
    }
    invalid = tuple(name for name, value in values.items() if value < 0)
    if invalid:
        raise ValueError(f"case generation minimums must be non-negative: {', '.join(invalid)}")


def _load_manifest_documents(manifest_path: Path) -> tuple[PublicAcademicDocument, ...]:
    payload = _load_json_object(manifest_path)
    raw_documents = _object_list(payload, "documents")
    return tuple(
        _public_academic_document(raw_document, index)
        for index, raw_document in enumerate(raw_documents, start=1)
    )


def _public_academic_document(
    raw_document: dict[str, object],
    index: int,
) -> PublicAcademicDocument:
    return PublicAcademicDocument(
        document_id=_required_string(raw_document, "id", f"document {index} id"),
        title=_required_string(raw_document, "title", f"document {index} title"),
        source=_required_string(raw_document, "source", f"document {index} source"),
        source_url=_required_string(
            raw_document,
            "source_url",
            f"document {index} source_url",
        ),
        bytes=_required_positive_int(raw_document, "bytes", f"document {index} bytes"),
        sha256=_required_string(raw_document, "sha256", f"document {index} sha256").lower(),
        source_organization=_required_string(
            raw_document,
            "source_organization",
            f"document {index} source_organization",
        ),
        license=_string_field(raw_document, "license"),
        license_url=_string_field(raw_document, "license_url"),
        attribution=_string_field(raw_document, "attribution"),
        domain=_required_string(raw_document, "domain", f"document {index} domain"),
        role=_required_string(raw_document, "role", f"document {index} role"),
        document_type=_required_string(
            raw_document,
            "document_type",
            f"document {index} document_type",
        ),
        stressors=tuple(_string_list_field(raw_document, "stressors")),
    )


def _verify_materialized_corpus(
    manifest_path: Path,
    armory_path: Path,
    provenance_path: Path,
    documents: Sequence[PublicAcademicDocument],
    *,
    manifest_sha256: str,
) -> None:
    if not provenance_path.is_file():
        raise ValueError(f"public corpus provenance metadata is missing: {provenance_path}")
    provenance = _load_json_object(provenance_path)
    if _bool_field(provenance, "benchmark_ready") is not True:
        raise ValueError("public corpus provenance metadata is not benchmark-ready")
    if _string_field(provenance, "corpus_kind") != _PUBLIC_ACADEMIC_CORPUS_KIND:
        raise ValueError("public corpus provenance metadata is not for public-academic")
    if _string_field(provenance, "manifest_sha256") != manifest_sha256:
        raise ValueError(f"public corpus provenance manifest hash does not match {manifest_path}")
    if _positive_int_field(provenance, "document_count") != len(documents):
        raise ValueError("public corpus provenance document count does not match manifest")

    provenance_documents = _provenance_documents_by_id(provenance)
    for document in documents:
        provenance_document = provenance_documents.get(document.document_id)
        if provenance_document is None:
            raise ValueError(
                f"public corpus provenance missing document id: {document.document_id}"
            )
        _verify_document_provenance(document, provenance_document)
        material_path = _safe_material_path(armory_path, document.source)
        if not material_path.is_file():
            raise ValueError(f"materialized file is missing: {document.source}")
        actual_bytes = material_path.stat().st_size
        if actual_bytes != document.bytes:
            raise ValueError(
                f"{document.source} byte count mismatch: "
                f"expected {document.bytes}, got {actual_bytes}"
            )
        actual_sha256 = _sha256(material_path)
        if actual_sha256 != document.sha256:
            raise ValueError(
                f"{document.source} sha256 mismatch: "
                f"expected {document.sha256}, got {actual_sha256}"
            )


def _provenance_documents_by_id(
    provenance: dict[str, object],
) -> dict[str, dict[str, object]]:
    by_id: dict[str, dict[str, object]] = {}
    for index, raw_document in enumerate(_object_list(provenance, "documents"), start=1):
        document_id = _required_string(raw_document, "id", f"provenance document {index} id")
        if document_id in by_id:
            raise ValueError(f"duplicate provenance document id: {document_id}")
        by_id[document_id] = raw_document
    return by_id


def _verify_document_provenance(
    document: PublicAcademicDocument,
    provenance_document: dict[str, object],
) -> None:
    expected_fields = {
        "source": document.source,
        "source_url": document.source_url,
        "title": document.title,
        "source_organization": document.source_organization,
        "domain": document.domain,
        "role": document.role,
        "document_type": document.document_type,
        "sha256": document.sha256,
        "expected_sha256": document.sha256,
    }
    for field, expected_value in expected_fields.items():
        if _string_field(provenance_document, field) != expected_value:
            raise ValueError(
                f"{document.document_id} provenance field {field} does not match manifest"
            )
    byte_fields = {
        "bytes": document.bytes,
        "expected_bytes": document.bytes,
    }
    for field, expected_value in byte_fields.items():
        if _positive_int_field(provenance_document, field) != expected_value:
            raise ValueError(
                f"{document.document_id} provenance field {field} does not match manifest"
            )


def _safe_material_path(armory_path: Path, source: str) -> Path:
    rel_path = Path(source)
    if rel_path.is_absolute() or not rel_path.parts or rel_path.parts[0] != storage.MATERIALS_DIR:
        raise ValueError(f"source must be a relative materials/ path: {source}")
    if any(part in ("", ".", "..") for part in rel_path.parts):
        raise ValueError(f"unsafe material source path: {source}")
    materials_root = (armory_path / storage.MATERIALS_DIR).resolve()
    material_path = (armory_path / rel_path).resolve()
    try:
        material_path.relative_to(materials_root)
    except ValueError as exc:
        raise ValueError(f"source escapes materials directory: {source}") from exc
    return material_path


def _generate_cases(documents: Sequence[PublicAcademicDocument]) -> GeneratedCases:
    ordered_documents = tuple(documents)
    title_counts = Counter(
        (document.source_organization, document.title) for document in ordered_documents
    )
    retrieval_cases = tuple(
        _retrieval_case(
            document,
            ordered_documents,
            include_source_hint=title_counts[(document.source_organization, document.title)] > 1,
        )
        for document in ordered_documents
    )
    material_role_cases = tuple(_material_role_case(document) for document in ordered_documents)
    document_understanding_cases = tuple(
        _document_understanding_case(document) for document in ordered_documents
    )
    return GeneratedCases(
        retrieval=retrieval_cases,
        material_roles=material_role_cases,
        document_understanding=document_understanding_cases,
    )


def _retrieval_case(
    document: PublicAcademicDocument,
    documents: Sequence[PublicAcademicDocument],
    *,
    include_source_hint: bool,
) -> RetrievalCase:
    near_miss = _near_miss_document(document, documents)
    forbidden_before_expected = (near_miss.source,) if near_miss is not None else ()
    forbidden_document_ids = (near_miss.document_id,) if near_miss is not None else ()
    return RetrievalCase(
        id=f"public-academic-retrieval-{document.document_id}",
        domain=document.domain,
        task="near-miss-negative" if near_miss is not None else "single-source-title",
        query=_retrieval_query(document, include_source_hint=include_source_hint),
        expected=(document.source,),
        forbidden_before_expected=forbidden_before_expected,
        top_k=_DEFAULT_TOP_K,
        document_id=document.document_id,
        expected_document_ids=(document.document_id,),
        forbidden_document_ids=forbidden_document_ids,
        source_organization=document.source_organization,
        title=document.title,
    )


def _near_miss_document(
    document: PublicAcademicDocument,
    documents: Sequence[PublicAcademicDocument],
) -> PublicAcademicDocument | None:
    for candidate in documents:
        if candidate.document_id != document.document_id and candidate.domain == document.domain:
            return candidate
    for candidate in documents:
        if (
            candidate.document_id != document.document_id
            and candidate.source_organization == document.source_organization
        ):
            return candidate
    for candidate in documents:
        if candidate.document_id != document.document_id:
            return candidate
    return None


def _retrieval_query(document: PublicAcademicDocument, *, include_source_hint: bool) -> str:
    domain = document.domain.replace("-", " ")
    source_hint = ""
    if include_source_hint:
        source_hint = f' at source section "{_source_section_hint(document.source)}"'
    return (
        "Which public academic material titled "
        f'"{document.title}" from {document.source_organization}{source_hint} '
        f"covers {domain}?"
    )


def _source_section_hint(source: str) -> str:
    path = Path(source)
    parts = list(path.with_suffix("").parts)
    if parts and parts[-1] == "index":
        parts.pop()
    if len(parts) >= 3 and parts[0] == storage.MATERIALS_DIR:
        parts = parts[2:]
    return "/".join(parts[-2:]) if len(parts) >= 2 else "/".join(parts)


def _material_role_case(document: PublicAcademicDocument) -> MaterialRoleCase:
    public_role = _public_material_role(document)
    return MaterialRoleCase(
        id=f"public-academic-role-{document.document_id}",
        domain=document.domain,
        source=document.source,
        expected_role=_benchmark_material_role(public_role),
        expected_material_role=public_role,
        expected_public_academic_role=document.role,
        document_id=document.document_id,
        source_organization=document.source_organization,
        title=document.title,
        document_type=document.document_type,
    )


def _public_material_role(document: PublicAcademicDocument) -> str:
    if document.document_type == "html-chapter-summary":
        return "reference"
    if "textbook" in document.document_type or document.role == "textbook":
        return "textbook"
    if document.document_type == "html-course-notes":
        return "course-notes"
    if document.document_type == "html-lecture-notes" or document.role == "lecture-notes":
        return "lecture-notes"
    return document.role


def _benchmark_material_role(public_role: str) -> str:
    if public_role in {"course-notes", "lecture-notes"}:
        return "lecture"
    if public_role in {"textbook", "reference", "assignment", "slides"}:
        return public_role
    return "reference"


def _document_understanding_case(document: PublicAcademicDocument) -> DocumentUnderstandingCase:
    material_role = _public_material_role(document)
    return DocumentUnderstandingCase(
        id=f"public-academic-understanding-{document.document_id}",
        domain=document.domain,
        task="source-grounded-document-understanding",
        prompt=(
            "Using only the cited public academic material, identify the source "
            f"organization, domain, and material role for {document.title}."
        ),
        source=document.source,
        document_id=document.document_id,
        title=document.title,
        source_organization=document.source_organization,
        expected_material_role=material_role,
        expected_evidence=(document.source,),
        expected_citation_targets=(document.source,),
        expected_answer_criteria=(
            f"title: {document.title}",
            f"source organization: {document.source_organization}",
            f"domain: {document.domain}",
            f"material role: {material_role}",
        ),
    )


def _case_validation_failures(
    cases: GeneratedCases,
    documents: Sequence[PublicAcademicDocument],
    minimums: CaseGenerationMinimums,
) -> list[str]:
    failures: list[str] = []
    document_sources = {document.source for document in documents}
    _extend_minimum_failure(
        failures,
        "retrieval cases",
        len(cases.retrieval),
        minimums.retrieval_cases,
    )
    _extend_minimum_failure(
        failures,
        "material role cases",
        len(cases.material_roles),
        minimums.material_role_cases,
    )
    _extend_minimum_failure(
        failures,
        "document understanding cases",
        len(cases.document_understanding),
        minimums.document_understanding_cases,
    )
    near_miss_cases = sum(1 for case in cases.retrieval if case.forbidden_before_expected)
    if near_miss_cases <= 0:
        failures.append("retrieval cases must include negative/near-miss expectations")

    for case in cases.retrieval:
        failures.extend(
            f"{case.id} references unknown document source: {reference}"
            for reference in (*case.expected, *case.forbidden_before_expected)
            if _source_reference(reference) not in document_sources
        )
    failures.extend(
        f"{case.id} references unknown document source: {case.source}"
        for case in cases.material_roles
        if case.source not in document_sources
    )
    for case in cases.document_understanding:
        failures.extend(
            f"{case.id} references unknown document source: {reference}"
            for reference in (*case.expected_evidence, *case.expected_citation_targets)
            if _source_reference(reference) not in document_sources
        )

    breadth = _breadth(cases)
    _extend_minimum_failure(failures, "domains", breadth["domains"], minimums.domains)
    _extend_minimum_failure(
        failures,
        "material roles",
        breadth["material_roles"],
        minimums.material_roles,
    )
    _extend_minimum_failure(
        failures,
        "source organizations",
        breadth["source_organizations"],
        minimums.source_organizations,
    )
    return failures


def _extend_minimum_failure(
    failures: list[str],
    label: str,
    actual: int,
    expected: int,
) -> None:
    if actual < expected:
        failures.append(f"{label} must be at least {expected}; found {actual}")


def _source_reference(reference: str) -> str:
    return reference.split("#", 1)[0]


def _breadth(cases: GeneratedCases) -> dict[str, int]:
    domains = {
        case.domain
        for case in (
            *cases.retrieval,
            *cases.material_roles,
            *cases.document_understanding,
        )
    }
    material_roles = {case.expected_material_role for case in cases.material_roles}
    source_organizations = {
        case.source_organization
        for case in (
            *cases.retrieval,
            *cases.material_roles,
            *cases.document_understanding,
        )
    }
    return {
        "domains": len(domains),
        "material_roles": len(material_roles),
        "source_organizations": len(source_organizations),
    }


def _render_artifacts(cases: GeneratedCases) -> dict[str, str]:
    return {
        _RAG_CASES_FILE: _jsonl(cases.retrieval),
        _MATERIAL_ROLE_CASES_FILE: _jsonl(cases.material_roles),
        _DOCUMENT_UNDERSTANDING_CASES_FILE: _jsonl(cases.document_understanding),
    }


def _jsonl(items: Sequence[object]) -> str:
    return "".join(_json_line(item) + "\n" for item in items)


def _json_line(item: object) -> str:
    return json.dumps(
        _dataclass_dict(item),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _dataclass_dict(item: object) -> dict[str, object]:
    if not is_dataclass(item):
        raise TypeError("expected dataclass instance")
    return cast("dict[str, object]", asdict(item))


def _target_paths(output_dir: Path) -> dict[str, Path]:
    return {
        _RAG_CASES_FILE: output_dir / _RAG_CASES_FILE,
        _MATERIAL_ROLE_CASES_FILE: output_dir / _MATERIAL_ROLE_CASES_FILE,
        _DOCUMENT_UNDERSTANDING_CASES_FILE: output_dir / _DOCUMENT_UNDERSTANDING_CASES_FILE,
        _READINESS_REPORT_FILE: output_dir / _READINESS_REPORT_FILE,
    }


def _prepare_output_paths(target_paths: dict[str, Path], *, overwrite: bool) -> None:
    output_dir = next(iter(target_paths.values())).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = tuple(path for path in target_paths.values() if path.exists())
    if existing and not overwrite:
        paths = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"generated case output exists; pass --overwrite: {paths}")


def _readiness_report(
    *,
    manifest_path: Path,
    armory_path: Path,
    provenance_path: Path,
    output_dir: Path,
    manifest_sha256: str,
    documents: Sequence[PublicAcademicDocument],
    cases: GeneratedCases,
    deterministic_status: str,
    failures: tuple[str, ...],
) -> ReadinessReport:
    target_paths = _target_paths(output_dir)
    return ReadinessReport(
        schema_version=1,
        status="failed" if failures else "passed",
        benchmark_ready=not failures,
        manifest_path=str(manifest_path),
        armory_path=str(armory_path),
        provenance_path=str(provenance_path),
        output_dir=str(output_dir),
        manifest_sha256=manifest_sha256,
        manifest_document_count=len(documents),
        materialized_file_count=len(documents) if not failures else 0,
        safety_checks_status="passed" if not failures else "failed",
        hash_verification_status="passed" if not failures else "failed",
        byte_verification_status="passed" if not failures else "failed",
        provenance_status="passed" if not failures else "failed",
        deterministic_serialization_status=deterministic_status,
        case_counts_by_type={
            "document_understanding": len(cases.document_understanding),
            "material_role": len(cases.material_roles),
            "retrieval": len(cases.retrieval),
        },
        breadth=_breadth(cases),
        near_miss_retrieval_cases=sum(
            1 for case in cases.retrieval if case.forbidden_before_expected
        ),
        generated_files={
            "document_understanding": str(target_paths[_DOCUMENT_UNDERSTANDING_CASES_FILE]),
            "material_roles": str(target_paths[_MATERIAL_ROLE_CASES_FILE]),
            "rag": str(target_paths[_RAG_CASES_FILE]),
            "readiness_report": str(target_paths[_READINESS_REPORT_FILE]),
        },
        failures=failures,
    )


def _readiness_report_json(report: ReadinessReport) -> str:
    return json.dumps(asdict(report), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def print_text_report(report: ReadinessReport) -> None:
    print(f"Public academic benchmark cases: {report.status}")
    print(f"manifest={report.manifest_path}")
    print(f"armory={report.armory_path}")
    print(f"output_dir={report.output_dir}")
    print(f"benchmark_ready={str(report.benchmark_ready).lower()}")
    print(
        "cases="
        f"retrieval:{report.case_counts_by_type.get('retrieval', 0)} "
        f"material_role:{report.case_counts_by_type.get('material_role', 0)} "
        "document_understanding:"
        f"{report.case_counts_by_type.get('document_understanding', 0)}"
    )
    print(
        "breadth="
        f"domains:{report.breadth.get('domains', 0)} "
        f"material_roles:{report.breadth.get('material_roles', 0)} "
        f"source_organizations:{report.breadth.get('source_organizations', 0)}"
    )
    print(f"near_miss_retrieval_cases={report.near_miss_retrieval_cases}")
    if report.failures:
        print("failures:")
        for failure in report.failures:
            print(f"  - {failure}")


def _load_json_object(path: Path) -> dict[str, object]:
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"could not read JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON file: {path}") from exc
    if not isinstance(payload, dict):
        raise TypeError(f"JSON file must contain an object: {path}")
    return cast("dict[str, object]", payload)


def _object_list(mapping: dict[str, object], key: str) -> list[dict[str, object]]:
    value = mapping.get(key)
    if not isinstance(value, list):
        raise TypeError(f"{key} must be a list")
    result: list[dict[str, object]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise TypeError(f"{key} item {index} must be an object")
        result.append(cast("dict[str, object]", item))
    return result


def _required_string(mapping: dict[str, object], key: str, label: str) -> str:
    value = _string_field(mapping, key)
    if not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _required_positive_int(mapping: dict[str, object], key: str, label: str) -> int:
    value = _positive_int_field(mapping, key)
    if value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


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


def _positive_int_field(mapping: dict[str, object], key: str) -> int:
    value = mapping.get(key)
    if isinstance(value, int) and value > 0:
        return value
    return 0


def _bool_field(mapping: dict[str, object], key: str) -> bool | None:
    value = mapping.get(key)
    if isinstance(value, bool):
        return value
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _failure_report(
    *,
    manifest_path: Path,
    armory_path: Path,
    output_dir: Path,
    failure: str,
) -> ReadinessReport:
    manifest = manifest_path.expanduser().resolve()
    armory = armory_path.expanduser().resolve()
    output = output_dir.expanduser().resolve()
    return ReadinessReport(
        schema_version=1,
        status="failed",
        benchmark_ready=False,
        manifest_path=str(manifest),
        armory_path=str(armory),
        provenance_path=str(armory / storage.INTERNAL_DIR / _PROVENANCE_METADATA_NAME),
        output_dir=str(output),
        manifest_sha256=_maybe_sha256(manifest),
        manifest_document_count=0,
        materialized_file_count=0,
        safety_checks_status="failed",
        hash_verification_status="failed",
        byte_verification_status="failed",
        provenance_status="failed",
        deterministic_serialization_status="not-run",
        case_counts_by_type={
            "document_understanding": 0,
            "material_role": 0,
            "retrieval": 0,
        },
        breadth={
            "domains": 0,
            "material_roles": 0,
            "source_organizations": 0,
        },
        near_miss_retrieval_cases=0,
        generated_files={
            "document_understanding": str(output / _DOCUMENT_UNDERSTANDING_CASES_FILE),
            "material_roles": str(output / _MATERIAL_ROLE_CASES_FILE),
            "rag": str(output / _RAG_CASES_FILE),
            "readiness_report": str(output / _READINESS_REPORT_FILE),
        },
        failures=(failure,),
    )


def _maybe_sha256(path: Path) -> str:
    try:
        return _sha256(path)
    except OSError:
        return ""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Public academic manifest JSON")
    parser.add_argument("armory", type=Path, help="Materialized public academic armory")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for cases")
    parser.add_argument("--overwrite", action="store_true", help="Replace generated outputs")
    parser.add_argument("--json-report", type=Path, help="Optional readiness report path")
    parser.add_argument("--min-retrieval-cases", type=int, default=25)
    parser.add_argument("--min-material-role-cases", type=int, default=15)
    parser.add_argument("--min-document-understanding-cases", type=int, default=10)
    parser.add_argument("--min-domains", type=int, default=3)
    parser.add_argument("--min-material-roles", type=int, default=4)
    parser.add_argument("--min-source-organizations", type=int, default=3)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    minimums = CaseGenerationMinimums(
        retrieval_cases=cast("int", args.min_retrieval_cases),
        material_role_cases=cast("int", args.min_material_role_cases),
        document_understanding_cases=cast("int", args.min_document_understanding_cases),
        domains=cast("int", args.min_domains),
        material_roles=cast("int", args.min_material_roles),
        source_organizations=cast("int", args.min_source_organizations),
    )
    manifest = cast("Path", args.manifest)
    armory = cast("Path", args.armory)
    output_dir = cast("Path", args.output_dir)
    json_report = cast("Path | None", args.json_report)
    try:
        report = generate_cases(
            manifest,
            armory,
            output_dir,
            minimums=minimums,
            overwrite=cast("bool", args.overwrite),
        )
    except (OSError, TypeError, ValueError) as exc:
        report = _failure_report(
            manifest_path=manifest,
            armory_path=armory,
            output_dir=output_dir,
            failure=str(exc),
        )
        print_text_report(report)
        if json_report is not None:
            _write_json_report(json_report, report)
        return 2
    print_text_report(report)
    if json_report is not None:
        _write_json_report(json_report, report)
    return 0


def _write_json_report(path: Path, report: ReadinessReport) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_readiness_report_json(report), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
