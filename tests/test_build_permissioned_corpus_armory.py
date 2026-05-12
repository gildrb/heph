from __future__ import annotations

import json
from pathlib import Path

from scripts import build_permissioned_corpus_armory


def test_build_corpus_copies_supported_documents_and_writes_provenance(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    pdf = source_dir / "Lecture 1.PDF"
    pdf.write_text("slides", encoding="utf-8")
    ignored = source_dir / "image.png"
    ignored.write_text("image", encoding="utf-8")
    armory = tmp_path / "armory"
    manifest = tmp_path / "suite" / "manifest.json"

    report = build_permissioned_corpus_armory.build_corpus(
        (source_dir,),
        armory,
        manifest,
        domain="mathematics",
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    documents = payload["documents"]
    assert report.status == 0
    assert report.copied_documents == 1
    assert report.skipped_documents == 1
    assert (armory / "materials" / "source-Lecture 1.pdf").is_file()
    assert documents[0]["source"] == "materials/source-Lecture 1.pdf"
    assert documents[0]["domain"] == "mathematics"
    assert documents[0]["source_url"] == pdf.resolve().as_uri()
    assert "permissioned" in documents[0]["permission_note"]
    assert (manifest.parent / "rag.jsonl").is_file()
    assert (manifest.parent / "chat_event_expectation.json").read_text(encoding="utf-8") == "[]\n"


def test_build_corpus_refuses_overwrite_without_flag(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "notes.md").write_text("notes", encoding="utf-8")
    armory = tmp_path / "armory"
    manifest = tmp_path / "manifest.json"

    first = build_permissioned_corpus_armory.build_corpus((source_dir,), armory, manifest)
    second = build_permissioned_corpus_armory.build_corpus((source_dir,), armory, manifest)

    assert first.status == 0
    assert second.status == 2
    assert "destination already exists" in second.failures[0]


def test_build_corpus_limit_selects_prefix(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "a.md").write_text("a", encoding="utf-8")
    (source_dir / "b.md").write_text("b", encoding="utf-8")

    report = build_permissioned_corpus_armory.build_corpus(
        (source_dir,),
        tmp_path / "armory",
        tmp_path / "manifest.json",
        limit=1,
    )

    assert report.status == 0
    assert report.copied_documents == 1


def test_build_corpus_can_balance_limited_selection_by_parent_domain(tmp_path: Path) -> None:
    math_dir = tmp_path / "Mathematics"
    ai_dir = tmp_path / "Artificial Intelligence"
    math_dir.mkdir()
    ai_dir.mkdir()
    for index in range(4):
        (math_dir / f"math-{index}.pdf").write_text("math", encoding="utf-8")
    for index in range(2):
        (ai_dir / f"ai-{index}.pdf").write_text("ai", encoding="utf-8")
    manifest = tmp_path / "suite" / "manifest.json"

    report = build_permissioned_corpus_armory.build_corpus(
        (math_dir, ai_dir),
        tmp_path / "armory",
        manifest,
        limit=3,
        domain_from_parent=True,
        balance_domains=True,
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    domains = [document["domain"] for document in payload["documents"]]
    assert report.status == 0
    assert report.copied_documents == 3
    assert set(domains) == {"Artificial Intelligence", "Mathematics"}


def test_build_corpus_can_infer_roles_from_copied_content(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "generic.md").write_text(
        "Question 1. Exercise 2. Problem 3. Due date Friday.",
        encoding="utf-8",
    )
    manifest = tmp_path / "suite" / "manifest.json"

    report = build_permissioned_corpus_armory.build_corpus(
        (source_dir,),
        tmp_path / "armory",
        manifest,
        infer_roles_from_index=True,
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert report.status == 0
    assert payload["documents"][0]["role"] == "assignment"
    assert payload["documents"][0]["document_type"] == "exercise-sheet"


def test_build_corpus_can_use_parent_folder_as_domain(tmp_path: Path) -> None:
    math_dir = tmp_path / "Mathematics"
    ai_dir = tmp_path / "Artificial Intelligence"
    math_dir.mkdir()
    ai_dir.mkdir()
    (math_dir / "lecture.pdf").write_text("math lecture", encoding="utf-8")
    (ai_dir / "exam.pdf").write_text("ai exam", encoding="utf-8")
    manifest = tmp_path / "suite" / "manifest.json"

    report = build_permissioned_corpus_armory.build_corpus(
        (math_dir, ai_dir),
        tmp_path / "armory",
        manifest,
        domain_from_parent=True,
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    domains = {document["domain"] for document in payload["documents"]}
    assert report.status == 0
    assert domains == {"Artificial Intelligence", "Mathematics"}


def test_build_corpus_reviewed_omits_scaffold_known_limits(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "lecture.pdf").write_text("lecture", encoding="utf-8")
    manifest = tmp_path / "suite" / "manifest.json"

    report = build_permissioned_corpus_armory.build_corpus(
        (source_dir,),
        tmp_path / "armory",
        manifest,
        reviewed=True,
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert report.status == 0
    assert payload["known_limits"] == []


def test_build_corpus_cli_writes_json_report(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "notes.md").write_text("notes", encoding="utf-8")
    json_report = tmp_path / "report.json"

    status = build_permissioned_corpus_armory.main(
        [
            str(tmp_path / "armory"),
            str(tmp_path / "manifest.json"),
            str(source_dir),
            "--json-report",
            str(json_report),
        ]
    )

    payload = json.loads(json_report.read_text(encoding="utf-8"))
    assert status == 0
    assert payload["copied_documents"] == 1


def test_build_corpus_cli_can_infer_roles_from_index(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "generic.md").write_text(
        "Question 1. Exercise 2. Problem 3. Due date Friday.",
        encoding="utf-8",
    )
    manifest = tmp_path / "manifest.json"

    status = build_permissioned_corpus_armory.main(
        [
            str(tmp_path / "armory"),
            str(manifest),
            str(source_dir),
            "--infer-roles-from-index",
        ]
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert status == 0
    assert payload["documents"][0]["role"] == "assignment"


def test_build_corpus_cli_can_use_parent_folder_as_domain(tmp_path: Path) -> None:
    math_dir = tmp_path / "Mathematics"
    ai_dir = tmp_path / "Artificial Intelligence"
    math_dir.mkdir()
    ai_dir.mkdir()
    (math_dir / "lecture.pdf").write_text("math lecture", encoding="utf-8")
    (ai_dir / "exam.pdf").write_text("ai exam", encoding="utf-8")
    manifest = tmp_path / "manifest.json"

    status = build_permissioned_corpus_armory.main(
        [
            str(tmp_path / "armory"),
            str(manifest),
            str(math_dir),
            str(ai_dir),
            "--domain-from-parent",
        ]
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    domains = {document["domain"] for document in payload["documents"]}
    assert status == 0
    assert domains == {"Artificial Intelligence", "Mathematics"}


def test_build_corpus_cli_reviewed_omits_scaffold_known_limits(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "lecture.pdf").write_text("lecture", encoding="utf-8")
    manifest = tmp_path / "manifest.json"

    status = build_permissioned_corpus_armory.main(
        [
            str(tmp_path / "armory"),
            str(manifest),
            str(source_dir),
            "--reviewed",
        ]
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert status == 0
    assert payload["known_limits"] == []


def test_build_corpus_cli_can_balance_limited_selection_by_parent_domain(
    tmp_path: Path,
) -> None:
    math_dir = tmp_path / "Mathematics"
    ai_dir = tmp_path / "Artificial Intelligence"
    math_dir.mkdir()
    ai_dir.mkdir()
    for index in range(4):
        (math_dir / f"math-{index}.pdf").write_text("math", encoding="utf-8")
    for index in range(2):
        (ai_dir / f"ai-{index}.pdf").write_text("ai", encoding="utf-8")
    manifest = tmp_path / "manifest.json"

    status = build_permissioned_corpus_armory.main(
        [
            str(tmp_path / "armory"),
            str(manifest),
            str(math_dir),
            str(ai_dir),
            "--limit",
            "3",
            "--domain-from-parent",
            "--balance-domains",
        ]
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    domains = [document["domain"] for document in payload["documents"]]
    assert status == 0
    assert set(domains) == {"Artificial Intelligence", "Mathematics"}
