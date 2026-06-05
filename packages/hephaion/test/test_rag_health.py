from __future__ import annotations

from pathlib import Path

from rag.health import scan_extraction_health


def _write_material(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_scan_extraction_health_passes_clean_index(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    _write_material(armory / "materials" / "lecture.md", "# Lecture\n\nClean text.\n")

    report = scan_extraction_health(armory)

    assert report.passed
    assert report.documents == 1
    assert report.pass_rate == 1.0


def test_scan_extraction_health_reports_generic_noise(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    _write_material(armory / "materials" / "lecture.md", "# Lecture\n\nExtractionNoise.\n")

    report = scan_extraction_health(armory, forbidden_text=("ExtractionNoise",))

    assert not report.passed
    assert report.pass_rate == 0.0
    assert report.issues[0].source == "materials/lecture.md"
    assert report.issues[0].forbidden_text_present == ("ExtractionNoise",)
