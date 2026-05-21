"""Create a benchmark manifest scaffold from an armory's material files.

This does not claim semantic labels are correct. It creates a machine-checkable
starting point for a public or permissioned corpus so humans can review domains,
roles, document types, stressors, datasets, and known limits before running
strict manifest gates.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from hephaistos.materials import (
    MaterialFile,
    MaterialRole,
    infer_material_role_from_text,
    material_manifest,
)
from hephaistos.rag import load_or_build


class ManifestDocument(TypedDict):
    source: str
    domain: str
    role: str
    document_type: str
    stressors: list[str]
    source_url: str
    permission_note: str


class ManifestDataset(TypedDict):
    path: str
    kind: str


class GeneratedManifest(TypedDict):
    id: str
    description: str
    corpus_kind: str
    documents: list[ManifestDocument]
    datasets: list[ManifestDataset]
    known_limits: list[str]
    generated_from_armory: NotRequired[str]


_DEFAULT_DATASETS: tuple[ManifestDataset, ...] = (
    {"path": "rag.jsonl", "kind": "retrieval"},
    {"path": "material_roles.jsonl", "kind": "material-roles"},
    {"path": "priority.jsonl", "kind": "priority"},
    {"path": "answers.jsonl", "kind": "grounded-answers"},
    {"path": "chat_events.jsonl", "kind": "chat-events"},
    {"path": "chat_event_expectation.json", "kind": "chat-event-answer-expectation"},
    {"path": "replay.jsonl", "kind": "model-replay-prompts"},
    {"path": "learning_state.jsonl", "kind": "study-state"},
)
_TABLE_ROW_RE = re.compile(r"(?:^|\n)\s*\S+(?:\s{2,}|\t|\|)\S+(?:\s{2,}|\t|\|)\S+")
_EXTRACTION_NOISE_RE = re.compile(r"\w[\u00a8\u00b4\u02c6`]\w|\ufffd|[|Il1]{6,}")
_MATH_NOTATION_RE = re.compile(r"[∑∫√∞≤≥≈≠→↔]|\\(?:sum|int|frac|sqrt|begin)\b")
_GERMAN_ACADEMIC_RE = re.compile(
    r"\b(?:aufgabe|übung|uebung|klausur|vorlesung|beweis|satz|lösung|loesung)\b",
    re.IGNORECASE,
)


def create_manifest(
    armory_path: Path,
    *,
    corpus_id: str = "external-academic-corpus",
    description: str = "External academic benchmark corpus.",
    corpus_kind: str = "permissioned-materials",
    domain: str = "unlabelled",
    include_default_datasets: bool = True,
    infer_roles_from_index: bool = False,
    reviewed: bool = False,
) -> GeneratedManifest:
    """Create a manifest scaffold from visible materials in an armory."""
    indexed_text = _indexed_text_by_source(armory_path) if infer_roles_from_index else {}
    documents = [
        _document_entry(
            material,
            default_domain=domain,
            inferred_role=_content_role(material, indexed_text),
            indexed_text=indexed_text.get(material.rel_path, ""),
        )
        for material in material_manifest(armory_path)
    ]
    if not documents:
        raise ValueError(f"armory has no visible material files: {armory_path}")

    manifest: GeneratedManifest = {
        "id": corpus_id,
        "description": description,
        "corpus_kind": corpus_kind,
        "documents": documents,
        "datasets": [dict(dataset) for dataset in _DEFAULT_DATASETS]
        if include_default_datasets
        else [],
        "known_limits": []
        if reviewed
        else [
            "Generated scaffold: domains, stressors, and roles require human review.",
            "Document provenance requires human review.",
            "No model-backed run result is committed.",
        ],
        "generated_from_armory": str(armory_path),
    }
    return manifest


def _indexed_text_by_source(armory_path: Path) -> dict[str, str]:
    index = load_or_build(armory_path)
    return {
        document.source: " ".join(chunk.text for chunk in document.chunks)
        for document in index.documents
        if document.chunks
    }


def _content_role(
    material: MaterialFile,
    indexed_text: dict[str, str],
) -> MaterialRole:
    text = indexed_text.get(material.rel_path, "")
    if not text:
        return material.role
    role, _confidence, _reason = infer_material_role_from_text(material.rel_path, text)
    return role


def _document_entry(
    material: MaterialFile,
    *,
    default_domain: str,
    inferred_role: MaterialRole,
    indexed_text: str = "",
) -> ManifestDocument:
    return {
        "source": material.rel_path,
        "domain": default_domain,
        "role": inferred_role,
        "document_type": _document_type(material, role=inferred_role, indexed_text=indexed_text),
        "stressors": _stressors(material, role=inferred_role, indexed_text=indexed_text),
        "source_url": "",
        "permission_note": "",
    }


def _document_type(
    material: MaterialFile,
    *,
    role: MaterialRole,
    indexed_text: str = "",
) -> str:
    suffix = material.path.suffix.lower()
    rel_lower = material.rel_path.lower()
    if role == "past_exam":
        return "past-exam"
    if role == "assignment":
        return "exercise-sheet"
    if _has_any(rel_lower, ("solution", "solutions", "lösung", "loesung")):
        return "solutions"
    if _has_any(rel_lower, ("scan", "ocr", "fototopdf", "pdf_upload")):
        return "scanned-pdf"
    if _has_any(rel_lower, ("cheatsheet", "cheat-sheet", "summary", "zusammenfassung")):
        return "cheatsheet"
    if _has_any(rel_lower, ("handout_4x4", "handout-4x4", "_4x4", "-4x4")):
        return "multi-slide-handout"
    if _has_any(rel_lower, ("syllabus", "information", "informationsblatt")):
        return "syllabus"
    if role == "slides":
        return "slide-deck" if suffix in (".ppt", ".pptx") else "lecture-slides"
    if suffix == ".pdf" and _has_table_like_text(indexed_text):
        return "table-heavy-pdf"
    if suffix == ".pdf":
        return "pdf"
    if suffix in (".md", ".txt", ".rst"):
        return "notes"
    if suffix in (".tex", ".latex"):
        return "latex-source"
    if suffix in (".csv", ".tsv", ".xlsx", ".xls"):
        return "table"
    return suffix.lstrip(".") or "unknown"


def _stressors(
    material: MaterialFile,
    *,
    role: MaterialRole,
    indexed_text: str = "",
) -> list[str]:
    stressors: set[str] = {role}
    suffix = material.path.suffix.lower()
    rel_lower = material.rel_path.lower()
    text_sample = indexed_text[:20_000]
    if suffix == ".pdf":
        stressors.add("real-pdf")
    if suffix in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
        stressors.update(("scan-image", "ocr-needed"))
    if suffix in (".tex", ".latex") or "\\" in material.path.name:
        stressors.add("formula-language")
    if suffix in (".csv", ".tsv", ".xlsx", ".xls"):
        stressors.add("table-heavy")
    if role == "past_exam":
        stressors.add("exam-format")
    if role == "assignment":
        stressors.add("exercise-sheet")
    if role in ("lecture", "slides"):
        stressors.add("lecture-material")
    if _has_any(rel_lower, ("solution", "solutions", "lösung", "loesung")):
        stressors.add("worked-solution")
    if _has_any(rel_lower, ("scan", "ocr", "fototopdf", "pdf_upload")):
        stressors.update(("ocr-noise", "scanned-pdf"))
    if _has_any(rel_lower, ("cheatsheet", "cheat-sheet", "summary", "zusammenfassung")):
        stressors.update(("dense-reference", "table-heavy"))
    if _has_any(rel_lower, ("handout_4x4", "handout-4x4", "_4x4", "-4x4")):
        stressors.add("multi-column")
    if _has_any(rel_lower, ("syllabus", "information", "informationsblatt")):
        stressors.add("syllabus")
    if any(ord(char) > 127 for char in material.rel_path):
        stressors.update(("unicode", "multilingual"))
    if text_sample:
        if _has_table_like_text(text_sample):
            stressors.update(("table-heavy", "tabular-text"))
        if _has_multilingual_text(text_sample):
            stressors.update(("unicode", "multilingual"))
        if _has_extraction_noise(text_sample):
            stressors.update(("ocr-noise", "noisy-text-extraction"))
        if _has_math_notation(text_sample):
            stressors.update(("formula-language", "math-notation"))
    if any(token in rel_lower for token in ("scan", "ocr")):
        stressors.add("ocr-noise")
    if any(token in rel_lower for token in ("multi-column", "multicolumn", "zweispaltig")):
        stressors.add("multi-column")
    return sorted(stressors)


def _has_table_like_text(text: str) -> bool:
    return len(_TABLE_ROW_RE.findall(text)) >= 3


def _has_multilingual_text(text: str) -> bool:
    return any(ord(char) > 127 for char in text) or bool(_GERMAN_ACADEMIC_RE.search(text))


def _has_extraction_noise(text: str) -> bool:
    return bool(_EXTRACTION_NOISE_RE.search(text))


def _has_math_notation(text: str) -> bool:
    return bool(_MATH_NOTATION_RE.search(text))


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def write_manifest(path: Path, manifest: GeneratedManifest) -> None:
    """Write a generated manifest as pretty JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("armory", type=Path, help="Armory path containing materials/")
    parser.add_argument("output", type=Path, help="Output manifest JSON path")
    parser.add_argument("--id", default="external-academic-corpus")
    parser.add_argument("--description", default="External academic benchmark corpus.")
    parser.add_argument("--corpus-kind", default="permissioned-materials")
    parser.add_argument("--domain", default="unlabelled")
    parser.add_argument(
        "--no-default-datasets",
        action="store_true",
        help="Do not include placeholder dataset declarations",
    )
    parser.add_argument(
        "--infer-roles-from-index",
        action="store_true",
        help="Use indexed document text to infer roles when available.",
    )
    parser.add_argument(
        "--reviewed",
        action="store_true",
        help="Mark the manifest as reviewed and do not add scaffold known_limits.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    armory = cast("Path", args.armory).expanduser().resolve()
    output = cast("Path", args.output).expanduser().resolve()
    try:
        manifest = create_manifest(
            armory,
            corpus_id=cast("str", args.id),
            description=cast("str", args.description),
            corpus_kind=cast("str", args.corpus_kind),
            domain=cast("str", args.domain),
            include_default_datasets=not cast("bool", args.no_default_datasets),
            infer_roles_from_index=cast("bool", args.infer_roles_from_index),
            reviewed=cast("bool", args.reviewed),
        )
        write_manifest(output, manifest)
    except (OSError, ValueError) as exc:
        print(f"benchmark manifest generation error: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote benchmark manifest scaffold to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
