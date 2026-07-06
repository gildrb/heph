from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.check_public_install import (
    DEFAULT_INDEX,
    DEFAULT_WORK_ROOT,
    _build_parser,
    _expected_runtime_version,
    _installed_heph_version,
    _pip_install_command,
    _public_index_env,
    _run_public,
    _uv_tool_install_command,
)


def test_public_install_uses_ignored_artifact_scratch_root_by_default() -> None:
    args = _build_parser().parse_args([])

    assert args.work_root == DEFAULT_WORK_ROOT
    assert args.index == DEFAULT_INDEX
    assert args.expect_runtime_channel == "pypi"


def test_public_install_builds_latest_uv_tool_command() -> None:
    command = _uv_tool_install_command("latest", "3.13", DEFAULT_INDEX)

    assert command == [
        "uv",
        "tool",
        "install",
        "--force",
        "--python",
        "3.13",
        "--default-index",
        "https://pypi.org/simple",
        "--refresh-package",
        "heph",
        "heph@latest",
    ]


def test_public_install_builds_versioned_uv_tool_command() -> None:
    command = _uv_tool_install_command("0.0.59", "3.13", DEFAULT_INDEX)

    assert command[-1] == "heph==0.0.59"


def test_public_install_builds_latest_pip_command() -> None:
    command = _pip_install_command(Path("/tmp/venv/bin/python"), "latest", DEFAULT_INDEX)

    assert command == [
        "/tmp/venv/bin/python",
        "-m",
        "pip",
        "install",
        "--no-cache-dir",
        "--index-url",
        "https://pypi.org/simple",
        "heph",
    ]


def test_public_install_clears_local_index_environment() -> None:
    env = _public_index_env(
        {
            "PATH": "/bin",
            "UV_FIND_LINKS": "/tmp/dist",
            "UV_INDEX_URL": "https://packages.example/simple",
            "PIP_FIND_LINKS": "/tmp/dist",
            "PIP_INDEX_URL": "https://packages.example/simple",
        },
        Path("/tmp/cache"),
    )

    assert env == {
        "PATH": "/bin",
        "UV_CACHE_DIR": "/tmp/cache",
    }


def test_public_install_derives_expected_runtime_version() -> None:
    assert _expected_runtime_version("0.0.59", None) == "v0.0.59"
    assert _expected_runtime_version("0.0.59", "release-1") == "release-1"


def test_public_install_parses_heph_version(monkeypatch, tmp_path) -> None:
    def fake_output(
        command: list[str],
        *,
        cwd: Path,
        env: object | None = None,
    ) -> str:
        assert command == ["/tmp/heph", "--version"]
        assert cwd == tmp_path
        assert env is None
        return "heph 0.0.59\n"

    monkeypatch.setattr("scripts.check_public_install._run_output", fake_output)

    assert _installed_heph_version(Path("/tmp/heph"), cwd=tmp_path) == "0.0.59"


def test_public_install_reports_failed_step(monkeypatch, tmp_path) -> None:
    def fake_run(command: list[str], *, cwd: Path, env: object | None = None) -> None:
        assert command == ["uv", "tool", "install"]
        assert cwd == tmp_path
        assert env is None
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr("scripts.check_public_install._run", fake_run)

    with pytest.raises(SystemExit, match="uv tool install from PyPI failed with exit code 1"):
        _run_public(
            ["uv", "tool", "install"],
            cwd=tmp_path,
            env=None,
            step="uv tool install from PyPI",
        )
