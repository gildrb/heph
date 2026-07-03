from __future__ import annotations

from scripts.check_release_state import release_state_errors


def test_release_state_accepts_current_manifest_and_metadata() -> None:
    assert (
        release_state_errors(
            current_version_must_match_stable=True,
            require_tag=False,
            tag=None,
            commit=None,
        )
        == []
    )


def test_release_state_can_require_an_explicit_release_tag() -> None:
    errors = release_state_errors(
        current_version_must_match_stable=False,
        require_tag=True,
        tag="v9.9.9",
        commit=None,
    )

    assert "release tag 'v9.9.9' does not match manifest tag 'v0.0.58'" in errors
    assert "stable release tag does not exist: v9.9.9" in errors
