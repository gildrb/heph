"""Convert standard RAG QA manifests into Heph benchmark armories."""

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
    metadata_from_mapping,
    numeric_grade,
    optional_str,
    print_status,
    required_str,
    write_report,
)

_ADAPTER = "standard-rag"
_DEFAULT_TOP_K = 5
_DEFAULT_SPLIT = "default"
_DEFAULT_DOMAIN = "standard-rag"
_DEFAULT_TASK_TYPE = "question-answering"
_NAMED_DATASETS = frozenset({"ms-marco", "natural-questions"})


def convert_standard_rag_dataset(
    dataset: str,
    output_dir: Path,
    *,
    manifest_path: Path | None,
    split: str = "",
    domain: str = "",
    task_type: str = "",
    positive_threshold: float = 1.0,
    top_k: int = _DEFAULT_TOP_K,
    overwrite: bool = False,
) -> dict[str, object]:
    """Load a standard RAG manifest and write a Heph benchmark suite."""
    output = ensure_output_available(output_dir, overwrite=overwrite)
    if manifest_path is None:
        _raise_missing_named_dataset(dataset)
    manifest = _read_manifest(cast("Path", manifest_path))
    manifest_dataset = optional_str(manifest.get("dataset")) or dataset
    manifest_split = split or optional_str(manifest.get("split")) or _DEFAULT_SPLIT
    manifest_domain = domain or optional_str(manifest.get("domain")) or _DEFAULT_DOMAIN
    manifest_task_type = task_type or optional_str(manifest.get("task_type")) or _DEFAULT_TASK_TYPE
    documents = tuple(_load_documents(manifest))
    queries, judgments = _load_queries_and_judgments(manifest)
    conversion = ConversionInput(
        adapter=_ADAPTER,
        dataset=manifest_dataset,
        source_format="standard-rag-manifest",
        input_source=str(cast("Path", manifest_path).expanduser().resolve()),
        split=manifest_split,
        domain=manifest_domain,
        task_type=manifest_task_type,
        documents=documents,
        queries=tuple(queries),
        judgments=tuple(judgments),
        top_k=top_k,
        positive_threshold=positive_threshold,
        cache=CacheInfo(enabled=False, path="", used=False),
    )
    return convert_dataset(conversion, output, overwrite=overwrite)


def _raise_missing_named_dataset(dataset: str) -> None:
    if dataset in _NAMED_DATASETS:
        raise AdapterError(
            "dataset_requires_manifest",
            f"{dataset} requires an explicit local manifest for deterministic conversion",
            "Pass --manifest pointing to a reviewed local QA/source manifest.",
        )
    supported = ", ".join(sorted(_NAMED_DATASETS))
    raise AdapterError(
        "unsupported_dataset",
        f"unsupported standard RAG dataset: {dataset}",
        f"Pass --manifest for a custom dataset or choose one of: {supported}.",
    )


def _read_manifest(path: Path) -> dict[str, object]:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise AdapterError(
            "input_not_found",
            f"standard RAG manifest does not exist: {resolved}",
            "Pass --manifest with an existing JSON manifest.",
        )
    try:
        raw = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AdapterError(
            "malformed_input",
            f"standard RAG manifest contains invalid JSON at line {exc.lineno}",
            "Fix the manifest JSON syntax and rerun the adapter.",
        ) from exc
    if not isinstance(raw, dict):
        raise AdapterError(
            "malformed_input",
            "standard RAG manifest must be a JSON object",
            "Use an object with documents plus queries or qa_pairs.",
        )
    return cast("dict[str, object]", raw)


