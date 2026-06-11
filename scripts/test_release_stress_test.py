from __future__ import annotations

from pathlib import Path

from scripts.check_dependency_sdist_allowlist import allowed_source_only_package_names
from scripts.release_stress_test import _wheel_install_command


def test_release_stress_binary_policy_uses_reviewed_source_allowlist() -> None:
    command = _wheel_install_command(
        Path("/tmp/venv/bin/python"),
        [Path("/tmp/dist/heph-0.1.0-py3-none-any.whl")],
    )

    no_binary = command[command.index("--no-binary") + 1]
    assert no_binary.split(",") == list(allowed_source_only_package_names())
    assert "numpy" in no_binary
    assert "pufferlib" in no_binary
