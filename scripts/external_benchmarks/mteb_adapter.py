"""Convert local MTEB retrieval exports into Heph benchmark armories.

The adapter intentionally handles local, reviewed exports instead of reaching
out to Hugging Face at runtime. MTEB retrieval tasks have a corpus, queries, and
relevant-doc judgments; this module normalizes those files into the same
portable suite shape used by the other external benchmark adapters.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
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

_ADAPTER = "mteb"
_DEFAULT_TOP_K = 10
_DEFAULT_SPLIT = "test"
_DEFAULT_SUBSET = "default"
_DEFAULT_DOMAIN = "mteb-retrieval"
_DEFAULT_TASK_TYPE = "retrieval"
_SOURCE_FORMAT = "mteb-retrieval-local"


@dataclass(frozen=True, slots=True)
class MtebFiles:
    """Resolved local files for one MTEB retrieval split."""

    corpus: Path
    queries: Path
    relevant_docs: Path


def convert_mteb_dataset(
    dataset: str,
    output_dir: Path,
    *,
    source_dir: Path | None = None,
    corpus_file: Path | None = None,
    queries_file: Path | None = None,
    relevance_file: Path | None = None,
    split: str = _DEFAULT_SPLIT,
    subset: str = _DEFAULT_SUBSET,
    domain: str = _DEFAULT_DOMAIN,
    task_type: str = _DEFAULT_TASK_TYPE,
    positive_threshold: float = 1.0,
    top_k: int = _DEFAULT_TOP_K,
    overwrite: bool = False,
) -> dict[str, object]:
    """Load a local MTEB retrieval export and write a Heph benchmark suite."""
    output = ensure_output_available(output_dir, overwrite=overwrite)
    dataset_name = _mteb_name(dataset)
    files = _resolve_mteb_files(
        source_dir=source_dir,
        corpus_file=corpus_file,
        queries_file=queries_file,
        relevance_file=relevance_file,
        split=split,
    )
    documents = tuple(_load_corpus(files.corpus))
    queries = tuple(_load_queries(files.queries))
    judgments = tuple(_load_relevance(files.relevant_docs))
    conversion = ConversionInput(
        adapter=_ADAPTER,
        dataset=_dataset_identifier(dataset_name),
        source_format=_SOURCE_FORMAT,
        input_source=_input_source(files, source_dir=source_dir),
        split=split,
        domain=domain,
        task_type=task_type,
        documents=documents,
        queries=queries,
        judgments=judgments,
        top_k=top_k,
        positive_threshold=positive_threshold,
        cache=CacheInfo(enabled=False, path="", used=False),
        warnings=_conversion_warnings(subset=subset, files=files),
    )
    return convert_dataset(conversion, output, overwrite=overwrite)


def _mteb_name(dataset: str) -> str:
    raw = dataset.strip()
    if raw.startswith("mteb/"):
        raw = raw.removeprefix("mteb/")
    if not raw:
        raise AdapterError(
            "unsupported_dataset",
            "MTEB dataset identifier is empty",
            "Use a dataset identifier such as mteb/SciFact.",
        )
    return raw


def _dataset_identifier(dataset_name: str) -> str:
    return f"mteb/{dataset_name}"


def _resolve_mteb_files(
    *,
    source_dir: Path | None,
    corpus_file: Path | None,
    queries_file: Path | None,
    relevance_file: Path | None,
    split: str,
) -> MtebFiles:
    explicit_files = tuple(
        path for path in (corpus_file, queries_file, relevance_file) if path is not None
    )
    if source_dir is not None and explicit_files:
        raise AdapterError(
            "invalid_option",
            "choose either --source-dir or explicit --corpus-file/--queries-file/--relevance-file",
            "Use one deterministic input style for the MTEB adapter.",
        )
    if source_dir is not None:
        return _discover_mteb_files(source_dir.expanduser().resolve(), split=split)
    if corpus_file is None or queries_file is None or relevance_file is None:
        raise AdapterError(
            "missing_input",
            "MTEB conversion requires --source-dir or all three explicit input files",
            "Pass --source-dir with local JSONL/TSV exports, or pass --corpus-file, "
            "--queries-file, and --relevance-file.",
        )
    return MtebFiles(
        corpus=_existing_file(corpus_file, label="MTEB corpus"),
        queries=_existing_file(queries_file, label="MTEB queries"),
        relevant_docs=_existing_file(relevance_file, label="MTEB relevant_docs"),
    )


def _discover_mteb_files(source_dir: Path, *, split: str) -> MtebFiles:
    if not source_dir.exists():
        raise AdapterError(
            "input_not_found",
            f"MTEB source directory does not exist: {source_dir}",
            "Export the retrieval task locally or pass explicit input files.",
        )
    if not source_dir.is_dir():
        raise AdapterError(
            "input_not_directory",
            f"MTEB source path is not a directory: {source_dir}",
            "Use --corpus-file/--queries-file/--relevance-file for individual files.",
        )
    return MtebFiles(
        corpus=_discover_file(source_dir, _corpus_candidates(source_dir), label="MTEB corpus"),
        queries=_discover_file(
            source_dir,
            _query_candidates(source_dir, split),
            label="MTEB queries",
        ),
        relevant_docs=_discover_file(
            source_dir,
            _relevance_candidates(source_dir, split),
            label="MTEB relevant_docs",
        ),
    )


def _corpus_candidates(source_dir: Path) -> tuple[Path, ...]:
    return _dedupe_paths(
        (
            source_dir / "corpus.jsonl",
            source_dir / "corpus" / "corpus.jsonl",
            *sorted((source_dir / "corpus").glob("corpus*.jsonl")),
            *sorted((source_dir / "corpus").glob("*.jsonl")),
        )
    )


def _query_candidates(source_dir: Path, split: str) -> tuple[Path, ...]:
    return _dedupe_paths(
        (
            source_dir / "queries.jsonl",
            source_dir / "queries" / f"{split}.jsonl",
            source_dir / "queries" / "queries.jsonl",
            source_dir / "queries" / f"queries-{split}.jsonl",
            *sorted((source_dir / "queries").glob("queries*.jsonl")),
            *sorted((source_dir / "queries").glob("*.jsonl")),
        )
    )


def _relevance_candidates(source_dir: Path, split: str) -> tuple[Path, ...]:
    return _dedupe_paths(
        (
            source_dir / "relevant_docs.jsonl",
            source_dir / "qrels" / f"{split}.tsv",
            source_dir / "qrels" / f"{split}.txt",
            source_dir / "relevant_docs" / f"{split}.jsonl",
            source_dir / "data" / f"{split}.jsonl",
            *sorted((source_dir / "data").glob(f"{split}-*.jsonl")),
            *sorted((source_dir / "data").glob(f"{split}*.jsonl")),
        )
    )


def _dedupe_paths(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    seen: set[Path] = set()
    result: list[Path] = []
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        result.append(path)
    return tuple(result)


def _discover_file(source_dir: Path, candidates: tuple[Path, ...], *, label: str) -> Path:
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise AdapterError(
        "input_not_found",
        f"could not find {label} under {source_dir}",
        "Provide JSONL/TSV exports. Parquet Hugging Face shards should be exported "
        "to local JSONL before conversion.",
    )


def _existing_file(path: Path, *, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise AdapterError(
            "input_not_found",
            f"{label} file does not exist: {resolved}",
            "Pass an existing local JSONL or TSV export.",
        )
    return resolved


def _input_source(files: MtebFiles, *, source_dir: Path | None) -> str:
    if source_dir is not None:
        return str(source_dir.expanduser().resolve())
    return ";".join(
        (
            f"corpus={files.corpus}",
            f"queries={files.queries}",
            f"relevant_docs={files.relevant_docs}",
        )
    )


def _conversion_warnings(*, subset: str, files: MtebFiles) -> tuple[str, ...]:
    warnings: list[str] = []
    if subset != _DEFAULT_SUBSET:
        warnings.append(f"subset={subset}")
    if any(
        path.suffix == ".parquet" for path in (files.corpus, files.queries, files.relevant_docs)
    ):
        warnings.append("parquet inputs are not read directly; export to JSONL/TSV first")
    return tuple(warnings)


def _load_corpus(path: Path) -> list[ExternalDocument]:
    rows = _read_jsonl_objects(path, label="MTEB corpus")
    documents: list[ExternalDocument] = []
    for index, raw in enumerate(rows, start=1):
        context = f"MTEB corpus row {index}"
        document_id = required_str(
            _first_present(raw, ("id", "_id", "corpus-id", "corpus_id")),
            field_name="id",
            context=context,
        )
        text = _document_text(raw, context=context)
        title = optional_str(raw.get("title"))
        source_url = optional_str(raw.get("source_url") or raw.get("url"))
        metadata = metadata_from_mapping(
            raw,
            exclude=frozenset(
                {
                    "id",
                    "_id",
                    "corpus-id",
                    "corpus_id",
                    "text",
                    "content",
                    "body",
                    "title",
                    "source_url",
                    "url",
                }
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


def _document_text(raw: dict[str, object], *, context: str) -> str:
    for field_name in ("text", "content", "body"):
        text = optional_str(raw.get(field_name))
        if text:
            return text
    raise AdapterError(
        "malformed_input",
        f"{context} must include non-empty text, content, or body",
        "Export MTEB text retrieval corpora with document text.",
    )


def _load_queries(path: Path) -> list[ExternalQuery]:
    rows = _read_jsonl_objects(path, label="MTEB queries")
    queries: list[ExternalQuery] = []
    for index, raw in enumerate(rows, start=1):
        context = f"MTEB query row {index}"
        query_id = required_str(
            _first_present(raw, ("id", "_id", "query-id", "query_id")),
            field_name="id",
            context=context,
        )
        query_text = _query_text(raw, context=context)
        metadata = metadata_from_mapping(
            raw,
            exclude=frozenset({"id", "_id", "query-id", "query_id", "text", "query"}),
        )
        queries.append(ExternalQuery(original_id=query_id, text=query_text, metadata=metadata))
    return queries


def _query_text(raw: dict[str, object], *, context: str) -> str:
    text = optional_str(raw.get("text")) or optional_str(raw.get("query"))
    instruction = optional_str(raw.get("instruction"))
    if text and instruction:
        return f"{instruction}\n{text}"
    if text:
        return text
    if instruction:
        return instruction
    raise AdapterError(
        "malformed_input",
        f"{context} must include non-empty text, query, or instruction",
        "Export MTEB text retrieval queries with a text/query column.",
    )


def _load_relevance(path: Path) -> list[RelevanceJudgment]:
    if path.suffix in {".tsv", ".txt"}:
        return _load_relevance_tsv(path)
    return _load_relevance_jsonl(path)


def _load_relevance_jsonl(path: Path) -> list[RelevanceJudgment]:
    rows = _read_jsonl_objects(path, label="MTEB relevant_docs")
    judgments: list[RelevanceJudgment] = []
    for index, raw in enumerate(rows, start=1):
        context = f"MTEB relevant_docs row {index}"
        query_id = required_str(
            _first_present(raw, ("query-id", "query_id", "qid", "queryId")),
            field_name="query-id",
            context=context,
        )
        document_id = required_str(
            _first_present(
                raw,
                (
                    "corpus-id",
                    "corpus_id",
                    "docid",
                    "doc_id",
                    "document_id",
                    "corpusId",
                ),
            ),
            field_name="corpus-id",
            context=context,
        )
        grade = numeric_grade(
            _first_present(raw, ("score", "grade", "relevance")),
            context=context,
            default=1.0,
        )
        judgments.append(
            RelevanceJudgment(
                query_id=query_id,
                document_id=document_id,
                grade=grade,
                metadata={"relevant_docs_path": path.name, "line": index},
            )
        )
    return judgments


def _load_relevance_tsv(path: Path) -> list[RelevanceJudgment]:
    judgments: list[RelevanceJudgment] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        normalized = [part.strip() for part in line.replace(",", "\t").split("\t") if part.strip()]
        if line_number == 1 and normalized and normalized[0] in {"query-id", "query_id", "qid"}:
            continue
        if len(normalized) == 3:
            query_id, document_id, raw_grade = normalized
        elif len(normalized) >= 4:
            query_id = normalized[0]
            document_id = normalized[2]
            raw_grade = normalized[3]
        else:
            raise AdapterError(
                "malformed_input",
                f"MTEB relevant_docs line {line_number} must have at least 3 columns",
                "Use columns query-id, corpus-id, score.",
            )
        grade = numeric_grade(raw_grade, context=f"MTEB relevant_docs line {line_number}")
        judgments.append(
            RelevanceJudgment(
                query_id=query_id,
                document_id=document_id,
                grade=grade,
                metadata={"relevant_docs_path": path.name, "line": line_number},
            )
        )
    if not judgments:
        raise AdapterError(
            "malformed_input",
            f"MTEB relevant_docs file contains no judgments: {path}",
            "Provide at least one relevance judgment.",
        )
    return judgments


def _read_jsonl_objects(path: Path, *, label: str) -> list[dict[str, object]]:
    if not path.is_file():
        raise AdapterError(
            "input_not_found",
            f"{label} file is missing: {path}",
            "Provide a complete MTEB retrieval export.",
        )
    rows: list[dict[str, object]] = []
    try:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            raw = json.loads(line)
            if not isinstance(raw, dict):
                raise AdapterError(
                    "malformed_input",
                    f"{label} line {line_number} must be a JSON object",
                    "Fix the JSONL input so each row is an object.",
                )
            rows.append(cast("dict[str, object]", raw))
    except json.JSONDecodeError as exc:
        raise AdapterError(
            "malformed_input",
            f"{label} contains invalid JSON at line {exc.lineno}",
            "Fix the JSONL syntax and rerun the adapter.",
        ) from exc
    if not rows:
        raise AdapterError(
            "malformed_input",
            f"{label} file is empty: {path}",
            "Provide at least one row.",
        )
    return rows


def _first_present(row: dict[str, object], keys: tuple[str, ...]) -> object | None:
    for key in keys:
        if key in row:
            return row[key]
    return None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", help="MTEB dataset id, for example mteb/SciFact")
    parser.add_argument("--output", required=True, type=Path, help="Output benchmark suite dir")
    parser.add_argument("--source-dir", type=Path, help="Local MTEB retrieval export directory")
    parser.add_argument("--corpus-file", type=Path, help="Explicit corpus JSONL file")
    parser.add_argument("--queries-file", type=Path, help="Explicit queries JSONL file")
    parser.add_argument(
        "--relevance-file",
        type=Path,
        help="Explicit relevant-docs JSONL/TSV file",
    )
    parser.add_argument("--split", default=_DEFAULT_SPLIT)
    parser.add_argument("--subset", default=_DEFAULT_SUBSET)
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
    dataset = cast("str", args.dataset)
    output = cast("Path", args.output)
    json_report = cast("Path | None", args.json_report)
    try:
        report = convert_mteb_dataset(
            dataset,
            output,
            source_dir=cast("Path | None", args.source_dir),
            corpus_file=cast("Path | None", args.corpus_file),
            queries_file=cast("Path | None", args.queries_file),
            relevance_file=cast("Path | None", args.relevance_file),
            split=cast("str", args.split),
            subset=cast("str", args.subset),
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
            "Rerun with a small local export and report this issue if it persists.",
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
    raw_source_dir = args.source_dir
    if isinstance(raw_source_dir, Path):
        return str(raw_source_dir)
    raw_files = [
        value
        for value in (args.corpus_file, args.queries_file, args.relevance_file)
        if isinstance(value, Path)
    ]
    if raw_files:
        return ";".join(str(path) for path in raw_files)
    raw_dataset = args.dataset
    return str(raw_dataset)


if __name__ == "__main__":
    raise SystemExit(main())
