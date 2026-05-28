"""Run generic preflight checks for a real or permissioned academic corpus.

This wrapper is for the stage before a real corpus has full labelled RAG and
answer datasets. It combines strict manifest validation with the generic
document-understanding stress benchmark, producing one JSON artifact that can be
attached to a completion audit.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from hephaion.materials import MaterialRole, material_manifest
from scripts import benchmark_document_understanding, validate_benchmark_manifest

DEFAULT_MIN_DOCUMENTS = 40
DEFAULT_MIN_DOMAINS = 5
DEFAULT_MIN_ROLES = 3
DEFAULT_MIN_DOCUMENT_TYPES = 8
DEFAULT_MIN_STRESSORS = 16
DEFAULT_REQUIRED_STRESSORS = (
    "real-pdf",
    "ocr-noise",
    "table-heavy",
    "multi-column",
    "multilingual",
)
DEFAULT_REQUIRED_ROLES: tuple[MaterialRole, ...] = ("assignment", "past_exam", "slides")
DEFAULT_MIN_OVERVIEW_SOURCE_COVERAGE = 0.4
DEFAULT_FORBIDDEN_KNOWN_LIMITS = (
    "synthetic",
    "no real scanned pdfs",
    "no table-heavy",
    "generated scaffold",
    "provenance requires human review",
    "require human review",
    "no model-backed",
)


class _PreflightTimeoutError(TimeoutError):
    """Raised when a preflight stage exceeds its wall-clock budget."""


@dataclass(frozen=True, slots=True)
class RealCorpusPreflightReport:
    status: int
    armory_path: str
    manifest_path: str
    failures: tuple[str, ...]
    manifest: validate_benchmark_manifest.ManifestReport | None
    document_understanding: benchmark_document_understanding.DocumentUnderstandingReport | None


def run_preflight(
    armory_path: Path,
    manifest_path: Path,
    *,
    min_documents: int = DEFAULT_MIN_DOCUMENTS,
    min_domains: int = DEFAULT_MIN_DOMAINS,
    min_roles: int = DEFAULT_MIN_ROLES,
    min_document_types: int = DEFAULT_MIN_DOCUMENT_TYPES,
    min_stressors: int = DEFAULT_MIN_STRESSORS,
    required_stressors: tuple[str, ...] = DEFAULT_REQUIRED_STRESSORS,
    required_roles: tuple[MaterialRole, ...] = DEFAULT_REQUIRED_ROLES,
    min_role_confidence: float = 0.0,
    min_overview_source_coverage: float = DEFAULT_MIN_OVERVIEW_SOURCE_COVERAGE,
    document_timeout_seconds: int = 0,
    index_file_timeout_seconds: int = 0,
) -> RealCorpusPreflightReport:
    """Run strict manifest validation and generic document-understanding checks."""
    failures: list[str] = []
    manifest_report: validate_benchmark_manifest.ManifestReport | None = None
    document_report: benchmark_document_understanding.DocumentUnderstandingReport | None = None
    manifest_sources: set[str] = set()

    try:
        manifest_sources = _manifest_sources(manifest_path)
        manifest_report = validate_benchmark_manifest.validate_manifest(
            manifest_path,
            min_documents=min_documents,
            min_domains=min_domains,
            min_roles=min_roles,
            min_document_types=min_document_types,
            min_stressors=min_stressors,
            required_stressors=required_stressors,
            forbid_known_limit=DEFAULT_FORBIDDEN_KNOWN_LIMITS,
            require_document_provenance=True,
        )
        if manifest_report.corpus_kind == "synthetic-snippets":
            failures.append("manifest corpus_kind is synthetic-snippets")
    except (OSError, TypeError, ValueError) as exc:
        failures.append(f"manifest: {exc}")

    try:
        failures.extend(_armory_manifest_consistency_failures(armory_path, manifest_sources))
    except OSError as exc:
        failures.append(f"manifest/armory consistency: {exc}")

    try:
        document_report = _run_document_understanding(
            armory_path,
            min_documents=min_documents,
            required_roles=required_roles,
            min_role_confidence=min_role_confidence,
            min_overview_source_coverage=min_overview_source_coverage,
            timeout_seconds=document_timeout_seconds,
            index_file_timeout_seconds=index_file_timeout_seconds,
        )
        failures.extend(
            f"document-understanding: {failure}" for failure in document_report.failures
        )
    except _PreflightTimeoutError as exc:
        failures.append(str(exc))
    except (OSError, TypeError, ValueError) as exc:
        failures.append(f"document-understanding: {exc}")

    return RealCorpusPreflightReport(
        status=1 if failures else 0,
        armory_path=str(armory_path),
        manifest_path=str(manifest_path),
        failures=tuple(failures),
        manifest=manifest_report,
        document_understanding=document_report,
    )


def _run_document_understanding(
    armory_path: Path,
    *,
    min_documents: int,
    required_roles: tuple[MaterialRole, ...],
    min_role_confidence: float,
    min_overview_source_coverage: float,
    timeout_seconds: int,
    index_file_timeout_seconds: int,
) -> benchmark_document_understanding.DocumentUnderstandingReport:
    if timeout_seconds <= 0:
        with _IndexFileTimeoutEnv(index_file_timeout_seconds):
            return benchmark_document_understanding.run_benchmark(
                armory_path,
                min_documents=min_documents,
                require_roles=required_roles,
                min_role_confidence=min_role_confidence,
                min_overview_source_coverage=min_overview_source_coverage,
            )
    start_method = "fork" if "fork" in multiprocessing.get_all_start_methods() else "spawn"
    ctx = multiprocessing.get_context(start_method)
    queue = ctx.Queue()
    process = ctx.Process(
        target=_document_understanding_worker,
        args=(
            queue,
            str(armory_path),
            min_documents,
            required_roles,
            min_role_confidence,
            min_overview_source_coverage,
            index_file_timeout_seconds,
        ),
    )
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join(5)
        raise _PreflightTimeoutError(
            f"document-understanding: timed out after {timeout_seconds} second(s)"
        )
    if queue.empty():
        raise ValueError("document-understanding worker exited without a report")
    status, payload = cast("tuple[str, object]", queue.get())
    if status == "ok":
        return cast("benchmark_document_understanding.DocumentUnderstandingReport", payload)
    raise ValueError(str(payload))


def _document_understanding_worker(
    queue: object,
    armory_path: str,
    min_documents: int,
    required_roles: tuple[MaterialRole, ...],
    min_role_confidence: float,
    min_overview_source_coverage: float,
    index_file_timeout_seconds: int,
) -> None:
    report_queue = cast("multiprocessing.queues.Queue", queue)
    try:
        with _IndexFileTimeoutEnv(index_file_timeout_seconds):
            report_queue.put(
                (
                    "ok",
                    benchmark_document_understanding.run_benchmark(
                        Path(armory_path),
                        min_documents=min_documents,
                        require_roles=required_roles,
                        min_role_confidence=min_role_confidence,
                        min_overview_source_coverage=min_overview_source_coverage,
                    ),
                )
            )
    except Exception as exc:
        report_queue.put(("error", f"{type(exc).__name__}: {exc}"))


class _IndexFileTimeoutEnv:
    def __init__(self, seconds: int) -> None:
        self._seconds = seconds
        self._previous: str | None = None

    def __enter__(self) -> None:
        if self._seconds <= 0:
            return
        self._previous = os.environ.get("HEPHAION_INDEX_FILE_TIMEOUT_SECONDS")
        os.environ["HEPHAION_INDEX_FILE_TIMEOUT_SECONDS"] = str(self._seconds)

    def __exit__(self, *_exc: object) -> None:
        if self._seconds <= 0:
            return
        if self._previous is None:
            os.environ.pop("HEPHAION_INDEX_FILE_TIMEOUT_SECONDS", None)
        else:
            os.environ["HEPHAION_INDEX_FILE_TIMEOUT_SECONDS"] = self._previous


def _manifest_sources(manifest_path: Path) -> set[str]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("manifest must be a JSON object")
    raw_documents = payload.get("documents")
    if not isinstance(raw_documents, list):
        raise TypeError("manifest documents must be a list")
    sources: set[str] = set()
    for idx, raw_document in enumerate(raw_documents, start=1):
        if not isinstance(raw_document, dict):
            raise TypeError(f"manifest document {idx} must be an object")
        source = raw_document.get("source")
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"manifest document {idx} source must be a non-empty string")
        sources.add(source.strip())
    return sources


def _armory_manifest_consistency_failures(
    armory_path: Path,
    manifest_sources: set[str],
) -> tuple[str, ...]:
    if not manifest_sources:
        return ()
    visible_sources = {material.rel_path for material in material_manifest(armory_path)}
    missing_from_armory = tuple(sorted(manifest_sources - visible_sources))
    missing_from_manifest = tuple(sorted(visible_sources - manifest_sources))
    failures: list[str] = []
    if missing_from_armory:
        failures.append(
            "manifest/armory mismatch: manifest source(s) missing from armory: "
            + ", ".join(missing_from_armory[:10])
        )
    if missing_from_manifest:
        failures.append(
            "manifest/armory mismatch: armory material(s) missing from manifest: "
            + ", ".join(missing_from_manifest[:10])
        )
    return tuple(failures)


def print_text_report(report: RealCorpusPreflightReport) -> None:
    print(f"Real corpus preflight: {report.armory_path}")
    print(f"status={report.status}")
    if report.manifest is not None:
        validate_benchmark_manifest.print_text_report(report.manifest)
    if report.document_understanding is not None:
        benchmark_document_understanding.print_text_report(report.document_understanding)
    if report.failures:
        print("failures:")
        for failure in report.failures:
            print(f"  - {failure}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("armory", type=Path, help="Armory path containing materials/")
    parser.add_argument("manifest", type=Path, help="Benchmark manifest JSON")
    parser.add_argument("--min-documents", type=int, default=DEFAULT_MIN_DOCUMENTS)
    parser.add_argument("--min-domains", type=int, default=DEFAULT_MIN_DOMAINS)
    parser.add_argument("--min-roles", type=int, default=DEFAULT_MIN_ROLES)
    parser.add_argument("--min-document-types", type=int, default=DEFAULT_MIN_DOCUMENT_TYPES)
    parser.add_argument("--min-stressors", type=int, default=DEFAULT_MIN_STRESSORS)
    parser.add_argument("--require-stressor", action="append", default=[])
    parser.add_argument(
        "--require-role",
        action="append",
        choices=sorted(benchmark_document_understanding._KNOWN_ROLES),
        default=[],
    )
    parser.add_argument("--min-role-confidence", type=float, default=0.0)
    parser.add_argument(
        "--min-overview-source-coverage",
        type=float,
        default=DEFAULT_MIN_OVERVIEW_SOURCE_COVERAGE,
    )
    parser.add_argument(
        "--document-timeout-seconds",
        type=int,
        default=0,
        help="Abort document-understanding preflight after this many seconds; 0 disables.",
    )
    parser.add_argument(
        "--index-file-timeout-seconds",
        type=int,
        default=0,
        help="Skip one material file after this many indexing seconds; 0 disables.",
    )
    parser.add_argument("--json-report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    min_role_confidence = float(args.min_role_confidence)
    if not 0.0 <= min_role_confidence <= 1.0:
        parser.error("--min-role-confidence must be between 0.0 and 1.0")
    min_overview_source_coverage = float(args.min_overview_source_coverage)
    if not 0.0 <= min_overview_source_coverage <= 1.0:
        parser.error("--min-overview-source-coverage must be between 0.0 and 1.0")
    document_timeout_seconds = int(args.document_timeout_seconds)
    if document_timeout_seconds < 0:
        parser.error("--document-timeout-seconds must be non-negative")
    index_file_timeout_seconds = int(args.index_file_timeout_seconds)
    if index_file_timeout_seconds < 0:
        parser.error("--index-file-timeout-seconds must be non-negative")
    required_roles = (
        tuple(
            benchmark_document_understanding._as_material_role(role)
            for role in cast("list[str]", args.require_role)
        )
        or DEFAULT_REQUIRED_ROLES
    )
    required_stressors = tuple(cast("list[str]", args.require_stressor)) or (
        DEFAULT_REQUIRED_STRESSORS
    )
    report = run_preflight(
        cast("Path", args.armory).expanduser().resolve(),
        cast("Path", args.manifest).expanduser().resolve(),
        min_documents=int(args.min_documents),
        min_domains=int(args.min_domains),
        min_roles=int(args.min_roles),
        min_document_types=int(args.min_document_types),
        min_stressors=int(args.min_stressors),
        required_stressors=required_stressors,
        required_roles=required_roles,
        min_role_confidence=min_role_confidence,
        min_overview_source_coverage=min_overview_source_coverage,
        document_timeout_seconds=document_timeout_seconds,
        index_file_timeout_seconds=index_file_timeout_seconds,
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
