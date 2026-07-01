from __future__ import annotations

from pathlib import Path

import pytest
from heph.self_update import (
    UpdateContext,
    UpdateFailedError,
    choose_update_plan,
    format_update_plan,
    run_update_plan,
)


def _context(
    *,
    executable: Path = Path("/opt/heph/bin/python"),
    package_module: Path = Path("/opt/heph/lib/python3.13/site-packages/heph/self_update.py"),
    source_checkout: bool = False,
) -> UpdateContext:
    return UpdateContext(
        executable=executable,
        package_module=package_module,
        project_root=Path("/src/heph"),
        source_checkout=source_checkout,
        python_version="3.13",
    )


def test_source_checkout_plan_refuses_to_overwrite_checkout() -> None:
    plan = choose_update_plan(_context(source_checkout=True))

    assert plan.installer == "source"
    assert not plan.runnable
    assert "git pull --ff-only" in "\n".join(plan.details)
    assert "heph@latest" in "\n".join(plan.details)


def test_uv_tool_plan_force_refreshes_latest_release(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("heph.self_update.shutil.which", lambda name: f"/bin/{name}")
    context = _context(
        executable=Path("/Users/gil/.local/share/uv/tools/heph/bin/python"),
        package_module=Path(
            "/Users/gil/.local/share/uv/tools/heph/lib/python3.13/site-packages/heph/__init__.py"
        ),
    )

    plan = choose_update_plan(context)

    assert plan.installer == "uv"
    assert plan.command == (
        "/bin/uv",
        "tool",
        "install",
        "--force",
        "--python",
        "3.13",
        "--refresh-package",
        "heph",
        "heph@latest",
    )


def test_pip_plan_upgrades_heph_and_dependencies() -> None:
    plan = choose_update_plan(_context())

    assert plan.installer == "pip"
    assert plan.command == (
        "/opt/heph/bin/python",
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--upgrade-strategy",
        "eager",
        "heph",
    )


def test_format_update_plan_supports_dry_run() -> None:
    plan = choose_update_plan(_context())

    text = format_update_plan(plan, dry_run=True)

    assert "Would run:" in text
    assert "python -m pip install" in text


def test_run_update_plan_reports_command_failure() -> None:
    plan = choose_update_plan(_context())

    with pytest.raises(UpdateFailedError) as exc_info:
        run_update_plan(plan, runner=lambda _command: 17)

    assert exc_info.value.returncode == 17
