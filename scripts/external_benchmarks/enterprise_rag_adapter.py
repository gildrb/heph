"""Convert EnterpriseRAG-Bench into a Heph benchmark suite.

EnterpriseRAG-Bench is an official large-scale RAG benchmark with 500k+
enterprise-style documents and 500 questions. This adapter expects a local
checkout or extracted dataset containing ``questions.jsonl`` and
``generated_data/sources``. It preserves the original ``dsid_...`` document
identifiers in metadata so Heph retrieval can be exported to the
leaderboard answer format without weakening the benchmark.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

from scripts.external_benchmarks.conversion import (
    AdapterError,
    CacheInfo,
    ConversionInput,
    ExternalDocument,
    ExternalQuery,
    RelevanceJudgment,
    build_error_report,
    convert_dataset,
    ensure_output_available,
    optional_str,
    print_status,
    required_str,
    write_report,
)

_ADAPTER = "enterprise-rag"
_DATASET = "enterprise-rag-bench"
_SOURCE_FORMAT = "enterprise-rag-json-sources"
_DEFAULT_SPLIT = "test"
_DEFAULT_DOMAIN = "enterprise-rag"
_DEFAULT_TASK_TYPE = "enterprise-question-answering"
_DEFAULT_TOP_K = 10


def convert_enterprise_rag_dataset(
    source_dir: Path,
    output_dir: Path,
    *,
    split: str = _DEFAULT_SPLIT,
    domain: str = _DEFAULT_DOMAIN,
    task_type: str = _DEFAULT_TASK_TYPE,
    positive_threshold: float = 1.0,
    top_k: int = _DEFAULT_TOP_K,
    overwrite: bool = False,
) -> dict[str, object]:
    """Load a local EnterpriseRAG-Bench checkout and write a Heph benchmark suite."""
    output = ensure_output_available(output_dir, overwrite=overwrite)
    root = source_dir.expanduser().resolve()
    questions_path = root / "questions.jsonl"
    sources_dir = root / "generated_data" / "sources"
    _validate_source_paths(root, questions_path, sources_dir)

    documents, document_ids_by_official_id, duplicate_document_count = _load_documents(sources_dir)
    queries, judgments, skipped_without_expected = _load_queries_and_judgments(
        questions_path,
        document_ids_by_official_id=document_ids_by_official_id,
    )
    conversion = ConversionInput(
        adapter=_ADAPTER,
        dataset=_DATASET,
        source_format=_SOURCE_FORMAT,
        input_source=str(root),
        split=split or _DEFAULT_SPLIT,
        domain=domain or _DEFAULT_DOMAIN,
        task_type=task_type or _DEFAULT_TASK_TYPE,
        documents=tuple(documents),
        queries=tuple(queries),
        judgments=tuple(judgments),
        top_k=top_k,
        positive_threshold=positive_threshold,
        cache=CacheInfo(enabled=False, path="", used=False),
        warnings=_conversion_warnings(
            skipped_without_expected,
            duplicate_document_count=duplicate_document_count,
        ),
    )
    return convert_dataset(conversion, output, overwrite=overwrite)


def _validate_source_paths(root: Path, questions_path: Path, sources_dir: Path) -> None:
    if not root.is_dir():
        raise AdapterError(
            "input_not_found",
            f"EnterpriseRAG source directory does not exist: {root}",
            "Clone EnterpriseRAG-Bench or pass a local extracted dataset directory.",
        )
    if not questions_path.is_file():
        raise AdapterError(
            "missing_questions",
            f"EnterpriseRAG questions file not found: {questions_path}",
            "Use a source directory containing questions.jsonl.",
        )
    if not sources_dir.is_dir():
        raise AdapterError(
            "missing_sources",
            f"EnterpriseRAG sources directory not found: {sources_dir}",
            "Use a source directory containing generated_data/sources.",
        )


def _load_documents(
    sources_dir: Path,
) -> tuple[list[ExternalDocument], dict[str, tuple[str, ...]], int]:
    documents: list[ExternalDocument] = []
    document_ids_by_official_id: dict[str, list[str]] = {}
    for path in sorted(sources_dir.rglob("*.json")):
        raw = _read_json_object(path)
        context = f"document {path.relative_to(sources_dir)}"
        official_document_id = required_str(
            raw.get("dataset_doc_uuid"),
            field_name="dataset_doc_uuid",
            context=context,
        )
        internal_document_id = _internal_document_id(
            official_document_id,
            duplicate_index=len(document_ids_by_official_id.get(official_document_id, [])),
        )
        document_ids_by_official_id.setdefault(official_document_id, []).append(
            internal_document_id
        )
        title_field, content_fields, title, text, empty_content = _extract_document_content(
            raw,
            context=context,
        )
        relative_path = path.relative_to(sources_dir)
        source_type = relative_path.parts[0] if relative_path.parts else ""
        metadata = _metadata_from_enterprise_mapping(
            raw,
            exclude=frozenset(
                {
                    "dataset_doc_uuid",
                    "title_field_name",
                    "content_field_names",
                    title_field,
                    *content_fields,
                }
            ),
        )
        metadata["enterprise_rag_source_path"] = relative_path.as_posix()
        metadata["enterprise_rag_document_id"] = official_document_id
        if internal_document_id != official_document_id:
            metadata["enterprise_rag_duplicate_document"] = True
        if empty_content:
            metadata["enterprise_rag_empty_content"] = True
        if source_type:
            metadata["source_type"] = source_type
        documents.append(
            ExternalDocument(
                original_id=internal_document_id,
                title=title,
                text=text,
                metadata=metadata,
                source_path=relative_path.with_suffix(".md").as_posix(),
            )
        )
    if not documents:
        raise AdapterError(
            "empty_sources",
            f"EnterpriseRAG sources directory contains no JSON documents: {sources_dir}",
            "Use the official generated_data/sources directory.",
        )
    duplicate_document_count = sum(
        len(internal_ids) - 1
        for internal_ids in document_ids_by_official_id.values()
        if len(internal_ids) > 1
    )
    return (
        documents,
        {
            official_id: tuple(internal_ids)
            for official_id, internal_ids in document_ids_by_official_id.items()
        },
        duplicate_document_count,
    )


def _internal_document_id(official_document_id: str, *, duplicate_index: int) -> str:
    if duplicate_index == 0:
        return official_document_id
    return f"{official_document_id}__enterprise_duplicate_{duplicate_index + 1}"


def _read_json_object(path: Path) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AdapterError(
            "malformed_input",
            f"EnterpriseRAG JSON document is malformed at line {exc.lineno}: {path}",
            "Use the official dataset files or fix the malformed JSON document.",
        ) from exc
    if not isinstance(raw, dict):
        raise AdapterError(
            "malformed_input",
            f"EnterpriseRAG JSON document must be an object: {path}",
            "Use the official dataset files.",
        )
    return cast("dict[str, object]", raw)


def _extract_document_content(
    document: dict[str, object],
    *,
    context: str,
) -> tuple[str, tuple[str, ...], str, str, bool]:
    title_field = required_str(
        document.get("title_field_name"),
        field_name="title_field_name",
        context=context,
    )
    if title_field not in document:
        raise AdapterError(
            "malformed_input",
            f"{context} title field {title_field!r} is missing",
            "Use the official EnterpriseRAG source JSON files.",
        )
    raw_content_fields = document.get("content_field_names")
    if not isinstance(raw_content_fields, list) or not raw_content_fields:
        raise AdapterError(
            "malformed_input",
            f"{context} must include non-empty content_field_names",
            "Use the official EnterpriseRAG source JSON files.",
        )
    title = str(document[title_field]).strip()
    content_fields: list[str] = []
    content_parts: list[str] = []
    for raw_field in raw_content_fields:
        if not isinstance(raw_field, str) or raw_field not in document:
            raise AdapterError(
                "malformed_input",
                f"{context} has an invalid content field reference",
                "Use source JSON with valid content_field_names.",
            )
        content_fields.append(raw_field)
        if len(raw_content_fields) == 1:
            content_parts.append(str(document[raw_field]))
        else:
            value = document[raw_field]
            if isinstance(value, list):
                value_text = "\n".join(str(item) for item in value)
            else:
                value_text = str(value)
            content_parts.append(f"{raw_field}:\n{value_text}")
    text = "\n\n".join(part.strip() for part in content_parts if part.strip())
    empty_content = not text
    if empty_content:
        text = "[Empty EnterpriseRAG content]"
    return title_field, tuple(content_fields), title, text, empty_content


def _load_queries_and_judgments(
    questions_path: Path,
    *,
    document_ids_by_official_id: dict[str, tuple[str, ...]],
) -> tuple[list[ExternalQuery], list[RelevanceJudgment], int]:
    queries: list[ExternalQuery] = []
    judgments: list[RelevanceJudgment] = []
    skipped_without_expected = 0
    for line_number, line in enumerate(questions_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AdapterError(
                "malformed_input",
                f"questions.jsonl contains invalid JSON at line {line_number}",
                "Use the official EnterpriseRAG questions.jsonl file.",
            ) from exc
        if not isinstance(raw, dict):
            raise AdapterError(
                "malformed_input",
                f"questions.jsonl line {line_number} must be a JSON object",
                "Use the official EnterpriseRAG questions.jsonl file.",
            )
        row = cast("dict[str, object]", raw)
        query_id = required_str(row.get("question_id"), field_name="question_id", context="query")
        question = required_str(row.get("question"), field_name="question", context=query_id)
        expected_doc_ids = _expected_doc_ids(
            row,
            query_id,
            document_ids_by_official_id=document_ids_by_official_id,
        )
        if not expected_doc_ids:
            skipped_without_expected += 1
            continue
        queries.append(
            ExternalQuery(
                original_id=query_id,
                text=question,
                answers=_answers(row),
                metadata=_metadata_from_enterprise_mapping(
                    row,
                    exclude=frozenset(
                        {
                            "question_id",
                            "question",
                            "expected_doc_ids",
                            "gold_answer",
                            "answer_facts",
                        }
                    ),
                ),
            )
        )
        judgments.extend(
            RelevanceJudgment(
                query_id=query_id,
                document_id=document_id,
                grade=1.0,
                metadata={"source": "expected_doc_ids"},
            )
            for document_id in expected_doc_ids
        )
    if not queries:
        raise AdapterError(
            "empty_questions",
            "EnterpriseRAG questions produced no retrieval-labelled benchmark cases",
            "Use questions.jsonl with expected_doc_ids entries.",
        )
    return queries, judgments, skipped_without_expected


def _conversion_warnings(
    skipped_without_expected: int,
    *,
    duplicate_document_count: int,
) -> tuple[str, ...]:
    warnings: list[str] = []
    if skipped_without_expected:
        warnings.append(f"{skipped_without_expected} question(s) without expected_doc_ids skipped")
    if duplicate_document_count:
        warnings.append(
            f"{duplicate_document_count} duplicate dataset_doc_uuid document(s) preserved "
            "with stable internal ids"
        )
    return tuple(warnings)


def _metadata_from_enterprise_mapping(
    raw: dict[str, object],
    *,
    exclude: frozenset[str],
) -> dict[str, object]:
    metadata: dict[str, object] = {}
    raw_metadata = raw.get("metadata")
    if isinstance(raw_metadata, dict):
        metadata.update(
            {key: value for key, value in raw_metadata.items() if isinstance(key, str)}
        )
    elif raw_metadata is not None and "metadata" not in exclude:
        metadata["metadata"] = raw_metadata
    for key in sorted(raw):
        if key in exclude or key == "metadata":
            continue
        metadata[key] = raw[key]
    return metadata


def _expected_doc_ids(
    row: dict[str, object],
    query_id: str,
    *,
    document_ids_by_official_id: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    raw_expected = row.get("expected_doc_ids")
    if raw_expected is None:
        return ()
    if not isinstance(raw_expected, list):
        raise AdapterError(
            "malformed_input",
            f"{query_id} expected_doc_ids must be a list",
            "Use the official EnterpriseRAG questions.jsonl schema.",
        )
    official_ids = tuple(
        item.strip() for item in raw_expected if isinstance(item, str) and item.strip()
    )
    if len(official_ids) != len(raw_expected):
        raise AdapterError(
            "malformed_input",
            f"{query_id} expected_doc_ids must contain only non-empty strings",
            "Use valid dsid_... document identifiers.",
        )
    expected: list[str] = []
    seen: set[str] = set()
    for official_id in official_ids:
        internal_ids = document_ids_by_official_id.get(official_id, (official_id,))
        for internal_id in internal_ids:
            if internal_id in seen:
                continue
            seen.add(internal_id)
            expected.append(internal_id)
    return tuple(expected)


def _answers(row: dict[str, object]) -> tuple[str, ...]:
    answer = optional_str(row.get("gold_answer"))
    return (answer,) if answer else ()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path, help="EnterpriseRAG-Bench checkout root")
    parser.add_argument("--output", required=True, type=Path, help="Output benchmark suite dir")
    parser.add_argument("--split", default=_DEFAULT_SPLIT)
    parser.add_argument("--domain", default=_DEFAULT_DOMAIN)
    parser.add_argument("--task-type", default=_DEFAULT_TASK_TYPE)
    parser.add_argument("--positive-threshold", type=float, default=1.0)
    parser.add_argument("--top-k", type=int, default=_DEFAULT_TOP_K)
    parser.add_argument("--json-report", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    source_dir = cast("Path", args.source_dir)
    output = cast("Path", args.output)
    json_report = cast("Path | None", args.json_report)
    try:
        report = convert_enterprise_rag_dataset(
            source_dir,
            output,
            split=cast("str", args.split),
            domain=cast("str", args.domain),
            task_type=cast("str", args.task_type),
            positive_threshold=cast("float", args.positive_threshold),
            top_k=cast("int", args.top_k),
            overwrite=cast("bool", args.overwrite),
        )
    except AdapterError as exc:
        report = build_error_report(
            adapter=_ADAPTER,
            dataset=_DATASET,
            input_source=str(source_dir),
            output_dir=output,
            error=exc,
        )
        write_report(json_report, report)
        print_status(report, error=True)
        return 2
    except Exception as exc:
        error = AdapterError(
            "unexpected_error",
            f"unexpected adapter failure: {exc}",
            "Rerun with a small fixture and report this issue if it persists.",
        )
        report = build_error_report(
            adapter=_ADAPTER,
            dataset=_DATASET,
            input_source=str(source_dir),
            output_dir=output,
            error=error,
        )
        write_report(json_report, report)
        print_status(report, error=True)
        return 2
    write_report(json_report, report)
    print_status(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
