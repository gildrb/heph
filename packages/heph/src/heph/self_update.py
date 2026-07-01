from __future__ import annotations

import shlex
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

CommandRunner = Callable[[tuple[str, ...]], int]


@dataclass(frozen=True, slots=True)
class UpdateContext:
    executable: Path
    package_module: Path
    project_root: Path
    source_checkout: bool
    python_version: str


@dataclass(frozen=True, slots=True)
class UpdatePlan:
    installer: str
    command: tuple[str, ...]
    details: tuple[str, ...]

    @property
    def runnable(self) -> bool:
        return bool(self.command)


class UpdateFailedError(RuntimeError):
    def __init__(self, command: tuple[str, ...], returncode: int) -> None:
        super().__init__(
            f"update command failed with exit code {returncode}: {shlex.join(command)}"
        )
        self.command = command
        self.returncode = returncode


def choose_update_plan(context: UpdateContext) -> UpdatePlan:
    if context.source_checkout:
        return _source_checkout_plan(context)
    if _is_uv_tool_install(context):
        return _uv_tool_plan(context)
    return _pip_plan(context)


def format_update_plan(plan: UpdatePlan, *, dry_run: bool) -> str:
    lines = ["Heph update", *plan.details]
    if plan.command:
        prefix = "Would run" if dry_run else "Running"
        lines.append(f"{prefix}: {shlex.join(plan.command)}")
    return "\n".join(lines)


def run_update_plan(plan: UpdatePlan, *, runner: CommandRunner | None = None) -> None:
    if not plan.command:
        return
    command_runner = runner or _run_command
    returncode = command_runner(plan.command)
    if returncode != 0:
        raise UpdateFailedError(plan.command, returncode)


def _source_checkout_plan(context: UpdateContext) -> UpdatePlan:
    uv_command = _uv_tool_install_command(context.python_version)
    return UpdatePlan(
        installer="source",
        command=(),
        details=(
            f"  current Python: {context.executable}",
            f"  package module: {context.package_module}",
            "",
            "This executable is importing a source checkout, so the update command will not "
            "overwrite it.",
            f"  checkout: {context.project_root}",
            "",
            "To refresh this checkout:",
            f"  cd {context.project_root}",
            "  git pull --ff-only",
            "  uv sync",
            "  uv run heph",
            "",
            "To install or refresh the released tool instead:",
            f"  {shlex.join(uv_command)}",
        ),
    )


def _uv_tool_plan(context: UpdateContext) -> UpdatePlan:
    uv = shutil.which("uv")
    if uv is None:
        return UpdatePlan(
            installer="uv",
            command=(),
            details=(
                f"  current Python: {context.executable}",
                f"  package module: {context.package_module}",
                "",
                "This looks like a uv tool install, but `uv` is not on PATH.",
                "Install uv or put it on PATH, then run:",
                f"  {shlex.join(_uv_tool_install_command(context.python_version))}",
            ),
        )
    command = (uv, *_uv_tool_install_command(context.python_version)[1:])
    return UpdatePlan(
        installer="uv",
        command=command,
        details=(
            f"  current Python: {context.executable}",
            f"  package module: {context.package_module}",
            "  installer: uv tool",
        ),
    )


def _pip_plan(context: UpdateContext) -> UpdatePlan:
    return UpdatePlan(
        installer="pip",
        command=(
            str(context.executable),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--upgrade-strategy",
            "eager",
            "heph",
        ),
        details=(
            f"  current Python: {context.executable}",
            f"  package module: {context.package_module}",
            "  installer: pip-compatible environment",
        ),
    )


def _uv_tool_install_command(python_version: str) -> tuple[str, ...]:
    return (
        "uv",
        "tool",
        "install",
        "--force",
        "--python",
        python_version,
        "--refresh-package",
        "heph",
        "heph@latest",
    )


def _is_uv_tool_install(context: UpdateContext) -> bool:
    return _contains_uv_tool_heph_path(context.executable) or _contains_uv_tool_heph_path(
        context.package_module
    )


def _contains_uv_tool_heph_path(path: Path) -> bool:
    return "/uv/tools/heph/" in path.as_posix()


def _run_command(command: tuple[str, ...]) -> int:
    completed = subprocess.run(command, check=False)
    return completed.returncode
