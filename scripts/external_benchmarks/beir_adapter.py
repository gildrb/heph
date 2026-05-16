"""Convert BEIR datasets into Hephaistos benchmark armories.

The adapter accepts local BEIR-format fixtures/directories for deterministic
testing and can materialize approved public BEIR zip assets for named datasets.
It never depends on the unavailable ``beir-datasets`` package.
"""

from __future__ import annotations

import argparse
import json
import shutil
import urllib.error
import urllib.request
import zipfile
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

_ADAPTER = "beir"
_DEFAULT_TOP_K = 5
_DEFAULT_SPLIT = "test"
_DEFAULT_TASK_TYPE = "retrieval"
_DEFAULT_DOMAIN = "biomedical"
_PUBLIC_BEIR_BASE_URL = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets"
_SUPPORTED_PUBLIC_DATASETS = frozenset({"nfcorpus", "scidocs", "trec-covid"})


def convert_beir_dataset(
    dataset: str,
    output_dir: Path,
    *,
    source_dir: Path | None = None,
    source_zip: Path | None = None,
    download_url: str = "",
    cache_dir: Path | None = None,
    split: str = _DEFAULT_SPLIT,
    domain: str = _DEFAULT_DOMAIN,
    task_type: str = _DEFAULT_TASK_TYPE,
    positive_threshold: float = 1.0,
    top_k: int = _DEFAULT_TOP_K,
    overwrite: bool = False,
) -> dict[str, object]:
    """Load a BEIR dataset and write a Heph benchmark suite."""
    output = ensure_output_available(output_dir, overwrite=overwrite)
    beir_name = _beir_name(dataset)
    data_root, input_source, cache_info = _resolve_dataset_root(
        beir_name,
        output,
        source_dir=source_dir,
        source_zip=source_zip,
        download_url=download_url,
        cache_dir=cache_dir,
    )
    documents = _load_corpus(data_root / "corpus.jsonl")
    queries = _load_queries(data_root / "queries.jsonl")
    judgments = _load_qrels(_qrels_path(data_root, split))
    conversion = ConversionInput(
        adapter=_ADAPTER,
        dataset=_dataset_identifier(beir_name),
        source_format="beir-jsonl",
        input_source=input_source,
        split=split,
        domain=domain,
        task_type=task_type,
        documents=tuple(documents),
        queries=tuple(queries),
        judgments=tuple(judgments),
        top_k=top_k,
        positive_threshold=positive_threshold,
        cache=cache_info,
    )
    return convert_dataset(conversion, output, overwrite=overwrite)


def _beir_name(dataset: str) -> str:
    raw = dataset.strip()
    if raw.startswith("beir/"):
        raw = raw.removeprefix("beir/")
    if not raw:
        raise AdapterError(
            "unsupported_dataset",
            "BEIR dataset identifier is empty",
            "Use a dataset identifier such as beir/nfcorpus.",
        )
    return raw


def _dataset_identifier(beir_name: str) -> str:
    return f"beir/{beir_name}"


def _resolve_dataset_root(
    beir_name: str,
    output_dir: Path,
    *,
    source_dir: Path | None,
    source_zip: Path | None,
    download_url: str,
    cache_dir: Path | None,
) -> tuple[Path, str, CacheInfo]:
    configured_sources = sum(
        1
        for configured in (source_dir, source_zip, download_url.strip() or None)
        if configured is not None
    )
    if configured_sources > 1:
        raise AdapterError(
            "invalid_option",
            "choose only one of --source-dir, --source-zip, or --download-url",
            "Provide a single input source for deterministic conversion.",
        )
    if source_dir is not None:
        root = _discover_beir_root(source_dir.expanduser().resolve())
        return root, str(root), CacheInfo(enabled=False, path="", used=False)
    resolved_cache_dir = (cache_dir or output_dir / ".adapter-cache" / _ADAPTER).expanduser()
    resolved_cache_dir = resolved_cache_dir.resolve()
    if source_zip is not None:
        root = _extract_zip(source_zip.expanduser().resolve(), resolved_cache_dir, beir_name)
        return (
            root,
            str(source_zip.expanduser().resolve()),
            CacheInfo(enabled=True, path=str(resolved_cache_dir), used=True, assets=(str(root),)),
        )
    url = download_url.strip() or _public_dataset_url(beir_name)
    if not url:
        supported = ", ".join(f"beir/{name}" for name in sorted(_SUPPORTED_PUBLIC_DATASETS))
        raise AdapterError(
            "unsupported_dataset",
            f"unsupported BEIR dataset: beir/{beir_name}",
            f"Use one of {supported}, pass --source-dir for a fixture, or pass --download-url.",
        )
    root = _download_and_extract(url, resolved_cache_dir, beir_name)
    return (
        root,
        url,
        CacheInfo(
            enabled=True,
            path=str(resolved_cache_dir),
            used=True,
            assets=(url, str(root)),
        ),
    )


