from __future__ import annotations

from heph.release_state import (
    current_release_state,
    format_current_release_state,
    official_release,
)


def test_official_release_points_to_current_stable_version() -> None:
    release = official_release()

    assert release.package == "heph"
    assert release.command == "heph"
    assert release.channel == "stable"
    assert release.version == "0.0.59"
    assert release.tag == "v0.0.59"
    assert release.release_workflow == ".github/workflows/release.yml"


def test_current_release_state_exposes_runtime_and_official_stable() -> None:
    state = current_release_state()

    assert state["package_version"] == "0.0.59"
    official = state["official"]
    assert official["tag"] == "v0.0.59"
    runtime = state["runtime"]
    assert runtime["channel"] in {"source", "edge", "pypi"}
    assert runtime["python"]


def test_format_current_release_state_is_human_readable() -> None:
    text = format_current_release_state()

    assert "Heph release state" in text
    assert "official stable: v0.0.59 (0.0.59)" in text
    assert "release workflow: .github/workflows/release.yml" in text
