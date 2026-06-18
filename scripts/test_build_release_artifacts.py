from __future__ import annotations

from pathlib import Path

import pytest

from scripts.build_release_artifacts import (
    ReleaseBuildConfig,
    clean_dist,
    patched_release_config,
    release_build_config_from_env,
    release_build_input_errors,
    release_dependencies,
    render_release_config,
    stage_release_project,
)


def test_release_build_config_from_env_uses_release_backend_values() -> None:
    config = release_build_config_from_env(
        {
            "HEPHAION_POSTHOG_HOST": " https://posthog.example ",
            "HEPHAION_POSTHOG_PROJECT_TOKEN": " phc_release ",
            "HEPHAION_SENTRY_DSN": " https://sentry.example/1 ",
        },
        channel="pypi",
        release_version="v0.0.49",
    )

    assert config == ReleaseBuildConfig(
        channel="pypi",
        version="v0.0.49",
        posthog_host=" https://posthog.example ",
        posthog_project_token=" phc_release ",
        sentry_dsn=" https://sentry.example/1 ",
    )
    rendered = render_release_config(config)
    assert 'POSTHOG_HOST: str | None = "https://posthog.example"' in rendered
    assert 'POSTHOG_PROJECT_TOKEN: str | None = "phc_release"' in rendered
    assert 'SENTRY_DSN: str | None = "https://sentry.example/1"' in rendered
    assert 'RELEASE_CHANNEL: str | None = "pypi"' in rendered
    assert 'RELEASE_VERSION: str | None = "v0.0.49"' in rendered


def test_release_build_config_renders_empty_values_as_safe_stub() -> None:
    rendered = render_release_config(
        ReleaseBuildConfig(
            channel="pypi",
            version="v0.0.49",
            posthog_host="",
            posthog_project_token=None,
            sentry_dsn="   ",
        )
    )

    assert "POSTHOG_HOST: str | None = None" in rendered
    assert "POSTHOG_PROJECT_TOKEN: str | None = None" in rendered
    assert "SENTRY_DSN: str | None = None" in rendered


def test_patched_release_config_restores_original_after_error(tmp_path) -> None:
    path = tmp_path / "release.py"
    path.write_text("original\n", encoding="utf-8")
    config = ReleaseBuildConfig(
        channel="pypi",
        version="v0.0.49",
        posthog_host=None,
        posthog_project_token=None,
        sentry_dsn=None,
    )

    with pytest.raises(RuntimeError, match="boom"):
        _raise_after_checking_patched_release_config(path, config)

    assert path.read_text(encoding="utf-8") == "original\n"


def test_clean_dist_removes_release_artifacts_only(tmp_path) -> None:
    (tmp_path / "heph-0.0.49-py3-none-any.whl").write_text("", encoding="utf-8")
    (tmp_path / "heph-0.0.49.tar.gz").write_text("", encoding="utf-8")
    (tmp_path / "keep.txt").write_text("", encoding="utf-8")

    clean_dist(tmp_path)

    assert sorted(path.name for path in tmp_path.iterdir()) == ["keep.txt"]


def test_release_dependencies_collapse_internal_workspace_packages() -> None:
    dependencies = release_dependencies()

    assert "certifi==2026.2.25" in dependencies
    assert "docling==2.94.0" in dependencies
    assert "rich==14.3.3" in dependencies
    assert dependencies.count("unicodeit==0.7.5") == 1
    assert all(not dependency.startswith("heph-") for dependency in dependencies)
    assert "hephaion==0.0.49" not in dependencies


def test_stage_release_project_builds_single_public_package(tmp_path) -> None:
    project_dir = stage_release_project(tmp_path)
    pyproject = (project_dir / "pyproject.toml").read_text(encoding="utf-8")

    assert (project_dir / "src" / "heph" / "__init__.py").is_file()
    assert (project_dir / "src" / "ai" / "__init__.py").is_file()
    assert (project_dir / "src" / "extensions" / "__init__.py").is_file()
    assert (project_dir / "src" / "hephaion" / "__init__.py").is_file()
    assert (project_dir / "src" / "interfaces" / "__init__.py").is_file()
    assert (project_dir / "src" / "heph" / "state" / "release.toml").is_file()
    assert (project_dir / "src" / "hephaion" / "parameters" / "default.toml").is_file()
    assert 'name = "heph"' in pyproject
    assert 'build-backend = "setuptools.build_meta"' in pyproject
    assert "heph-ai" not in pyproject
    assert "heph-interfaces" not in pyproject
    assert "hephaion==0.0.49" not in pyproject


def test_release_build_inputs_match_stable_tag() -> None:
    assert release_build_input_errors("v0.0.49") == []


def _raise_after_checking_patched_release_config(
    path: Path,
    config: ReleaseBuildConfig,
) -> None:
    with patched_release_config(path, config):
        assert 'RELEASE_CHANNEL: str | None = "pypi"' in path.read_text(encoding="utf-8")
        raise RuntimeError("boom")
