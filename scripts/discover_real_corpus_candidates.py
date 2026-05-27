"""Discover armories that may be suitable for real academic corpus evaluation."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from hephaion.armory import storage
from hephaion.materials import material_manifest
from scripts import run_real_corpus_preflight


@dataclass(frozen=True, slots=True)
class RealCorpusCandidate:
    armory_path: str
    visible_materials: int
    roles: dict[str, int]
    extensions: dict[str, int]
    failures: tuple[str, ...]

    @property
    def passes(self) -> bool:
        return not self.failures


@dataclass(frozen=True, slots=True)
class RealCorpusDiscoveryReport:
    status: int
    root: str
    min_documents: int
    min_roles: int
    candidates: tuple[RealCorpusCandidate, ...]
    passing_candidates: tuple[str, ...]
    failures: tuple[str, ...]
    next_steps: tuple[str, ...]


def discover_candidates(
    root: Path,
    *,
    min_documents: int = run_real_corpus_preflight.DEFAULT_MIN_DOCUMENTS,
    min_roles: int = run_real_corpus_preflight.DEFAULT_MIN_ROLES,
    require_candidate: bool = False,
) -> RealCorpusDiscoveryReport:
    """Scan direct child armories and summarize corpus-readiness signals."""
    root = root.expanduser().resolve()
    failures: list[str] = []
    candidates: list[RealCorpusCandidate] = []
    if not root.is_dir():
        failures.append(f"root is not a directory: {root}")
    else:
        for path in sorted(child for child in root.iterdir() if child.is_dir()):
            if not _looks_like_armory(path):
                continue
            candidates.append(
                _candidate_report(path, min_documents=min_documents, min_roles=min_roles)
            )

    candidates.sort(key=lambda candidate: (-candidate.visible_materials, candidate.armory_path))
    passing_candidates = tuple(
        candidate.armory_path for candidate in candidates if candidate.passes
    )
    if require_candidate and not passing_candidates:
        failures.append(
            "no armory meets real-corpus candidate thresholds "
            f"(min_documents={min_documents}, min_roles={min_roles})"
        )
    next_steps = _next_steps(passing_candidates)

    return RealCorpusDiscoveryReport(
        status=1 if failures else 0,
        root=str(root),
        min_documents=min_documents,
        min_roles=min_roles,
        candidates=tuple(candidates),
        passing_candidates=passing_candidates,
        failures=tuple(failures),
        next_steps=next_steps,
    )


def _looks_like_armory(path: Path) -> bool:
    return (path / storage.MARKER_FILE).is_file() or (path / storage.MATERIALS_DIR).is_dir()


def _candidate_report(path: Path, *, min_documents: int, min_roles: int) -> RealCorpusCandidate:
    try:
        materials = material_manifest(path)
    except OSError as exc:
        return RealCorpusCandidate(
            armory_path=str(path),
            visible_materials=0,
            roles={},
            extensions={},
            failures=(f"material scan failed: {exc}",),
        )

    role_counts = Counter(material.role for material in materials)
    extension_counts = Counter(_extension(material.path) for material in materials)
    failures: list[str] = []
    if len(materials) < min_documents:
        failures.append(f"visible material count {len(materials)} below required {min_documents}")
    role_types = sum(1 for count in role_counts.values() if count > 0)
    if role_types < min_roles:
        failures.append(f"material role variety {role_types} below required {min_roles}")
    return RealCorpusCandidate(
        armory_path=str(path),
        visible_materials=len(materials),
        roles=dict(sorted(role_counts.items())),
        extensions=dict(sorted(extension_counts.items())),
        failures=tuple(failures),
    )


def _extension(path: Path) -> str:
    suffix = path.suffix.lower()
    return suffix or "<none>"


def print_text_report(report: RealCorpusDiscoveryReport) -> None:
    print(f"Real corpus candidate discovery: {report.root}")
    print(f"status={report.status}")
    print(f"min_documents={report.min_documents}")
    print(f"min_roles={report.min_roles}")
    if report.failures:
        print("failures:")
        for failure in report.failures:
            print(f"  - {failure}")
    if not report.candidates:
        print("candidates: none")
        return
    print("candidates:")
    for candidate in report.candidates:
        status = "pass" if candidate.passes else "fail"
        roles = _format_counts(candidate.roles)
        extensions = _format_counts(candidate.extensions)
        print(f"  - {status}: {candidate.armory_path}")
        print(
            f"    materials={candidate.visible_materials}; roles={roles}; extensions={extensions}"
        )
        for failure in candidate.failures:
            print(f"    failure: {failure}")
    if report.next_steps:
        print("next steps:")
        for step in report.next_steps:
            print(f"  - {step}")


def _next_steps(passing_candidates: tuple[str, ...]) -> tuple[str, ...]:
    if not passing_candidates:
        return ()
    armory_path = passing_candidates[0]
    return (
        "uv run python -m scripts.prepare_real_corpus_evidence "
        f"{armory_path} .artifacts/real-corpus-evidence",
        "uv run python -m scripts.run_model_eval_matrix "
        f"{armory_path} path/to/replay.jsonl path/to/model-matrix.json "
        ".artifacts/model-eval --validate-inputs "
        "--json-report .artifacts/model-eval/matrix.inputs.json",
    )


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in counts.items())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path.home() / ".armories",
        help="Directory containing armory folders",
    )
    parser.add_argument(
        "--min-documents",
        type=int,
        default=run_real_corpus_preflight.DEFAULT_MIN_DOCUMENTS,
    )
    parser.add_argument(
        "--min-roles",
        type=int,
        default=run_real_corpus_preflight.DEFAULT_MIN_ROLES,
        help="Minimum distinct broad material roles required for a candidate.",
    )
    parser.add_argument(
        "--require-candidate",
        action="store_true",
        help="Exit non-zero when no armory meets --min-documents",
    )
    parser.add_argument("--json-report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    min_documents = int(args.min_documents)
    if min_documents < 1:
        parser.error("--min-documents must be at least 1")
    min_roles = int(args.min_roles)
    if min_roles < 1:
        parser.error("--min-roles must be at least 1")
    report = discover_candidates(
        cast("Path", args.root),
        min_documents=min_documents,
        min_roles=min_roles,
        require_candidate=bool(args.require_candidate),
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
