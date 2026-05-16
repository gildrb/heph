from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from scripts.external_benchmarks import standard_rag_adapter
from scripts.external_benchmarks.conversion import MATERIAL_METADATA_NAME, RAG_DATASET_NAME


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def _as_dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast("dict[str, object]", value)


def _as_list(value: object) -> list[object]:
    assert isinstance(value, list)
    return cast("list[object]", value)


def _standard_manifest(tmp_path: Path) -> Path:
    manifest = tmp_path / "standard-rag.json"
    manifest.write_text(
        json.dumps(
            {
                "dataset": "fixture-standard-rag",
                "split": "dev",
                "domain": "medicine",
                "task_type": "qa-retrieval",
                "documents": [
                    {
                        "id": "source-a",
                        "title": "Source A",
                        "text": "Source A explains the target answer for the first question.",
                        "source_url": "https://example.edu/source-a",
                        "metadata": {"role": "paper"},
                    },
                    {
                        "id": "source-b",
                        "title": "Source B",
                        "content": "Source B is related but should not be a positive reference.",
                        "metadata": {"role": "reading"},
                    },
                    {
                        "id": "source-c",
                        "title": "Source C",
                        "body": "Source C answers the second question.",
                        "metadata": {"role": "guideline"},
                    },
                ],
                "queries": [
                    {
                        "id": "question-a",
                        "question": "Which source explains the target answer?",
                        "answer": "Source A",
                        "relevant_documents": [
                            {"document_id": "source-a", "grade": 1},
                            {"document_id": "source-b", "grade": 0},
                        ],
                        "metadata": {"difficulty": "easy"},
                    },
                    {
                        "id": "question-c",
                        "query": "Which source answers the second question?",
                        "answers": ["Source C"],
                        "relevance": {"source-c": 2},
                    },
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def test_standard_rag_adapter_converts_manifest_to_armory_cases(tmp_path: Path) -> None:
    manifest = _standard_manifest(tmp_path)
    output = tmp_path / "out"
    report_path = tmp_path / "report.json"

    status = standard_rag_adapter.main(
        [
            "ms-marco",
            "--manifest",
            str(manifest),
            "--output",
            str(output),
            "--json-report",
            str(report_path),
        ]
    )

    assert status == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "success"
    assert report["adapter"] == "standard-rag"
    assert report["dataset"] == "fixture-standard-rag"
    assert report["source_format"] == "standard-rag-manifest"
    assert report["counts"]["documents"] == 3
    assert report["counts"]["queries"] == 2
    assert report["counts"]["qrels"] == 3
    assert report["counts"]["cases"] == 2
    assert report["relevance"]["grade_distribution"] == {"0": 1, "1": 1, "2": 1}

    cases = _read_jsonl(output / RAG_DATASET_NAME)
    first_case = cases[0]
    assert first_case["domain"] == "medicine"
    assert first_case["task"] == "qa-retrieval"
    assert first_case["expected"] == ["materials/source-a.md"]
    metadata = _as_dict(first_case["metadata"])
    assert metadata["answers"] == ["Source A"]
    assert metadata["query_metadata"] == {"difficulty": "easy"}
    judgments = _as_list(metadata["relevance_judgments"])
    assert _as_dict(judgments[1])["positive"] is False
    assert (output / "armory" / "materials" / "source-a.md").read_text(encoding="utf-8")
    material_metadata = _read_jsonl(output / MATERIAL_METADATA_NAME)
    assert material_metadata[0]["source_url"] == "https://example.edu/source-a"
    assert _as_dict(material_metadata[0]["metadata"])["role"] == "paper"


def test_standard_rag_adapter_rejects_named_dataset_without_manifest(
    tmp_path: Path,
) -> None:
    output = tmp_path / "out"
    report_path = tmp_path / "report.json"

    status = standard_rag_adapter.main(
        ["natural-questions", "--output", str(output), "--json-report", str(report_path)]
    )

    assert status == 2
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "error"
    assert report["error"]["code"] == "dataset_requires_manifest"
    assert "Pass --manifest" in report["error"]["remediation"]
    assert not output.exists()
