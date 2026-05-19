from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from scripts.external_benchmarks import mteb_adapter
from scripts.external_benchmarks.conversion import MATERIAL_METADATA_NAME, RAG_DATASET_NAME


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def _read_report(path: Path) -> dict[str, object]:
    return cast("dict[str, object]", json.loads(path.read_text(encoding="utf-8")))


def _as_dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast("dict[str, object]", value)


def _mteb_fixture(tmp_path: Path) -> Path:
    fixture = tmp_path / "mteb-fixture"
    _write_jsonl(
        fixture / "corpus" / "corpus-00000-of-00001.jsonl",
        [
            {
                "id": "doc-alpha",
                "title": "Alpha MTEB document",
                "text": "Alpha source explains retrieval with MTEB secondary gates.",
                "metadata": {"source_url": "https://example.edu/mteb-alpha"},
            },
            {
                "id": "doc-beta",
                "title": "Beta MTEB document",
                "text": "Beta source is a non-relevant distractor.",
            },
            {
                "id": "doc-gamma",
                "title": "Gamma MTEB document",
                "text": "Gamma source covers a second retrieval question.",
            },
        ],
    )
    _write_jsonl(
        fixture / "queries" / "test.jsonl",
        [
            {
                "id": "query-1",
                "instruction": "Retrieve a relevant passage.",
                "text": "Which source explains MTEB secondary gates?",
            },
            {"id": "query-2", "text": "Which source covers the second retrieval question?"},
        ],
    )
    _write_jsonl(
        fixture / "data" / "test-00000-of-00001.jsonl",
        [
            {"query-id": "query-1", "corpus-id": "doc-alpha", "score": 1},
            {"query-id": "query-1", "corpus-id": "doc-beta", "score": 0},
            {"query-id": "query-2", "corpus-id": "doc-gamma", "score": 2},
        ],
    )
    return fixture


def test_mteb_adapter_maps_relevant_docs_to_expected_references(tmp_path: Path) -> None:
    source = _mteb_fixture(tmp_path)
    output = tmp_path / "out"
    report_path = tmp_path / "report.json"

    status = mteb_adapter.main(
        [
            "mteb/fixture",
            "--source-dir",
            str(source),
            "--output",
            str(output),
            "--top-k",
            "11",
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    assert status == 0
    assert report["status"] == "success"
    assert report["adapter"] == "mteb"
    assert report["dataset"] == "mteb/fixture"
    assert report["source_format"] == "mteb-retrieval-local"
    counts = _as_dict(report["counts"])
    deterministic_parameters = _as_dict(report["deterministic_parameters"])
    cache = _as_dict(report["cache"])
    assert counts["documents"] == 3
    assert counts["queries"] == 2
    assert counts["qrels"] == 3
    assert counts["cases"] == 2
    assert counts["positive_references"] == 2
    assert deterministic_parameters["top_k"] == 11
    assert cache["enabled"] is False

    cases = _read_jsonl(output / RAG_DATASET_NAME)
    first_case = cases[0]
    assert first_case["expected"] == ["materials/doc-alpha.md"]
    assert first_case["query"] == (
        "Retrieve a relevant passage.\nWhich source explains MTEB secondary gates?"
    )
    metadata = _as_dict(first_case["metadata"])
    assert metadata["adapter"] == "mteb"
    judgments = metadata["relevance_judgments"]
    assert judgments == [
        {
            "grade": 1,
            "metadata": {
                "line": 1,
                "relevant_docs_path": "test-00000-of-00001.jsonl",
            },
            "original_document_id": "doc-alpha",
            "positive": True,
            "source_id": "materials/doc-alpha.md",
        },
        {
            "grade": 0,
            "metadata": {
                "line": 2,
                "relevant_docs_path": "test-00000-of-00001.jsonl",
            },
            "original_document_id": "doc-beta",
            "positive": False,
            "source_id": "materials/doc-beta.md",
        },
    ]
    material_metadata = _read_jsonl(output / MATERIAL_METADATA_NAME)
    assert material_metadata[0]["original_document_id"] == "doc-alpha"
    assert material_metadata[0]["source_format"] == "mteb-retrieval-local"


def test_mteb_adapter_accepts_explicit_tsv_relevance_file(tmp_path: Path) -> None:
    source = _mteb_fixture(tmp_path)
    corpus = source / "corpus" / "corpus-00000-of-00001.jsonl"
    queries = source / "queries" / "test.jsonl"
    qrels = tmp_path / "qrels.tsv"
    qrels.write_text(
        "\n".join(
            [
                "query-id\tcorpus-id\tscore",
                "query-1\tdoc-alpha\t1",
                "query-2\tdoc-gamma\t1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "out"

    status = mteb_adapter.main(
        [
            "fixture",
            "--corpus-file",
            str(corpus),
            "--queries-file",
            str(queries),
            "--relevance-file",
            str(qrels),
            "--output",
            str(output),
        ]
    )

    assert status == 0
    assert (output / RAG_DATASET_NAME).is_file()
    cases = _read_jsonl(output / RAG_DATASET_NAME)
    assert [case["expected"] for case in cases] == [
        ["materials/doc-alpha.md"],
        ["materials/doc-gamma.md"],
    ]


def test_mteb_adapter_reports_missing_referenced_document(tmp_path: Path) -> None:
    source = _mteb_fixture(tmp_path)
    _write_jsonl(
        source / "data" / "test-00000-of-00001.jsonl",
        [{"query-id": "query-1", "corpus-id": "missing-doc", "score": 1}],
    )
    output = tmp_path / "out"
    report_path = tmp_path / "report.json"

    status = mteb_adapter.main(
        [
            "mteb/fixture",
            "--source-dir",
            str(source),
            "--output",
            str(output),
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    error = _as_dict(report["error"])
    assert status == 2
    assert report["status"] == "error"
    assert error["code"] == "missing_referenced_document"
    assert "missing-doc" in str(error["message"])
    assert not output.exists()
