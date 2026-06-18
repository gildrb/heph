from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_dependency_sdist_allowlist import allowed_source_only_package_names
from scripts.release_stress_test import (
    DEFAULT_WORK_ROOT,
    _build_parser,
    _pip_compile_command,
    _pip_install_command,
    _uv_tool_install_command,
    _validate_release_state_payload,
    _validate_sdk_capability_payload,
    _wheel_install_command,
)


def test_release_stress_uses_ignored_artifact_scratch_root_by_default() -> None:
    args = _build_parser().parse_args([])

    assert args.work_root == DEFAULT_WORK_ROOT


def test_release_stress_binary_policy_uses_reviewed_source_allowlist() -> None:
    command = _wheel_install_command(
        Path("/tmp/venv/bin/python"),
        [Path("/tmp/dist/heph-0.1.49-py3-none-any.whl")],
    )

    no_binary = command[command.index("--no-binary") + 1]
    assert no_binary.split(",") == list(allowed_source_only_package_names())
    assert "numpy" in no_binary
    assert "pufferlib" in no_binary


def test_release_stress_validates_sdk_capability_payload() -> None:
    _validate_sdk_capability_payload(
        {
            "version": 37,
            "jsonl": {
                "protocol": "heph-sdk-jsonl",
                "version": 1,
            },
        }
    )

    with pytest.raises(SystemExit, match="non-integer SDK version"):
        _validate_sdk_capability_payload(
            {
                "version": True,
                "jsonl": {
                    "protocol": "heph-sdk-jsonl",
                    "version": 1,
                },
            }
        )

    with pytest.raises(SystemExit, match="unexpected JSONL protocol"):
        _validate_sdk_capability_payload(
            {
                "version": 37,
                "jsonl": {
                    "protocol": "other",
                    "version": 1,
                },
            }
        )


def test_release_stress_builds_uv_tool_install_command() -> None:
    command = _uv_tool_install_command(Path("/tmp/dist"), "0.1.49", "3.13")

    assert command == [
        "uv",
        "tool",
        "install",
        "--force",
        "--python",
        "3.13",
        "--find-links",
        "/tmp/dist",
        "--no-sources",
        "--refresh-package",
        "heph",
        "--refresh-package",
        "heph-ai",
        "--refresh-package",
        "heph-extensions",
        "--refresh-package",
        "heph-interfaces",
        "--refresh-package",
        "hephaion",
        "heph==0.1.49",
    ]


def test_release_stress_builds_pip_install_command() -> None:
    command = _pip_install_command(Path("/tmp/venv/bin/python"), Path("/tmp/dist"), "0.1.49")

    assert command == [
        "/tmp/venv/bin/python",
        "-m",
        "pip",
        "install",
        "--find-links",
        "/tmp/dist",
        "heph==0.1.49",
    ]


def test_release_stress_builds_platform_compile_command() -> None:
    command = _pip_compile_command(
        Path("/tmp/heph-release.in"),
        Path("/tmp/dist"),
        "x86_64-pc-windows-msvc",
        Path("/tmp/heph-release-windows.txt"),
    )

    assert command == [
        "uv",
        "--quiet",
        "pip",
        "compile",
        "/tmp/heph-release.in",
        "--find-links",
        "/tmp/dist",
        "--no-sources",
        "--python-platform",
        "x86_64-pc-windows-msvc",
        "--output-file",
        "/tmp/heph-release-windows.txt",
    ]


def test_release_stress_validates_release_state_payload() -> None:
    _validate_release_state_payload(
        {
            "package_version": "0.1.49",
            "official": {
                "package": "heph",
                "command": "heph",
                "version": "0.1.49",
                "tag": "v0.1.49",
            },
            "runtime": {
                "channel": "source",
                "version": "",
                "python": "/tmp/python",
            },
        },
        expected_version="0.1.49",
    )
    _validate_release_state_payload(
        {
            "package_version": "0.1.49",
            "official": {
                "package": "heph",
                "command": "heph",
                "version": "0.1.49",
                "tag": "v0.1.49",
            },
            "runtime": {
                "channel": "pypi",
                "version": "v0.1.49",
                "python": "/tmp/python",
            },
        },
        expected_version="0.1.49",
        expected_runtime_channel="pypi",
        expected_runtime_version="v0.1.49",
    )

    with pytest.raises(SystemExit, match="wrong official tag"):
        _validate_release_state_payload(
            {
                "package_version": "0.1.49",
                "official": {
                    "package": "heph",
                    "command": "heph",
                    "version": "0.1.49",
                    "tag": "v0.0.0",
                },
                "runtime": {
                    "channel": "source",
                    "version": "",
                    "python": "/tmp/python",
                },
            },
            expected_version="0.1.49",
        )

    with pytest.raises(SystemExit, match="wrong runtime channel"):
        _validate_release_state_payload(
            {
                "package_version": "0.1.49",
                "official": {
                    "package": "heph",
                    "command": "heph",
                    "version": "0.1.49",
                    "tag": "v0.1.49",
                },
                "runtime": {
                    "channel": "source",
                    "version": "v0.1.49",
                    "python": "/tmp/python",
                },
            },
            expected_version="0.1.49",
            expected_runtime_channel="pypi",
        )
