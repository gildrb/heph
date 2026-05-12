"""Build a benchmark armory from permissioned local academic documents.

The command copies visible documents from one or more local folders into a new
armory, records file:// provenance in a benchmark manifest scaffold, and leaves
strict preflight/audit checks to decide whether the corpus is broad enough.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from hephaistos.armory import storage
from scripts import create_benchmark_manifest

_SUPPORTED_SUFFIXES = frozenset(
    {
        ".csv",
        ".docx",
        ".md",
        ".pdf",
        ".pptx",
        ".rst",
        ".tex",
        ".txt",
        ".xlsx",
    }
)


@dataclass(frozen=True, slots=True)
class BuiltPermissionedCorpus:
    status: int
    armory_path: str
    manifest_path: str
    copied_documents: int
    skipped_documents: int
    failures: tuple[str, ...]


def build_corpus(
    input_paths: tuple[Path, ...],
    armory_path: Path,
    manifest_path: Path,
    *,
    corpus_id: str = "permissioned-local-academic-corpus",
    description: str = "Permissioned local academic benchmark corpus.",
    corpus_kind: str = "permissioned-materials",
    domain: str = "unlabelled",
    limit: int = 0,
    overwrite: bool = False,
) -> BuiltPermissionedCorpus:
    """Copy local documents into an armory and write a manifest scaffold."""
    armory_path = armory_path.expanduser().resolve()
    manifest_path = manifest_path.expanduser().resolve()
    inputs = tuple(path.expanduser().resolve() for path in input_paths)
    failures = _input_failures(inputs)
    if failures:
        return BuiltPermissionedCorpus(
            status=2,
            armory_path=str(armory_path),
            manifest_path=str(manifest_path),
            copied_documents=0,
            skipped_documents=0,
            failures=failures,
        )
    storage.initialize(armory_path)
    selected, skipped = _select_documents(inputs, limit=limit)
    if not selected:
        return BuiltPermissionedCorpus(
            status=2,
            armory_path=str(armory_path),
            manifest_path=str(manifest_path),
            copied_documents=0,
            skipped_documents=skipped,
            failures=("no supported documents found",),
        )
    provenance: dict[str, str] = {}
    copied = 0
    for source in selected:
        destination = _destination_for(source, armory_path / storage.MATERIALS_DIR)
        if destination.exists() and not overwrite:
            return BuiltPermissionedCorpus(
                status=2,
                armory_path=str(armory_path),
                manifest_path=str(manifest_path),
                copied_documents=copied,
                skipped_documents=skipped,
                failures=(f"destination already exists: {destination}",),
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        rel = destination.relative_to(armory_path).as_posix()
        provenance[rel] = source.as_uri()
        copied += 1

    manifest = create_benchmark_manifest.create_manifest(
        armory_path,
        corpus_id=corpus_id,
        description=description,
        corpus_kind=corpus_kind,
        domain=domain,
        infer_roles_from_index=False,
    )
    for document in manifest["documents"]:
        document["source_url"] = provenance.get(document["source"], "")
        if document["source_url"]:
            document["permission_note"] = "Local permissioned material copied from this machine."
    create_benchmark_manifest.write_manifest(manifest_path, manifest)
    _write_placeholder_datasets(manifest_path.parent, manifest["datasets"])
    return BuiltPermissionedCorpus(
        status=0,
        armory_path=str(armory_path),
        manifest_path=str(manifest_path),
        copied_documents=copied,
        skipped_documents=skipped,
        failures=(),
    )


def _input_failures(inputs: tuple[Path, ...]) -> tuple[str, ...]:
    failures: list[str] = []
    if not inputs:
        failures.append("at least one input path is required")
    failures.extend(f"input path does not exist: {path}" for path in inputs if not path.exists())
    return tuple(failures)


def _select_documents(inputs: tuple[Path, ...], *, limit: int) -> tuple[tuple[Path, ...], int]:
    candidates: list[Path] = []
    skipped = 0
    for input_path in inputs:
        paths = [input_path] if input_path.is_file() else sorted(input_path.rglob("*"))
        for path in paths:
            if not path.is_file():
                continue
            if any(part.startswith(".") for part in path.parts):
                skipped += 1
                continue
            if path.suffix.casefold() not in _SUPPORTED_SUFFIXES:
                skipped += 1
                continue
            candidates.append(path)
            if limit > 0 and len(candidates) >= limit:
                return tuple(candidates), skipped
    return tuple(candidates), skipped


def _destination_for(source: Path, materials_dir: Path) -> Path:
    stable_name = _stable_filename(source)
    return materials_dir / stable_name


def _stable_filename(source: Path) -> str:
    stem = source.stem.strip().replace("/", "-")
    prefix = source.parent.name.strip().replace("/", "-")
    if prefix:
        stem = f"{prefix}-{stem}"
    return f"{stem}{source.suffix.lower()}"


def _write_placeholder_datasets(
    suite_dir: Path,
    datasets: list[create_benchmark_manifest.ManifestDataset],
) -> None:
    for dataset in datasets:
        dataset_path = suite_dir / dataset["path"]
        if dataset_path.exists():
            continue
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        dataset_path.write_text(_placeholder_dataset_text(dataset["kind"]), encoding="utf-8")


def _placeholder_dataset_text(kind: str) -> str:
    if kind == "chat-event-answer-expectation":
        return "[]\n"
    if kind.endswith("expectation"):
        return "{}\n"
    return ""


def print_text_report(report: BuiltPermissionedCorpus) -> None:
    print(f"Built permissioned corpus armory: {report.armory_path}")
    print(f"status={report.status}")
    print(f"manifest={report.manifest_path}")
    print(f"copied_documents={report.copied_documents}")
    print(f"skipped_documents={report.skipped_documents}")
    if report.failures:
        print("failures:")
        for failure in report.failures:
            print(f"  - {failure}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("armory", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--id", default="permissioned-local-academic-corpus")
    parser.add_argument("--description", default="Permissioned local academic benchmark corpus.")
    parser.add_argument("--corpus-kind", default="permissioned-materials")
    parser.add_argument("--domain", default="unlabelled")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json-report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    limit = int(args.limit)
    if limit < 0:
        parser.error("--limit must be non-negative")
    report = build_corpus(
        tuple(cast("list[Path]", args.inputs)),
        cast("Path", args.armory),
        cast("Path", args.manifest),
        corpus_id=cast("str", args.id),
        description=cast("str", args.description),
        corpus_kind=cast("str", args.corpus_kind),
        domain=cast("str", args.domain),
        limit=limit,
        overwrite=cast("bool", args.overwrite),
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
