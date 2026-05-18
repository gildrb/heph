"""Export Hephaistos EnterpriseRAG retrieval results to leaderboard JSONL.

The official EnterpriseRAG-Bench answer format requires original ``dsid_...``
document identifiers:

``{"question_id": "qst_0001", "answer": "...", "document_ids": ["dsid_..."]}``

This exporter reads a Hephaistos external-runner report and the suite's
``material_metadata.jsonl`` to convert retrieved ``materials/...`` references
back into official document IDs. It can emit document-only rows for retrieval
recall or include answer text from a separate JSONL file when full answer
evaluation is available.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast


class ExportError(Exception):
    """Expected export failure."""


def export_answers(
    report_path: Path,
    material_metadata_path: Path,
    output_path: Path,
    *,
    answers_path: Path | None = None,
) -> dict[str, object]:
    """Write EnterpriseRAG leaderboard-format answers from a runner report."""
    source_by_material = _load_material_source_map(material_metadata_path)
    answer_by_question = _load_answers(answers_path) if answers_path is not None else {}
    report = _read_json_object(report_path, label="runner report")
    rows = _answer_rows(report, source_by_material, answer_by_question)
    if not rows:
        raise ExportError("runner report did not contain any per-query retrieval rows")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return {
        "status": "success",
        "report": str(report_path.expanduser().resolve()),
        "material_metadata": str(material_metadata_path.expanduser().resolve()),
        "answers_file": str(answers_path.expanduser().resolve()) if answers_path else "",
        "output": str(output_path.expanduser().resolve()),
        "rows": len(rows),
        "rows_with_answers": sum(1 for row in rows if row.get("answer")),
    }


def _read_json_object(path: Path, *, label: str) -> dict[str, object]:
    try:
        raw = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except OSError as exc:
        raise ExportError(f"could not read {label}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ExportError(f"{label} contains invalid JSON at line {exc.lineno}: {path}") from exc
    if not isinstance(raw, dict):
        raise ExportError(f"{label} must be a JSON object: {path}")
    return cast("dict[str, object]", raw)


def _load_material_source_map(path: Path) -> dict[str, str]:
    source_by_material: dict[str, str] = {}
    try:
        lines = path.expanduser().read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ExportError(f"could not read material metadata: {path}") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ExportError(
                f"material metadata contains invalid JSON at line {line_number}: {path}"
            ) from exc
        if not isinstance(raw, dict):
            raise ExportError(f"material metadata line {line_number} must be an object")
        source_id = raw.get("source_id")
        original_id = _official_document_id(raw)
        if not isinstance(source_id, str) or not isinstance(original_id, str):
            raise ExportError(
                f"material metadata line {line_number} lacks source_id/original_document_id"
            )
        source_by_material[source_id] = original_id
    if not source_by_material:
        raise ExportError(f"material metadata is empty: {path}")
    return source_by_material


def _official_document_id(raw: Mapping[str, object]) -> object:
    metadata = raw.get("metadata")
    if isinstance(metadata, dict):
        official_id = metadata.get("enterprise_rag_document_id")
        if isinstance(official_id, str) and official_id.strip():
            return official_id.strip()
    return raw.get("original_document_id")


def _load_answers(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    answer_by_question: dict[str, str] = {}
    try:
        lines = path.expanduser().read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ExportError(f"could not read answers file: {path}") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ExportError(f"answers file contains invalid JSON at line {line_number}") from exc
        if not isinstance(raw, dict):
            raise ExportError(f"answers file line {line_number} must be an object")
        question_id = raw.get("question_id")
        answer = raw.get("answer")
        if isinstance(question_id, str) and isinstance(answer, str):
            answer_by_question[question_id] = answer
    return answer_by_question


def _answer_rows(
    report: Mapping[str, object],
    source_by_material: Mapping[str, str],
    answer_by_question: Mapping[str, str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for result in _per_query_results(report):
        case_id = _required_string(result, "case_id")
        question_id = _question_id(case_id)
        retrieved = result.get("retrieved")
        if not isinstance(retrieved, list):
            raise ExportError(f"{case_id} retrieved field must be a list")
        document_ids = _official_doc_ids(retrieved, source_by_material, case_id=case_id)
        row: dict[str, object] = {
            "question_id": question_id,
            "document_ids": document_ids,
        }
        answer = answer_by_question.get(question_id, "")
        if answer:
            row["answer"] = answer
        rows.append(row)
    return rows


def _per_query_results(report: Mapping[str, object]) -> list[dict[str, object]]:
    raw_benchmarks = report.get("benchmarks")
    if not isinstance(raw_benchmarks, list) or not raw_benchmarks:
        raise ExportError("runner report is missing benchmarks")
    first = raw_benchmarks[0]
    if not isinstance(first, dict):
        raise ExportError("runner report benchmark entry must be an object")
    raw_results = first.get("per_query_results")
    if not isinstance(raw_results, list):
        raise ExportError("runner report is missing per_query_results")
    results: list[dict[str, object]] = []
    for index, raw_result in enumerate(raw_results, start=1):
        if not isinstance(raw_result, dict):
            raise ExportError(f"per_query_results item {index} must be an object")
        results.append(cast("dict[str, object]", raw_result))
    return results


def _required_string(row: Mapping[str, object], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ExportError(f"per-query result must include non-empty {key}")
    return value.strip()


def _question_id(case_id: str) -> str:
    prefix = "enterprise-rag-enterprise-rag-bench-test-"
    if case_id.startswith(prefix):
        return case_id.removeprefix(prefix)
    if case_id.startswith("enterprise-rag-bench-"):
        return case_id.removeprefix("enterprise-rag-bench-")
    return case_id


def _official_doc_ids(
    retrieved: Sequence[object],
    source_by_material: Mapping[str, str],
    *,
    case_id: str,
) -> list[str]:
    document_ids: list[str] = []
    seen: set[str] = set()
    for raw_ref in retrieved:
        if not isinstance(raw_ref, str):
            raise ExportError(f"{case_id} retrieved references must be strings")
        source = raw_ref.split("#", 1)[0]
        official_id = source_by_material.get(source)
        if official_id is None:
            raise ExportError(f"{case_id} retrieved unknown material source: {source}")
        if official_id in seen:
            continue
        seen.add(official_id)
        document_ids.append(official_id)
    return document_ids


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Hephaistos external runner JSON report")
    parser.add_argument(
        "material_metadata",
        type=Path,
        help="EnterpriseRAG suite material_metadata.jsonl",
    )
    parser.add_argument("output", type=Path, help="Leaderboard-format answers JSONL")
    parser.add_argument(
        "--answers-file",
        type=Path,
        help="Optional JSONL with question_id/answer text to merge into output rows",
    )
    parser.add_argument("--json-report", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        report = export_answers(
            cast("Path", args.report),
            cast("Path", args.material_metadata),
            cast("Path", args.output),
            answers_path=cast("Path | None", args.answers_file),
        )
        status = 0
    except ExportError as exc:
        report = {
            "status": "error",
            "report": str(cast("Path", args.report).expanduser()),
            "material_metadata": str(cast("Path", args.material_metadata).expanduser()),
            "output": str(cast("Path", args.output).expanduser()),
            "rows": 0,
            "error": str(exc),
        }
        status = 2
    json_report = cast("Path | None", args.json_report)
    if json_report is not None:
        json_report.parent.mkdir(parents=True, exist_ok=True)
        json_report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
