from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_dependency_sdist_allowlist import allowed_source_only_package_names
from scripts.release_stress_test import _validate_sdk_capability_payload, _wheel_install_command


def test_release_stress_binary_policy_uses_reviewed_source_allowlist() -> None:
    command = _wheel_install_command(
        Path("/tmp/venv/bin/python"),
        [Path("/tmp/dist/heph-0.1.0-py3-none-any.whl")],
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