def _load_documents(manifest: dict[str, object]) -> list[ExternalDocument]:
    raw_documents = manifest.get("documents")
    if not isinstance(raw_documents, list) or not raw_documents:
        raise AdapterError(
            "malformed_input",
            "standard RAG manifest must include non-empty documents",
            "Add a documents array with id and text/content fields.",
        )
    documents: list[ExternalDocument] = []
    for index, raw_document in enumerate(raw_documents, start=1):
        if not isinstance(raw_document, dict):
            raise AdapterError(
                "malformed_input",
                f"document {index} must be a JSON object",
                "Use document objects with id and text/content fields.",
            )
        document = cast("dict[str, object]", raw_document)
        context = f"document {index}"
        document_id = required_str(
            document.get("id") or document.get("document_id"),
            field_name="id",
            context=context,
        )
        text = _document_text(document, context=context)
        title = optional_str(document.get("title"))
        source_url = optional_str(document.get("source_url") or document.get("url"))
        metadata = metadata_from_mapping(
            document,
            exclude=frozenset(
                {"id", "document_id", "text", "content", "body", "title", "source_url", "url"}
            ),
        )
        documents.append(
            ExternalDocument(
                original_id=document_id,
                title=title,
                text=text,
                metadata=metadata,
                source_url=source_url or None,
            )
        )
    return documents


def _document_text(document: dict[str, object], *, context: str) -> str:
    for field_name in ("text", "content", "body"):
        text = optional_str(document.get(field_name))
        if text:
            return text
    raise AdapterError(
        "malformed_input",
        f"{context} must include text, content, or body",
        "Provide non-empty source document text.",
    )


def _load_queries_and_judgments(
    manifest: dict[str, object],
) -> tuple[list[ExternalQuery], list[RelevanceJudgment]]:
    raw_queries = manifest.get("queries")
    query_field_name = "queries"
    if raw_queries is None:
        raw_queries = manifest.get("qa_pairs")
        query_field_name = "qa_pairs"
    if not isinstance(raw_queries, list) or not raw_queries:
        raise AdapterError(
            "malformed_input",
            "standard RAG manifest must include non-empty queries or qa_pairs",
            "Add queries with question/query text and relevant_documents/source_documents.",
        )
    queries: list[ExternalQuery] = []
    judgments: list[RelevanceJudgment] = []
    for index, raw_query in enumerate(raw_queries, start=1):
        if not isinstance(raw_query, dict):
            raise AdapterError(
                "malformed_input",
                f"{query_field_name} item {index} must be a JSON object",
                "Use query objects with id, question/query, and relevance annotations.",
            )
        query = cast("dict[str, object]", raw_query)
        context = f"{query_field_name} item {index}"
        query_id = _query_id(query, index=index)
        query_text = _query_text(query, context=context)
        answers = _answers(query)
        metadata = metadata_from_mapping(
            query,
            exclude=frozenset(
                {
                    "id",
                    "query_id",
                    "question",
                    "query",
                    "answer",
                    "answers",
                    "relevant_documents",
                    "relevance",
                    "source_documents",
                    "sources",
                }
            ),
        )
        relevance_rows = _relevance_rows(query, context=context)
        queries.append(
            ExternalQuery(
                original_id=query_id,
                text=query_text,
                answers=answers,
                metadata=metadata,
            )
        )
        judgments.extend(
            RelevanceJudgment(
                query_id=query_id,
                document_id=document_id,
                grade=grade,
                metadata={"source": source_name},
            )
            for document_id, grade, source_name in relevance_rows
        )
    return queries, judgments


def _query_id(query: dict[str, object], *, index: int) -> str:
    raw_id = optional_str(query.get("id") or query.get("query_id"))
    return raw_id or f"query-{index}"


def _query_text(query: dict[str, object], *, context: str) -> str:
    text = optional_str(query.get("question")) or optional_str(query.get("query"))
    if text:
        return text
    raise AdapterError(
        "malformed_input",
        f"{context} must include question or query text",
        "Add a non-empty question or query field.",
    )


def _answers(query: dict[str, object]) -> tuple[str, ...]:
    raw_answers = query.get("answers")
    raw_answer = query.get("answer")
    if isinstance(raw_answers, list):
        answers = tuple(
            item.strip() for item in raw_answers if isinstance(item, str) and item.strip()
        )
        if answers:
            return answers
    if isinstance(raw_answer, str) and raw_answer.strip():
        return (raw_answer.strip(),)
    return ()


