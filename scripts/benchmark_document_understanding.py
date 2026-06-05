"""Stress benchmark unlabelled document understanding for any armory.

This script is intentionally generic. It does not know course names, lecturer
names, universities, languages, or subjects. It checks whether an armory has
indexable material, whether extraction health passes, and whether content-based
role inference finds the requested broad document roles before a labelled eval
dataset exists.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from chat.evidence import build_turn_evidence_from_overview
from chat.session import ChatSession
from materials import MaterialRole, infer_material_role_from_text, material_manifest
from rag import ArmoryIndex, load_or_build
from rag.health import scan_extraction_health
from runtime import ChatConfig, Conversation

_KNOWN_ROLES = frozenset(
    {
        "assignment",
        "codebase",
        "lecture",
        "past_exam",
        "reference",
        "slides",
        "textbook",
        "vocabulary",
    }
)
_OVERVIEW_EXPECTED_SAMPLE_CAP = 32
_OVERVIEW_SAMPLE_CAP_MAX_COVERAGE_FLOOR = 0.4


@dataclass(frozen=True, slots=True)
class DocumentUnderstandingResult:
    source: str
    role: MaterialRole
    confidence: float
    reason: str
    chunks: int
    indexed: bool


@dataclass(frozen=True, slots=True)
class DocumentUnderstandingReport:
    armory_path: str
    visible_materials: int
    indexed_documents: int
    chunks: int
    role_counts: dict[str, int]
    indexed_role_counts: dict[str, int]
    unindexed_materials: tuple[str, ...]
    unindexable_files: dict[str, str]
    extraction_health_passed: bool
    extraction_health_pass_rate: float
    extraction_health_failures: tuple[str, ...]
    overview_sampled_sources: int
    overview_total_sources: int
    overview_source_coverage_rate: float
    failures: tuple[str, ...]
    results: tuple[DocumentUnderstandingResult, ...]

    @property
    def passed(self) -> bool:
        return not self.failures


def _as_material_role(value: str) -> MaterialRole:
    if value not in _KNOWN_ROLES:
        raise ValueError(f"unknown material role: {value}")
    return cast("MaterialRole", value)


def run_benchmark(
    armory_path: Path,
    *,
    min_documents: int = 1,
    require_roles: tuple[MaterialRole, ...] = (),
    min_role_confidence: float = 0.0,
    min_overview_source_coverage: float = 0.0,
) -> DocumentUnderstandingReport:
    """Run generic document-understanding checks against an armory."""
    index = load_or_build(armory_path)
    health = scan_extraction_health(armory_path)
    visible_sources = {material.rel_path for material in material_manifest(armory_path)}
    documents_by_source = {document.source: document for document in index.documents}
    results: list[DocumentUnderstandingResult] = []
    role_counts: Counter[str] = Counter()
    indexed_role_counts: Counter[str] = Counter()

    for source in sorted(visible_sources | set(documents_by_source)):
        document = documents_by_source.get(source)
        indexed = document is not None and bool(document.chunks)
        text = " ".join(chunk.text for chunk in document.chunks) if document is not None else ""
        role, confidence, reason = infer_material_role_from_text(source, text)
        role_counts[role] += 1
        if indexed:
            indexed_role_counts[role] += 1
        results.append(
            DocumentUnderstandingResult(
                source=source,
                role=role,
                confidence=confidence,
                reason=reason,
                chunks=len(document.chunks) if document is not None else 0,
                indexed=indexed,
            )
        )

    unindexed = tuple(
        sorted(source for source in visible_sources if source not in documents_by_source)
    )
    failures: list[str] = []
    if len(index.documents) < min_documents:
        failures.append(
            f"indexed document count {len(index.documents)} is below required {min_documents}"
        )
    failures.extend(
        f"required indexed role not found: {role}"
        for role in require_roles
        if indexed_role_counts[role] <= 0
    )
    low_confidence = tuple(
        result.source
        for result in results
        if result.indexed and result.confidence < min_role_confidence
    )
    if low_confidence:
        failures.append("role confidence below threshold for: " + ", ".join(low_confidence[:10]))
    if not health.passed:
        failures.append("extraction health failed")
    overview_sampled_sources, overview_total_sources = _overview_source_coverage(
        armory_path,
        index,
        tuple(sorted(visible_sources)),
    )
    overview_source_coverage_rate = (
        overview_sampled_sources / overview_total_sources if overview_total_sources else 0.0
    )
    overview_sampled_enough = overview_sampled_sources >= min(
        overview_total_sources,
        _OVERVIEW_EXPECTED_SAMPLE_CAP,
    )
    overview_cap_satisfies_floor = (
        min_overview_source_coverage <= _OVERVIEW_SAMPLE_CAP_MAX_COVERAGE_FLOOR
        and overview_sampled_enough
    )
    if (
        overview_source_coverage_rate < min_overview_source_coverage
        and not overview_cap_satisfies_floor
    ):
        failures.append(
            "overview source coverage "
            f"{overview_source_coverage_rate:.3f} below required "
            f"{min_overview_source_coverage:.3f} "
            f"({overview_sampled_sources}/{overview_total_sources} indexed sources)"
        )

    return DocumentUnderstandingReport(
        armory_path=str(armory_path),
        visible_materials=len(visible_sources),
        indexed_documents=len(index.documents),
        chunks=index.chunk_count,
        role_counts=dict(sorted(role_counts.items())),
        indexed_role_counts=dict(sorted(indexed_role_counts.items())),
        unindexed_materials=unindexed,
        unindexable_files=dict(sorted(index.unindexable_files.items())),
        extraction_health_passed=health.passed,
        extraction_health_pass_rate=health.pass_rate,
        extraction_health_failures=tuple(issue.source for issue in health.issues),
        overview_sampled_sources=overview_sampled_sources,
        overview_total_sources=overview_total_sources,
        overview_source_coverage_rate=overview_source_coverage_rate,
        failures=tuple(failures),
        results=tuple(results),
    )


def _overview_source_coverage(
    armory_path: Path,
    index: ArmoryIndex,
    visible_sources: tuple[str, ...],
) -> tuple[int, int]:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="document-understanding-benchmark",
        armory_path=armory_path,
        source_file_count=len(visible_sources),
        source_files=visible_sources,
    )
    session.rag_index = index
    evidence = build_turn_evidence_from_overview(session)
    if evidence is None:
        return 0, 0
    sampled_sources = evidence.sampled_source_count or len(
        {item.source for item in evidence.items}
    )
    total_sources = evidence.total_source_count or sampled_sources
    return sampled_sources, total_sources


def print_text_report(report: DocumentUnderstandingReport) -> None:
    """Print a compact human-readable report."""
    print(f"Document understanding stress: {report.armory_path}")
    print(
        f"materials={report.visible_materials} indexed={report.indexed_documents} "
        f"chunks={report.chunks}"
    )
    role_summary = ", ".join(f"{role}={count}" for role, count in report.role_counts.items())
    print(f"roles: {role_summary or 'none'}")
    indexed_role_summary = ", ".join(
        f"{role}={count}" for role, count in report.indexed_role_counts.items()
    )
    print(f"indexed roles: {indexed_role_summary or 'none'}")
    print(f"extraction_health={report.extraction_health_pass_rate:.1%}")
    print(
        "overview_source_coverage="
        f"{report.overview_source_coverage_rate:.1%} "
        f"({report.overview_sampled_sources}/{report.overview_total_sources})"
    )
    if report.unindexed_materials:
        print("unindexed materials:")
        for source in report.unindexed_materials[:10]:
            reason = report.unindexable_files.get(source, "not indexed")
            print(f"  - {source}: {reason}")
        if len(report.unindexed_materials) > 10:
            print(f"  - ... {len(report.unindexed_materials) - 10} more")
    print("documents:")
    for result in report.results[:20]:
        status = "indexed" if result.indexed else "not-indexed"
        print(
            f"  - {result.source}: {result.role} "
            f"({result.confidence:.2f}, {status}, {result.chunks} chunks)"
        )
    if len(report.results) > 20:
        print(f"  - ... {len(report.results) - 20} more")
    if report.failures:
        print("failures:")
        for failure in report.failures:
            print(f"  - {failure}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("armory", type=Path, help="Armory path to inspect")
    parser.add_argument("--min-documents", type=int, default=1)
    parser.add_argument(
        "--require-role",
        action="append",
        default=[],
        choices=sorted(_KNOWN_ROLES),
        help="Require at least one indexed/visible document with this inferred role",
    )
    parser.add_argument("--min-role-confidence", type=float, default=0.0)
    parser.add_argument("--min-overview-source-coverage", type=float, default=0.0)
    parser.add_argument("--json-report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    min_role_confidence = float(args.min_role_confidence)
    if not 0.0 <= min_role_confidence <= 1.0:
        parser.error("--min-role-confidence must be between 0.0 and 1.0")
    min_overview_source_coverage = float(args.min_overview_source_coverage)
    if not 0.0 <= min_overview_source_coverage <= 1.0:
        parser.error("--min-overview-source-coverage must be between 0.0 and 1.0")
    try:
        report = run_benchmark(
            args.armory,
            min_documents=int(args.min_documents),
            require_roles=tuple(_as_material_role(role) for role in args.require_role),
            min_role_confidence=min_role_confidence,
            min_overview_source_coverage=min_overview_source_coverage,
        )
    except (OSError, ValueError) as exc:
        print(f"document understanding benchmark error: {exc}", file=sys.stderr)
        return 2

    print_text_report(report)
    if args.json_report is not None:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(
            json.dumps(asdict(report), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
