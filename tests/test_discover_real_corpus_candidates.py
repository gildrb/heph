from __future__ import annotations

import json
from pathlib import Path

from hephaion.armory.storage import initialize
from scripts import discover_real_corpus_candidates


def _make_armory(root: Path, name: str, files: tuple[str, ...]) -> Path:
    armory = root / name
    initialize(armory)
    for rel_path in files:
        material = armory / "materials" / rel_path
        material.parent.mkdir(parents=True, exist_ok=True)
        material.write_text(
            "Question 1. Explain the lecture content. [5 marks]\n",
            encoding="utf-8",
        )
    return armory


def test_discovery_sorts_candidates_and_reports_counts(tmp_path: Path) -> None:
    small = _make_armory(tmp_path, "small", ("one.md",))
    large = _make_armory(
        tmp_path,
        "large",
        ("slides/Folien.pdf", "exam/past-exam.md", "notes/reference.txt"),
    )
    (tmp_path / "not-an-armory").mkdir()

    report = discover_real_corpus_candidates.discover_candidates(
        tmp_path,
        min_documents=2,
    )

    assert report.status == 0
    assert report.min_roles == 3
    assert report.passing_candidates == (str(large),)
    assert [candidate.armory_path for candidate in report.candidates] == [
        str(large),
        str(small),
    ]
    assert report.candidates[0].visible_materials == 3
    assert report.candidates[0].roles["past_exam"] == 1
    assert report.candidates[0].roles["slides"] == 1
    assert report.candidates[0].extensions[".pdf"] == 1
    assert report.candidates[1].failures == (
        "visible material count 1 below required 2",
        "material role variety 1 below required 3",
    )
    assert report.next_steps[0] == (
        "uv run python -m scripts.prepare_real_corpus_evidence "
        f"{large} .artifacts/real-corpus-evidence"
    )
    assert "run_model_eval_matrix" in report.next_steps[1]


def test_discovery_require_candidate_fails_when_no_armory_is_broad_enough(
    tmp_path: Path,
) -> None:
    _make_armory(tmp_path, "small", ("one.md",))

    report = discover_real_corpus_candidates.discover_candidates(
        tmp_path,
        min_documents=40,
        require_candidate=True,
    )

    assert report.status == 1
    assert report.passing_candidates == ()
    assert report.failures == (
        "no armory meets real-corpus candidate thresholds (min_documents=40, min_roles=3)",
    )
    assert report.next_steps == ()


def test_discovery_rejects_large_but_role_narrow_candidate(tmp_path: Path) -> None:
    _make_armory(tmp_path, "large-notes", tuple(f"notes/{idx}.md" for idx in range(40)))

    report = discover_real_corpus_candidates.discover_candidates(
        tmp_path,
        min_documents=40,
        min_roles=3,
        require_candidate=True,
    )

    assert report.status == 1
    assert report.passing_candidates == ()
    assert "material role variety 1 below required 3" in report.candidates[0].failures


def test_discovery_cli_writes_json_report(tmp_path: Path) -> None:
    _make_armory(tmp_path, "course", ("slides.pdf", "exam.md"))
    json_report = tmp_path / "discovery.json"

    status = discover_real_corpus_candidates.main(
        [
            str(tmp_path),
            "--min-documents",
            "2",
            "--min-roles",
            "2",
            "--json-report",
            str(json_report),
        ]
    )

    payload = json.loads(json_report.read_text(encoding="utf-8"))
    assert status == 0
    assert payload["status"] == 0
    assert payload["min_roles"] == 2
    assert payload["passing_candidates"]
    assert payload["next_steps"]