def _public_dataset_url(beir_name: str) -> str:
    if beir_name not in _SUPPORTED_PUBLIC_DATASETS:
        return ""
    return f"{_PUBLIC_BEIR_BASE_URL}/{beir_name}.zip"


def _discover_beir_root(path: Path) -> Path:
    if not path.exists():
        raise AdapterError(
            "input_not_found",
            f"BEIR source directory does not exist: {path}",
            "Provide an existing directory containing corpus.jsonl, queries.jsonl, and qrels/.",
        )
    if not path.is_dir():
        raise AdapterError(
            "input_not_directory",
            f"BEIR source path is not a directory: {path}",
            "Use --source-zip for zip files or --source-dir for extracted directories.",
        )
    if (path / "corpus.jsonl").is_file() and (path / "queries.jsonl").is_file():
        return path
    candidates = [
        child
        for child in sorted(path.iterdir())
        if child.is_dir()
        and (child / "corpus.jsonl").is_file()
        and (child / "queries.jsonl").is_file()
    ]
    if len(candidates) == 1:
        return candidates[0]
    raise AdapterError(
        "malformed_input",
        f"could not find a BEIR dataset root under {path}",
        "Expected corpus.jsonl, queries.jsonl, and qrels/<split>.tsv.",
    )


def _extract_zip(source_zip: Path, cache_dir: Path, beir_name: str) -> Path:
    if not source_zip.is_file():
        raise AdapterError(
            "input_not_found",
            f"BEIR source zip does not exist: {source_zip}",
            "Provide an existing BEIR zip file.",
        )
    extract_root = cache_dir / beir_name
    if (extract_root / "corpus.jsonl").is_file():
        return extract_root
    cache_dir.mkdir(parents=True, exist_ok=True)
    temp_root = cache_dir / f".{beir_name}-extracting"
    if temp_root.exists():
        shutil.rmtree(temp_root)
    temp_root.mkdir(parents=True)
    try:
        _safe_extract_zip(source_zip, temp_root)
        discovered = _discover_beir_root(temp_root)
        if extract_root.exists():
            shutil.rmtree(extract_root)
        shutil.move(str(discovered), extract_root)
    except zipfile.BadZipFile as exc:
        raise AdapterError(
            "malformed_input",
            f"invalid BEIR zip file: {source_zip}",
            "Download a valid BEIR dataset zip or use --source-dir with extracted files.",
        ) from exc
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)
    return extract_root


def _download_and_extract(url: str, cache_dir: Path, beir_name: str) -> Path:
    if not url.startswith("https://"):
        raise AdapterError(
            "unsafe_input_source",
            f"BEIR download URL must use HTTPS: {url}",
            "Use an HTTPS BEIR public asset URL or a local --source-dir fixture.",
        )
    cache_dir.mkdir(parents=True, exist_ok=True)
    zip_path = cache_dir / f"{beir_name}.zip"
    if not zip_path.exists():
        try:
            urllib.request.urlretrieve(url, zip_path)
        except (OSError, urllib.error.URLError) as exc:
            raise AdapterError(
                "download_failed",
                f"could not download BEIR dataset asset: {url}",
                "Check network access, pass --source-dir, or predownload with --source-zip.",
            ) from exc
    return _extract_zip(zip_path, cache_dir, beir_name)


def _safe_extract_zip(source_zip: Path, destination: Path) -> None:
    with zipfile.ZipFile(source_zip) as archive:
        for member in archive.infolist():
            member_path = destination / member.filename
            resolved = member_path.resolve()
            try:
                resolved.relative_to(destination.resolve())
            except ValueError as exc:
                raise AdapterError(
                    "unsafe_archive",
                    f"BEIR zip contains unsafe path: {member.filename}",
                    "Use an official BEIR dataset zip without path traversal entries.",
                ) from exc
        archive.extractall(destination)


