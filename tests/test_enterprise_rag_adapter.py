from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from scripts.external_benchmarks import enterprise_rag_adapter
from scripts.external_benchmarks.conversion import MATERIAL_METADATA_NAME, RAG_DATASET_NAME


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def _as_dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast("dict[str, object]", value)


def _enterprise_rag_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "EnterpriseRAG-Bench"
    sources = root / "generated_data" / "sources" / "github"
    sources.mkdir(parents=True)
    (sources / "alpha.json").write_text(
        json.dumps(
            {
                "dataset_doc_uuid": "dsid_alpha",
                "title_field_name": "title",
                "content_field_names": ["body"],
                "title": "Multipart Upload Defaults",
                "body": "The API allows 10 MiB per file and 50 MiB total per request.",
                "metadata": {"repository": "openai-compatible-api"},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (sources / "beta.json").write_text(
        json.dumps(
            {
                "dataset_doc_uuid": "dsid_beta",
                "title_field_name": "name",
                "content_field_names": ["summary", "details"],
                "name": "",
                "summary": "This is a distractor summary.",
                "details": ["stream timebox notes", "not upload limits"],
                "metadata": ["official docs sometimes use non-object metadata"],
                "source": "github",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (sources / "empty.json").write_text(
        json.dumps(
            {
                "dataset_doc_uuid": "dsid_empty",
                "title_field_name": "channel",
                "content_field_names": ["messages"],
                "channel": "general",
                "messages": "",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (sources / "beta-duplicate.json").write_text(
        json.dumps(
            {
                "dataset_doc_uuid": "dsid_beta",
                "title_field_name": "title",
                "content_field_names": ["body"],
                "title": "Duplicate Official UUID",
                "body": "A second official document shares the same dsid.",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    questions = [
        {
            "question_id": "qst_0001",
            "question_type": "basic",
            "source_types": ["github"],
            "question": "What are the multipart upload defaults?",
            "expected_doc_ids": ["dsid_alpha"],
            "gold_answer": "10 MiB per file and 50 MiB total per request.",
            "answer_facts": ["10 MiB per file", "50 MiB total"],
        },
        {
            "question_id": "qst_0002",
            "question": "Which stream metric document is duplicated?",
            "expected_doc_ids": ["dsid_beta", "dsid_beta"],
        },
        {
            "question_id": "qst_0003",
            "question": "This unlabeled generated question should be skipped.",
            "expected_doc_ids": [],
        },
    ]
    (root / "questions.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in questions),
        encoding="utf-8",
    )
    return root


def test_enterprise_rag_adapter_preserves_official_ids_and_content_schema(
    tmp_path: Path,
) -> None:
    source = _enterprise_rag_fixture(tmp_path)
    output = tmp_path / "out"
    report_path = tmp_path / "report.json"

    status = enterprise_rag_adapter.main(
        [
            str(source),
            "--output",
            str(output),
            "--top-k",
            "10",
            "--json-report",
            str(report_path),
        ]
    )

    assert status == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "success"
    assert report["adapter"] == "enterprise-rag"
    assert report["dataset"] == "enterprise-rag-bench"
    assert report["source_format"] == "enterprise-rag-json-sources"
    assert report["counts"]["documents"] == 4
    assert report["counts"]["queries"] == 2
    assert report["counts"]["qrels"] == 3
    assert report["counts"]["cases"] == 2
    assert report["warnings"] == [
        "1 duplicate dataset_doc_uuid document(s) preserved with stable internal ids",
        "1 question(s) without expected_doc_ids skipped",
    ]

    cases = _read_jsonl(output / RAG_DATASET_NAME)
    assert cases[0]["id"] == "enterprise-rag-enterprise-rag-bench-test-qst_0001"
    assert cases[0]["expected"] == ["materials/github/alpha.md"]
    assert cases[1]["expected"] == [
        "materials/github/beta-duplicate.md",
        "materials/github/beta.md",
    ]
    case_metadata = _as_dict(cases[0]["metadata"])
    assert case_metadata["original_query_id"] == "qst_0001"
    assert case_metadata["answers"] == ["10 MiB per file and 50 MiB total per request."]

    material_text = (output / "armory" / "materials" / "github" / "alpha.md").read_text(
        encoding="utf-8"
    )
    assert "# Multipart Upload Defaults" in material_text
    assert "10 MiB per file and 50 MiB total" in material_text

    material_metadata = _read_jsonl(output / MATERIAL_METADATA_NAME)
    material_by_source = {str(row["source_id"]): row for row in material_metadata}
    alpha = material_by_source["materials/github/alpha.md"]
    alpha_metadata = _as_dict(alpha["metadata"])
    assert alpha["original_document_id"] == "dsid_alpha"
    assert alpha_metadata["repository"] == "openai-compatible-api"
    assert alpha_metadata["enterprise_rag_source_path"] == "github/alpha.json"
    assert alpha_metadata["source_type"] == "github"
    assert "title" not in alpha_metadata
    assert "body" not in alpha_metadata
    beta_duplicate = material_by_source["materials/github/beta.md"]
    beta_duplicate_metadata = _as_dict(beta_duplicate["metadata"])
    assert beta_duplicate["original_document_id"] == "dsid_beta__enterprise_duplicate_2"
    assert beta_duplicate_metadata["enterprise_rag_document_id"] == "dsid_beta"
    assert beta_duplicate_metadata["enterprise_rag_duplicate_document"] is True
    assert beta_duplicate_metadata["metadata"] == [
        "official docs sometimes use non-object metadata"
    ]
    assert "summary" not in beta_duplicate_metadata
    assert "details" not in beta_duplicate_metadata
    empty_metadata = _as_dict(material_by_source["materials/github/empty.md"]["metadata"])
    assert empty_metadata["enterprise_rag_empty_content"] is True
    assert (output / "armory" / "materials" / "github" / "empty.md").read_text(
        encoding="utf-8"
    ) == "# general\n\n[Empty EnterpriseRAG content]\n"
