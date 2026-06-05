"""Prepare manifest and preflight artifacts for a real academic corpus.

This command does not make a corpus pass the completion audit by itself. It
creates the two artifacts the audit expects, using the same strict preflight
checks as ``scripts.run_real_corpus_preflight``. Small, synthetic, or weakly
labelled corpora should still fail with concrete reasons.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from hephaion.materials import MaterialRole

from scripts import create_benchmark_manifest, run_real_corpus_preflight


@dataclass(frozen=True, slots=True)
class PreparedRealCorpusEvidence:
    status: int
    armory_path: str
    output_dir: str
    manifest_path: str
    preflight_report_path: str
    next_chat_capture_command: str
    next_chat_extract_command: str
    next_chat_verify_command: str
    next_audit_command: str
    failures: tuple[str, ...]


def prepare_evidence(
    armory_path: Path,
    output_dir: Path,
    *,
    corpus_id: str = "external-academic-corpus",
    description: str = "External academic benchmark corpus.",
    corpus_kind: str = "permissioned-materials",
    domain: str = "unlabelled",
    infer_roles_from_index: bool = True,
    reviewed_manifest: bool = False,
    min_documents: int = run_real_corpus_preflight.DEFAULT_MIN_DOCUMENTS,
    min_domains: int = run_real_corpus_preflight.DEFAULT_MIN_DOMAINS,
    min_roles: int = run_real_corpus_preflight.DEFAULT_MIN_ROLES,
    min_document_types: int = run_real_corpus_preflight.DEFAULT_MIN_DOCUMENT_TYPES,
    min_stressors: int = run_real_corpus_preflight.DEFAULT_MIN_STRESSORS,
    required_stressors: tuple[str, ...] = run_real_corpus_preflight.DEFAULT_REQUIRED_STRESSORS,
    required_roles: tuple[MaterialRole, ...] = run_real_corpus_preflight.DEFAULT_REQUIRED_ROLES,
    min_role_confidence: float = 0.0,
    min_overview_source_coverage: float = (
        run_real_corpus_preflight.DEFAULT_MIN_OVERVIEW_SOURCE_COVERAGE
    ),
) -> PreparedRealCorpusEvidence:
    """Create a manifest scaffold and run strict preflight for an armory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    _ensure_suite_armory_link(output_dir, armory_path)
    manifest_path = output_dir / "real-corpus-manifest.json"
    preflight_report_path = output_dir / "real-corpus-preflight.json"

    failures: list[str] = []
    try:
        manifest = create_benchmark_manifest.create_manifest(
            armory_path,
            corpus_id=corpus_id,
            description=description,
            corpus_kind=corpus_kind,
            domain=domain,
            infer_roles_from_index=infer_roles_from_index,
            reviewed=reviewed_manifest,
        )
        _annotate_local_permissioned_provenance(manifest, armory_path)
        create_benchmark_manifest.write_manifest(manifest_path, manifest)
        _write_placeholder_datasets(output_dir, manifest["datasets"])
    except (OSError, ValueError) as exc:
        failures.append(f"manifest generation: {exc}")

    preflight_report: run_real_corpus_preflight.RealCorpusPreflightReport | None = None
    if manifest_path.is_file():
        preflight_report = run_real_corpus_preflight.run_preflight(
            armory_path,
            manifest_path,
            min_documents=min_documents,
            min_domains=min_domains,
            min_roles=min_roles,
            min_document_types=min_document_types,
            min_stressors=min_stressors,
            required_stressors=required_stressors,
            required_roles=required_roles,
            min_role_confidence=min_role_confidence,
            min_overview_source_coverage=min_overview_source_coverage,
        )
        preflight_report_path.write_text(
            json.dumps(asdict(preflight_report), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        failures.extend(preflight_report.failures)

    status = 1 if failures or preflight_report is None else preflight_report.status
    return PreparedRealCorpusEvidence(
        status=status,
        armory_path=str(armory_path),
        output_dir=str(output_dir),
        manifest_path=str(manifest_path),
        preflight_report_path=str(preflight_report_path),
        next_chat_capture_command=(
            f'uv run heph chat ask --jsonl {armory_path} "what is the material about" '
            f"> {output_dir / 'chat_events.jsonl'}"
        ),
        next_chat_extract_command=(
            "uv run python -m scripts.extract_chat_event_expectation "
            f"{output_dir / 'chat_events.jsonl'} "
            f"--output {output_dir / 'chat_event_expectation.json'}"
        ),
        next_chat_verify_command=(
            "uv run python -m scripts.benchmark_chat_events "
            f"{output_dir / 'chat_events.jsonl'} "
            f"--answer-expectation {output_dir / 'chat_event_expectation.json'}"
        ),
        next_audit_command=(
            "uv run python -m scripts.audit_agent_harness_completion "
            f"--real-manifest {manifest_path} "
            f"--real-preflight-report {preflight_report_path} "
            "--model-matrix-report <model-matrix-report.json>"
        ),
        failures=tuple(failures),
    )


def _ensure_suite_armory_link(output_dir: Path, armory_path: Path) -> None:
    suite_armory = output_dir / "armory"
    if suite_armory.exists():
        if suite_armory.resolve() == armory_path.resolve():
            return
        raise OSError(f"output suite already has a different armory path: {suite_armory}")
    try:
        suite_armory.symlink_to(armory_path, target_is_directory=True)
    except OSError:
        shutil.copytree(armory_path, suite_armory)


def _annotate_local_permissioned_provenance(
    manifest: create_benchmark_manifest.GeneratedManifest,
    armory_path: Path,
) -> None:
    if manifest["corpus_kind"] != "permissioned-materials":
        return
    note = f"Local permissioned material from armory: {armory_path.expanduser().resolve()}"
    for document in manifest["documents"]:
        if not document["source_url"] and not document["permission_note"]:
            document["permission_note"] = note


def _write_placeholder_datasets(
    output_dir: Path,
    datasets: list[create_benchmark_manifest.ManifestDataset],
) -> None:
    for dataset in datasets:
        dataset_path = output_dir / dataset["path"]
        if dataset_path.exists():
            continue
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        dataset_path.write_text(_placeholder_dataset_text(dataset["kind"]), encoding="utf-8")


def _placeholder_dataset_text(kind: str) -> str:
    if kind == "chat-event-answer-expectation":
        return json.dumps(_chat_event_expectation_scaffold(), ensure_ascii=False, indent=2) + "\n"
    if kind.endswith("expectation"):
        return "{}\n"
    return ""


def _chat_event_expectation_scaffold() -> list[dict[str, object]]:
    return [
        {
            "id": "real-corpus-material-overview",
            "domain": "review-required",
            "task": "material-overview",
            "must_not_include": [
                "the files cover",
                "next action",
                "say ready when you want recall",
                "ask for recall",
                "answer from memory",
                "source-backed",
                "source backed",
                "no evidence citations",
                "Document signals",
                "Retrieved overview sample",
                "Sampled orientation",
                "Visible topics",
                "non-exhaustive list",
                "not an exhaustive summary",
                "only a sample",
                "partial inventory",
            ],
            "expected_citations": ["E1", "E2"],
            "min_words": 24,
            "min_citation_count": 2,
            "min_distinct_sources": 2,
            "min_bullet_count": 2,
            "min_cited_bullet_count": 2,
            "max_explicit_date_lines": 1,
            "required_material_operations": ["sample_overview"],
            "forbidden_material_operations": ["search_index"],
            "evidence": [],
        }
    ]


def print_text_report(report: PreparedRealCorpusEvidence) -> None:
    print(f"Prepared real corpus evidence: {report.armory_path}")
    print(f"status={report.status}")
    print(f"manifest={report.manifest_path}")
    print(f"preflight_report={report.preflight_report_path}")
    print(f"next_chat_capture_command={report.next_chat_capture_command}")
    print(f"next_chat_extract_command={report.next_chat_extract_command}")
    print(f"next_chat_verify_command={report.next_chat_verify_command}")
    print(f"next_audit_command={report.next_audit_command}")
    if report.failures:
        print("failures:")
        for failure in report.failures:
            print(f"  - {failure}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("armory", type=Path, help="Armory path containing materials/")
    parser.add_argument("output_dir", type=Path, help="Directory for generated evidence files")
    parser.add_argument("--id", default="external-academic-corpus")
    parser.add_argument("--description", default="External academic benchmark corpus.")
    parser.add_argument("--corpus-kind", default="permissioned-materials")
    parser.add_argument("--domain", default="unlabelled")
    parser.add_argument(
        "--no-infer-roles-from-index",
        action="store_true",
        help="Use scanner role guesses only; do not inspect indexed document text.",
    )
    parser.add_argument(
        "--reviewed-manifest",
        action="store_true",
        help="Do not add generated-scaffold known_limits to the generated manifest.",
    )
    parser.add_argument(
        "--min-documents",
        type=int,
        default=run_real_corpus_preflight.DEFAULT_MIN_DOCUMENTS,
    )
    parser.add_argument(
        "--min-domains",
        type=int,
        default=run_real_corpus_preflight.DEFAULT_MIN_DOMAINS,
    )
    parser.add_argument(
        "--min-roles",
        type=int,
        default=run_real_corpus_preflight.DEFAULT_MIN_ROLES,
    )
    parser.add_argument(
        "--min-document-types",
        type=int,
        default=run_real_corpus_preflight.DEFAULT_MIN_DOCUMENT_TYPES,
    )
    parser.add_argument(
        "--min-stressors",
        type=int,
        default=run_real_corpus_preflight.DEFAULT_MIN_STRESSORS,
    )
    parser.add_argument("--require-stressor", action="append", default=[])
    parser.add_argument(
        "--require-role",
        action="append",
        choices=sorted(run_real_corpus_preflight.benchmark_document_understanding._KNOWN_ROLES),
        default=[],
    )
    parser.add_argument("--min-role-confidence", type=float, default=0.0)
    parser.add_argument(
        "--min-overview-source-coverage",
        type=float,
        default=run_real_corpus_preflight.DEFAULT_MIN_OVERVIEW_SOURCE_COVERAGE,
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

    required_roles = (
        tuple(
            run_real_corpus_preflight.benchmark_document_understanding._as_material_role(role)
            for role in cast("list[str]", args.require_role)
        )
        or run_real_corpus_preflight.DEFAULT_REQUIRED_ROLES
    )
    required_stressors = (
        tuple(cast("list[str]", args.require_stressor))
        or run_real_corpus_preflight.DEFAULT_REQUIRED_STRESSORS
    )
    try:
        report = prepare_evidence(
            cast("Path", args.armory).expanduser().resolve(),
            cast("Path", args.output_dir).expanduser().resolve(),
            corpus_id=cast("str", args.id),
            description=cast("str", args.description),
            corpus_kind=cast("str", args.corpus_kind),
            domain=cast("str", args.domain),
            infer_roles_from_index=not cast("bool", args.no_infer_roles_from_index),
            reviewed_manifest=cast("bool", args.reviewed_manifest),
            min_documents=int(args.min_documents),
            min_domains=int(args.min_domains),
            min_roles=int(args.min_roles),
            min_document_types=int(args.min_document_types),
            min_stressors=int(args.min_stressors),
            required_stressors=required_stressors,
            required_roles=required_roles,
            min_role_confidence=min_role_confidence,
            min_overview_source_coverage=min_overview_source_coverage,
        )
    except OSError as exc:
        print(f"real corpus evidence preparation error: {exc}", file=sys.stderr)
        return 2

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
