from __future__ import annotations

import hashlib
import json
import socket
from pathlib import Path

import pytest

from hephaistos.armory.storage import initialize
from scripts import (
    benchmark_material_roles,
    benchmark_rag,
    generate_public_academic_benchmark_cases,
)


def test_public_academic_case_generation_is_deterministic_and_grounded(
    tmp_path: Path,
) -> None:
    manifest, armory = _write_public_academic_fixture(tmp_path)
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"

    first_report = generate_public_academic_benchmark_cases.generate_cases(
        manifest,
        armory,
        first_output,
        minimums=_fixture_minimums(),
    )
    second_report = generate_public_academic_benchmark_cases.generate_cases(
        manifest,
        armory,
        second_output,
        minimums=_fixture_minimums(),
    )

    assert first_report.status == "passed"
    assert first_report.benchmark_ready is True
    assert first_report.case_counts_by_type == {
        "document_understanding": 4,
        "material_role": 4,
        "retrieval": 4,
    }
    assert first_report.breadth["domains"] == 3
    assert first_report.breadth["material_roles"] == 4
    assert first_report.breadth["source_organizations"] == 3
    assert first_report.near_miss_retrieval_cases == 4
    assert first_report.deterministic_serialization_status == "passed"
    assert second_report.deterministic_serialization_status == "passed"
    for name in ("rag.jsonl", "material_roles.jsonl", "document_understanding.jsonl"):
        assert (first_output / name).read_bytes() == (second_output / name).read_bytes()

    rag_cases = benchmark_rag.load_cases(first_output / "rag.jsonl")
    assert len(rag_cases) == 4
    assert all(case.expected[0].startswith("materials/public-academic/") for case in rag_cases)
    assert all(case.forbidden_before_expected for case in rag_cases)
    assert {case.domain for case in rag_cases} == {
        "artificial-intelligence",
        "computer-vision",
        "software-engineering",
    }

    role_cases = benchmark_material_roles.load_cases(first_output / "material_roles.jsonl")
    assert [case.expected_role for case in role_cases] == [
        "reference",
        "lecture",
        "textbook",
        "lecture",
    ]
    raw_role_cases = _jsonl(first_output / "material_roles.jsonl")
    assert {case["expected_material_role"] for case in raw_role_cases} == {
        "course-notes",
        "lecture-notes",
        "reference",
        "textbook",
    }

    understanding_cases = _jsonl(first_output / "document_understanding.jsonl")
    assert all(case["expected_evidence"] == [case["source"]] for case in understanding_cases)
    assert all(
        case["expected_citation_targets"] == [case["source"]] for case in understanding_cases
    )
    assert {
        criterion
        for case in understanding_cases
        for criterion in _string_list(case["expected_answer_criteria"])
    } >= {
        "domain: artificial-intelligence",
        "source organization: MIT CSAIL Missing Semester",
    }


def test_public_academic_case_generation_does_not_use_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, armory = _write_public_academic_fixture(tmp_path)

    def fail_network(*_args: object, **_kwargs: object) -> socket.socket:
        raise AssertionError("case generation must not open network sockets")

    monkeypatch.setattr(socket, "create_connection", fail_network)

    report = generate_public_academic_benchmark_cases.generate_cases(
        manifest,
        armory,
        tmp_path / "cases",
        minimums=_fixture_minimums(),
    )

    assert report.status == "passed"


def test_public_academic_case_generation_rejects_missing_provenance(
    tmp_path: Path,
) -> None:
    manifest, armory = _write_public_academic_fixture(tmp_path)
    (armory / ".hephaistos" / "public_corpus_provenance.json").unlink()

    with pytest.raises(ValueError, match="public corpus provenance metadata is missing"):
        generate_public_academic_benchmark_cases.generate_cases(
            manifest,
            armory,
            tmp_path / "cases",
            minimums=_fixture_minimums(),
        )


def test_public_academic_case_generation_rejects_hash_mismatch(
    tmp_path: Path,
) -> None:
    manifest, armory = _write_public_academic_fixture(tmp_path)
    material = armory / "materials" / "public-academic" / "ucb" / "summary.html"
    original = material.read_text(encoding="utf-8")
    material.write_text("X" + original[1:], encoding="utf-8")

    with pytest.raises(ValueError, match="sha256 mismatch"):
        generate_public_academic_benchmark_cases.generate_cases(
            manifest,
            armory,
            tmp_path / "cases",
            minimums=_fixture_minimums(),
        )


def test_public_academic_case_generation_refuses_to_overwrite_outputs(
    tmp_path: Path,
) -> None:
    manifest, armory = _write_public_academic_fixture(tmp_path)
    output = tmp_path / "cases"
    generate_public_academic_benchmark_cases.generate_cases(
        manifest,
        armory,
        output,
        minimums=_fixture_minimums(),
    )

    with pytest.raises(FileExistsError, match="pass --overwrite"):
        generate_public_academic_benchmark_cases.generate_cases(
            manifest,
            armory,
            output,
            minimums=_fixture_minimums(),
        )


