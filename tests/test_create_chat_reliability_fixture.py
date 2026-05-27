from __future__ import annotations

from pathlib import Path

import pytest

from hephaion.armory import storage
from scripts import create_chat_reliability_fixture as fixture


def test_create_fixture_armory_writes_generic_materials(tmp_path: Path) -> None:
    armory = tmp_path / "armory"

    files = fixture.create_fixture_armory(armory)
    material_text = "\n".join(path.read_text(encoding="utf-8") for path in files)

    assert (armory / storage.MARKER_FILE).is_file()
    assert len(files) == len(fixture.FIXTURE_MATERIALS) + 1
    assert "Selection sort repeatedly chooses the smallest remaining item" in material_text
    assert "The product rule says" in material_text
    assert "Retrieval practice asks" in material_text
    assert "mark unsupported claims as not found" in material_text


def test_create_fixture_armory_refuses_accidental_overwrite(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    fixture.create_fixture_armory(armory)

    with pytest.raises(FileExistsError, match="fixture materials already exist"):
        fixture.create_fixture_armory(armory)

    overwritten = fixture.create_fixture_armory(armory, variant="rerun", force=True)

    assert overwritten[0].read_text(encoding="utf-8").endswith("the corpus generic and public.\n")


def test_create_fixture_armories_writes_distinct_seeded_armories(tmp_path: Path) -> None:
    report = fixture.create_fixture_armories(
        tmp_path / "seeded",
        count=3,
        seed_prefix="gauntlet-seed",
    )

    armories = [Path(item["armory"]) for item in report["armories"]]
    manifests = [
        (
            armory / storage.MATERIALS_DIR / fixture.FIXTURE_MATERIALS_DIR / "fixture-manifest.md"
        ).read_text(encoding="utf-8")
        for armory in armories
    ]

    assert report["count"] == 3
    assert len(set(armories)) == 3
    assert all((armory / storage.MARKER_FILE).is_file() for armory in armories)
    assert "Variant: gauntlet-seed-01" in manifests[0]
    assert "Variant: gauntlet-seed-02" in manifests[1]
    assert "Variant: gauntlet-seed-03" in manifests[2]


def test_create_fixture_armories_rejects_nonpositive_count(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="count must be positive"):
        fixture.create_fixture_armories(tmp_path / "empty", count=0)
