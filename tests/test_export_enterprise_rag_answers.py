from __future__ import annotations

import json
from pathlib import Path

from scripts import export_enterprise_rag_answers


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def test_export_enterprise_rag_answers_maps_materials_back_to_official_ids(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "runner.json"
    material_metadata_path = tmp_path / "material_metadata.jsonl"
    answers_path = tmp_path / "answers.jsonl"
    output_path = tmp_path / "leaderboard.jsonl"
    json_report_path = tmp_path / "export-report.json"

    report_path.write_text(
        json.dumps(
            {
                "benchmarks": [
                    {
                        "per_query_results": [
                            {
                                "case_id": ("enterprise-rag-enterprise-rag-bench-test-qst_0001"),
                                "retrieved": [
                                    "materials/dsid_alpha.md#chunk=0",
                                    "materials/dsid_beta__enterprise_duplicate_2.md#chunk=1",
                                    "materials/dsid_alpha.md#chunk=2",
                                ],
                            }
                        ]
                    }
                ]
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_jsonl(
        material_metadata_path,
        [
            {
                "source_id": "materials/dsid_alpha.md",
                "original_document_id": "dsid_alpha",
            },
            {
                "source_id": "materials/dsid_beta__enterprise_duplicate_2.md",
                "original_document_id": "dsid_beta__enterprise_duplicate_2",
                "metadata": {"enterprise_rag_document_id": "dsid_beta"},
            },
        ],
    )
    _write_jsonl(
        answers_path,
        [{"question_id": "qst_0001", "answer": "The limit is 10 MiB per file."}],
    )

    status = export_enterprise_rag_answers.main(
        [
            str(report_path),
            str(material_metadata_path),
            str(output_path),
            "--answers-file",
            str(answers_path),
            "--json-report",
            str(json_report_path),
        ]
    )

    rows = _read_jsonl(output_path)
    export_report = json.loads(json_report_path.read_text(encoding="utf-8"))

    assert status == 0
    assert rows == [
        {
            "answer": "The limit is 10 MiB per file.",
            "document_ids": ["dsid_alpha", "dsid_beta"],
            "question_id": "qst_0001",
        }
    ]
    assert export_report["status"] == "success"
    assert export_report["rows"] == 1
    assert export_report["rows_with_answers"] == 1