def _load_corpus(path: Path) -> list[ExternalDocument]:
    rows = _read_jsonl_objects(path, label="BEIR corpus")
    documents: list[ExternalDocument] = []
    for index, raw in enumerate(rows, start=1):
        context = f"BEIR corpus row {index}"
        document_id = required_str(raw.get("_id"), field_name="_id", context=context)
        text = required_str(raw.get("text"), field_name="text", context=context)
        title = optional_str(raw.get("title"))
        metadata = metadata_from_mapping(raw, exclude=frozenset({"_id", "text", "title"}))
        source_url = optional_str(raw.get("source_url"))
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


def _load_queries(path: Path) -> list[ExternalQuery]:
    rows = _read_jsonl_objects(path, label="BEIR queries")
    queries: list[ExternalQuery] = []
    for index, raw in enumerate(rows, start=1):
        context = f"BEIR query row {index}"
        query_id = required_str(raw.get("_id"), field_name="_id", context=context)
        query_text = optional_str(raw.get("text")) or optional_str(raw.get("query"))
        if not query_text:
            raise AdapterError(
                "malformed_input",
                f"{context} must include non-empty text or query",
                "Fix queries.jsonl so every query has text.",
            )
        metadata = metadata_from_mapping(raw, exclude=frozenset({"_id", "text", "query"}))
        queries.append(ExternalQuery(original_id=query_id, text=query_text, metadata=metadata))
    return queries


def _read_jsonl_objects(path: Path, *, label: str) -> list[dict[str, object]]:
    if not path.is_file():
        raise AdapterError(
            "input_not_found",
            f"{label} file is missing: {path}",
            "Provide a complete BEIR dataset with corpus.jsonl and queries.jsonl.",
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


def _qrels_path(data_root: Path, split: str) -> Path:
    candidates = (
        data_root / "qrels" / f"{split}.tsv",
        data_root / "qrels" / f"{split}.txt",
        data_root / f"qrels-{split}.tsv",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise AdapterError(
        "input_not_found",
        f"BEIR qrels file is missing for split {split!r} under {data_root}",
        "Provide qrels/<split>.tsv or choose the correct --split.",
    )


def _load_qrels(path: Path) -> list[RelevanceJudgment]:
    judgments: list[RelevanceJudgment] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.strip().split("\t")
        if len(parts) == 1:
            parts = line.strip().split()
        normalized = [part.strip() for part in parts if part.strip()]
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
                f"qrels line {line_number} must have at least 3 columns",
                "Use BEIR TSV qrels: query-id, corpus-id, score.",
            )
        grade = numeric_grade(raw_grade, context=f"qrels line {line_number}")
        judgments.append(
            RelevanceJudgment(
                query_id=query_id,
                document_id=document_id,
                grade=grade,
                metadata={"qrels_path": path.name, "line": line_number},
            )
        )
    if not judgments:
        raise AdapterError(
            "malformed_input",
            f"qrels file contains no judgments: {path}",
            "Provide at least one relevance judgment.",
        )
    return judgments


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", help="BEIR dataset id, for example beir/nfcorpus")
    parser.add_argument("--output", required=True, type=Path, help="Output benchmark suite dir")
    parser.add_argument("--source-dir", type=Path, help="Extracted BEIR dataset directory")
    parser.add_argument("--source-zip", type=Path, help="BEIR dataset zip file")
    parser.add_argument("--download-url", default="", help="Explicit public BEIR zip URL")
    parser.add_argument("--cache-dir", type=Path, help="Explicit adapter cache directory")
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
    dataset = cast("str", args.dataset)
    output = cast("Path", args.output)
    json_report = cast("Path | None", args.json_report)
    try:
        report = convert_beir_dataset(
            dataset,
            output,
            source_dir=cast("Path | None", args.source_dir),
            source_zip=cast("Path | None", args.source_zip),
            download_url=cast("str", args.download_url),
            cache_dir=cast("Path | None", args.cache_dir),
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
            "Rerun with a small fixture and report this issue if it persists.",
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
    raw_source_zip = args.source_zip
    raw_download_url = args.download_url
    if isinstance(raw_source_dir, Path):
        return str(raw_source_dir)
    if isinstance(raw_source_zip, Path):
        return str(raw_source_zip)
    if isinstance(raw_download_url, str) and raw_download_url:
        return raw_download_url
    raw_dataset = args.dataset
    return str(raw_dataset)


if __name__ == "__main__":
    raise SystemExit(main())