def test_public_academic_case_generation_cli_writes_readiness_report(
    tmp_path: Path,
) -> None:
    manifest, armory = _write_public_academic_fixture(tmp_path)
    report_path = tmp_path / "readiness.json"

    status = generate_public_academic_benchmark_cases.main(
        [
            str(manifest),
            str(armory),
            "--output-dir",
            str(tmp_path / "cases"),
            "--json-report",
            str(report_path),
            "--min-retrieval-cases",
            "4",
            "--min-material-role-cases",
            "4",
            "--min-document-understanding-cases",
            "4",
            "--min-domains",
            "3",
            "--min-material-roles",
            "4",
            "--min-source-organizations",
            "3",
        ]
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 0
    assert payload["status"] == "passed"
    assert payload["case_counts_by_type"]["retrieval"] == 4
    assert payload["generated_files"]["readiness_report"].endswith("readiness_report.json")


def _fixture_minimums() -> generate_public_academic_benchmark_cases.CaseGenerationMinimums:
    return generate_public_academic_benchmark_cases.CaseGenerationMinimums(
        retrieval_cases=4,
        material_role_cases=4,
        document_understanding_cases=4,
        domains=3,
        material_roles=4,
        source_organizations=3,
    )


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _write_public_academic_fixture(tmp_path: Path) -> tuple[Path, Path]:
    documents = [
        _fixture_document(
            document_id="ucb-summary",
            title="Search Summary",
            source="materials/public-academic/ucb/summary.html",
            body="Search Summary reference material from UC Berkeley CS188.",
            source_organization="UC Berkeley EECS CS188",
            domain="artificial-intelligence",
            role="reference",
            document_type="html-chapter-summary",
        ),
        _fixture_document(
            document_id="stanford-course-notes",
            title="Linear Classification Notes",
            source="materials/public-academic/stanford/linear.html",
            body="Linear Classification course notes from Stanford CS231n.",
            source_organization="Stanford CS231n",
            domain="computer-vision",
            role="lecture-notes",
            document_type="html-course-notes",
        ),
        _fixture_document(
            document_id="ucb-textbook",
            title="State Spaces and Search Problems",
            source="materials/public-academic/ucb/state.html",
            body="State Spaces and Search Problems textbook material from UC Berkeley CS188.",
            source_organization="UC Berkeley EECS CS188",
            domain="artificial-intelligence",
            role="textbook",
            document_type="html-search-textbook-section",
        ),
        _fixture_document(
            document_id="mit-lecture",
            title="Shell Tools and Scripting",
            source="materials/public-academic/mit/shell-tools.html",
            body="Shell Tools and Scripting lecture notes from MIT Missing Semester.",
            source_organization="MIT CSAIL Missing Semester",
            domain="software-engineering",
            role="lecture-notes",
            document_type="html-lecture-notes",
        ),
    ]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "id": "public-academic-fixture",
                "description": "Fixture public academic manifest.",
                "corpus_kind": "public-academic",
                "documents": documents,
                "datasets": [],
                "known_limits": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    armory = tmp_path / "armory"
    initialize(armory)
    provenance_documents: list[dict[str, object]] = []
    for document in documents:
        source = str(document["source"])
        output_path = armory / source
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(str(document["_body"]), encoding="utf-8")
        provenance_documents.append(
            {
                "id": document["id"],
                "title": document["title"],
                "source": source,
                "source_url": document["source_url"],
                "output_path": str(output_path),
                "bytes": document["bytes"],
                "sha256": document["sha256"],
                "expected_bytes": document["bytes"],
                "expected_sha256": document["sha256"],
                "source_organization": document["source_organization"],
                "license": document["license"],
                "license_url": document["license_url"],
                "attribution": document["attribution"],
                "domain": document["domain"],
                "role": document["role"],
                "document_type": document["document_type"],
                "stressors": document["stressors"],
            }
        )
        del document["_body"]
    (armory / ".hephaistos" / "public_corpus_provenance.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "benchmark_ready": True,
                "manifest_path": str(manifest),
                "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
                "armory_path": str(armory),
                "corpus_kind": "public-academic",
                "document_count": len(provenance_documents),
                "documents": provenance_documents,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest, armory


def _fixture_document(
    *,
    document_id: str,
    title: str,
    source: str,
    body: str,
    source_organization: str,
    domain: str,
    role: str,
    document_type: str,
) -> dict[str, object]:
    encoded = body.encode("utf-8")
    return {
        "id": document_id,
        "title": title,
        "source": source,
        "source_url": f"https://example.edu/{document_id}.html",
        "bytes": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "source_organization": source_organization,
        "license": "Public academic fixture attribution.",
        "license_url": "https://example.edu/license",
        "attribution": f"{source_organization} public fixture.",
        "domain": domain,
        "role": role,
        "document_type": document_type,
        "stressors": ["public-html", domain],
        "_body": body,
    }