def _relevance_rows(
    query: dict[str, object],
    *,
    context: str,
) -> list[tuple[str, float, str]]:
    for field_name in ("relevant_documents", "relevance", "source_documents", "sources"):
        raw_relevance = query.get(field_name)
        if raw_relevance is None:
            continue
        return _parse_relevance(raw_relevance, context=context, source_name=field_name)
    raise AdapterError(
        "malformed_input",
        f"{context} must include relevance annotations",
        "Add relevant_documents, relevance, source_documents, or sources.",
    )


def _parse_relevance(
    raw_relevance: object,
    *,
    context: str,
    source_name: str,
) -> list[tuple[str, float, str]]:
    if isinstance(raw_relevance, dict):
        rows: list[tuple[str, float, str]] = []
        for document_id in sorted(raw_relevance):
            if not isinstance(document_id, str):
                continue
            grade = numeric_grade(raw_relevance[document_id], context=context)
            rows.append((document_id, grade, source_name))
        if rows:
            return rows
    if isinstance(raw_relevance, list):
        rows = []
        for index, item in enumerate(raw_relevance, start=1):
            rows.append(
                _parse_relevance_item(
                    item, context=f"{context} relevance {index}", source_name=source_name
                )
            )
        if rows:
            return rows
    raise AdapterError(
        "malformed_input",
        f"{context} relevance annotations are empty or malformed",
        "Use document IDs, {document_id: grade}, or objects with id/document_id and grade.",
    )


def _parse_relevance_item(
    item: object,
    *,
    context: str,
    source_name: str,
) -> tuple[str, float, str]:
    if isinstance(item, str) and item.strip():
        return item.strip(), 1.0, source_name
    if isinstance(item, dict):
        row = cast("dict[str, object]", item)
        document_id = required_str(
            row.get("id") or row.get("document_id") or row.get("source_id"),
            field_name="document_id",
            context=context,
        )
        grade = numeric_grade(
            _first_present(row, ("grade", "score", "relevance")), context=context, default=1.0
        )
        return document_id, grade, source_name
    raise AdapterError(
        "malformed_input",
        f"{context} must be a document ID string or relevance object",
        "Use document IDs or objects with document_id and grade.",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", help="Dataset id, for example ms-marco or natural-questions")
    parser.add_argument("--manifest", type=Path, help="Local standard RAG JSON manifest")
    parser.add_argument("--output", required=True, type=Path, help="Output benchmark suite dir")
    parser.add_argument("--split", default="")
    parser.add_argument("--domain", default="")
    parser.add_argument("--task-type", default="")
    parser.add_argument("--positive-threshold", type=float, default=1.0)
    parser.add_argument("--top-k", type=int, default=_DEFAULT_TOP_K)
    parser.add_argument("--json-report", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    dataset = cast("str", args.dataset)
    output = cast("Path", args.output)
    json_report = cast("Path | None", args.json_report)
    try:
        report = convert_standard_rag_dataset(
            dataset,
            output,
            manifest_path=cast("Path | None", args.manifest),
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
            dataset=dataset,
            input_source=_input_source_for_error(args),
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
            "Rerun with a small manifest and report this issue if it persists.",
        )
        report = build_error_report(
            adapter=_ADAPTER,
            dataset=dataset,
            input_source=_input_source_for_error(args),
            output_dir=output,
            error=error,
        )
        write_report(json_report, report)
        print_status(report, error=True)
        return 2
    write_report(json_report, report)
    print_status(report)
    return 0


def _input_source_for_error(args: argparse.Namespace) -> str:
    raw_manifest = args.manifest
    if isinstance(raw_manifest, Path):
        return str(raw_manifest)
    raw_dataset = args.dataset
    return str(raw_dataset)


def _first_present(row: dict[str, object], keys: tuple[str, ...]) -> object | None:
    for key in keys:
        if key in row:
            return row[key]
    return None


if __name__ == "__main__":
    raise SystemExit(main())
