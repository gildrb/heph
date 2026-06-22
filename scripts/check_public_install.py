"""Verify public PyPI installs for the user-facing Heph command."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from scripts.release_stress_test import (
    _isolated_uv_tool_env,
    _run,
    _run_output,
    _stress_heph_executable,
    _stress_installed_sdk,
    _tool_executable,
    _validate_sdk_capability_payload,
    _venv_executable,
    _venv_python,
)

DEFAULT_INDEX = "https://pypi.org/simple"
DEFAULT_WORK_ROOT = Path(".artifacts") / "public-install"
PUBLIC_INDEX_ENV_KEYS = (
    "PIP_EXTRA_INDEX_URL",
    "PIP_FIND_LINKS",
    "PIP_INDEX_URL",
    "PIP_NO_INDEX",
    "UV_DEFAULT_INDEX",
    "UV_EXTRA_INDEX_URL",
    "UV_FIND_LINKS",
    "UV_INDEX",
    "UV_INDEX_URL",
    "UV_NO_INDEX",
)


def main() -> int:
    args = _build_parser().parse_args()
    scratch_root = args.work_root
    scratch_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="run-", dir=scratch_root) as temp_dir:
        work_dir = Path(temp_dir)
        uv_heph = _install_public_uv_tool(
            version=args.version,
            python=args.python,
            index=args.index,
            work_dir=work_dir,
        )
        expected_version = _installed_heph_version(uv_heph.path, cwd=work_dir, env=uv_heph.env)
        expected_runtime_version = _expected_runtime_version(
            expected_version,
            args.expect_runtime_version,
        )
        _stress_heph_executable(
            uv_heph.path,
            expected_version=expected_version,
            expected_runtime_channel=args.expect_runtime_channel,
            expected_runtime_version=expected_runtime_version,
            cwd=work_dir,
            env=uv_heph.env,
        )
        _stress_sdk_command(uv_heph.path, cwd=work_dir, env=uv_heph.env)

        pip_heph = _install_public_pip(
            version=args.version,
            index=args.index,
            python=args.python,
            work_dir=work_dir,
        )
        _stress_heph_executable(
            pip_heph.path,
            expected_version=expected_version,
            expected_runtime_channel=args.expect_runtime_channel,
            expected_runtime_version=expected_runtime_version,
            cwd=work_dir,
        )
        _stress_installed_sdk(pip_heph.python, pip_heph.path, cwd=work_dir)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", default="3.13")
    parser.add_argument("--version", default="latest")
    parser.add_argument("--work-root", type=Path, default=DEFAULT_WORK_ROOT)
    parser.add_argument("--index", default=DEFAULT_INDEX)
    parser.add_argument("--expect-runtime-channel", default="pypi")
    parser.add_argument("--expect-runtime-version")
    return parser


@dataclass(frozen=True)
class InstalledTool:
    path: Path
    env: Mapping[str, str]


@dataclass(frozen=True)
class InstalledPipCommand:
    path: Path
    python: Path


def _install_public_uv_tool(
    *,
    version: str,
    python: str,
    index: str,
    work_dir: Path,
) -> InstalledTool:
    tool_dir = work_dir / "uv-tools"
    tool_bin = work_dir / "uv-tool-bin"
    tool_bin.mkdir()
    env = _public_index_env(_isolated_uv_tool_env(tool_dir, tool_bin), work_dir / "uv-cache")
    _run_public(
        _uv_tool_install_command(version, python, index),
        cwd=work_dir,
        env=env,
        step="uv tool install from PyPI",
    )
    return InstalledTool(_tool_executable(tool_bin, "heph"), env)


def _install_public_pip(
    *,
    version: str,
    python: str,
    index: str,
    work_dir: Path,
) -> InstalledPipCommand:
    venv = work_dir / "pip-venv"
    _run_public(
        ["uv", "venv", str(venv), "--python", python, "--seed"],
        cwd=work_dir,
        env=None,
        step="create pip smoke-test venv",
    )
    venv_python = _venv_python(venv)
    env = _public_index_env(os.environ, work_dir / "pip-cache")
    _run_public(
        _pip_install_command(venv_python, version, index),
        cwd=work_dir,
        env=env,
        step="pip install from PyPI",
    )
    _run_public(
        [str(venv_python), "-m", "pip", "check"],
        cwd=work_dir,
        env=env,
        step="pip check public install",
    )
    return InstalledPipCommand(_venv_executable(venv, "heph"), venv_python)


def _uv_tool_install_command(version: str, python: str, index: str) -> list[str]:
    spec = "heph@latest" if version == "latest" else f"heph=={version}"
    return [
        "uv",
        "tool",
        "install",
        "--force",
        "--python",
        python,
        "--default-index",
        index,
        "--refresh-package",
        "heph",
        spec,
    ]


def _pip_install_command(python: Path, version: str, index: str) -> list[str]:
    spec = "heph" if version == "latest" else f"heph=={version}"
    return [
        str(python),
        "-m",
        "pip",
        "install",
        "--no-cache-dir",
        "--index-url",
        index,
        spec,
    ]


def _public_index_env(env: Mapping[str, str], cache_dir: Path) -> dict[str, str]:
    public_env = dict(env)
    for key in PUBLIC_INDEX_ENV_KEYS:
        public_env.pop(key, None)
    public_env["UV_CACHE_DIR"] = str(cache_dir)
    return public_env


def _run_public(
    command: list[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None,
    step: str,
) -> None:
    try:
        _run(command, cwd=cwd, env=env)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"{step} failed with exit code {exc.returncode}") from None


def _installed_heph_version(
    heph: Path,
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
) -> str:
    output = _run_output([str(heph), "--version"], cwd=cwd, env=env).strip()
    prefix = "heph "
    if not output.startswith(prefix) or len(output) == len(prefix):
        raise SystemExit(f"heph --version returned {output!r}")
    return output.removeprefix(prefix)


def _expected_runtime_version(version: str, expected_runtime_version: str | None) -> str:
    if expected_runtime_version is not None:
        return expected_runtime_version
    return f"v{version}"


def _stress_sdk_command(
    heph: Path,
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
) -> None:
    raw_capabilities = _run_output([str(heph), "sdk", "capabilities"], cwd=cwd, env=env)
    try:
        payload: object = json.loads(raw_capabilities)
    except ValueError as exc:
        raise SystemExit("heph sdk capabilities did not emit valid JSON") from exc
    _validate_sdk_capability_payload(payload)


if __name__ == "__main__":
    raise SystemExit(main())
