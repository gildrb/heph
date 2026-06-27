"""Armory creation and material import handlers for agent tools."""

from __future__ import annotations

import shlex
from collections.abc import Sequence
from pathlib import Path

from harness.agent.path_safety import safe_path
from harness.agent.tool_schema import ToolResult
from harness.armory.storage import (
    ARMORY_DIRS,
    MARKER_FILE,
    MATERIALS_DIR,
    ArmoryValidationError,
    default_armory_home,
    initialize,
    read_marker,
    validate,
)
from harness.materials.importing import import_material_files


def run_create_armory(
    path: str,
    *,
    workspace: Path,
    **_kwargs: object,
) -> ToolResult:
    try:
        target = safe_path(workspace, path)
    except ValueError as exc:
        return ToolResult(success=False, content=str(exc), error="path_escape")
    try:
        initialize(target)
        marker = read_marker(target)
    except OSError as exc:
        return ToolResult(
            success=False,
            content=f"Error creating armory: {exc}",
            error="io_error",
        )

    created_paths = [str((target / dirname).relative_to(target)) for dirname in ARMORY_DIRS]
    marker_rel = str(MARKER_FILE)
    lines = [
        f"Armory ready: {target}",
        "User source files belong in materials/.",
        "Internal Heph state belongs in .harness/.",
        "Required layout:",
        *(f"  - {dirname}/" for dirname in created_paths),
        f"  - {marker_rel}",
    ]
    return ToolResult(
        success=True,
        content="\n".join(lines),
        metadata={
            "path": str(target),
            "layout_version": marker.get("version", 0),
            "materials_dir": "materials",
            "marker": marker_rel,
        },
    )


def run_validate_armory(
    path: str,
    *,
    workspace: Path,
    **_kwargs: object,
) -> ToolResult:
    try:
        target = safe_path(workspace, path)
    except ValueError as exc:
        return ToolResult(success=False, content=str(exc), error="path_escape")
    try:
        validate(target)
        marker = read_marker(target)
    except ArmoryValidationError as exc:
        return ToolResult(success=False, content=str(exc), error="invalid_armory")
    except OSError as exc:
        return ToolResult(success=False, content=f"Error reading armory: {exc}", error="io_error")

    return ToolResult(
        success=True,
        content=(
            f"Valid Heph armory: {target}\n"
            "Use materials/ for user source files. .harness/ is internal state."
        ),
        metadata={
            "path": str(target),
            "layout_version": marker.get("version", 0),
            "materials_dir": "materials",
            "marker": str(MARKER_FILE),
        },
    )


def run_create_named_armory(
    name: str,
    *,
    workspace: Path,
    **_kwargs: object,
) -> ToolResult:
    _ = workspace
    target = _named_armory_target(name)
    if isinstance(target, ToolResult):
        return target
    if target.exists():
        try:
            validate(target)
            marker = read_marker(target)
        except (ArmoryValidationError, OSError) as exc:
            return ToolResult(
                success=False,
                content=f"Exact target exists but is not a valid Heph armory: {target}\n{exc}",
                metadata={"path": str(target), "created": False},
                error="invalid_existing_armory",
            )
        return _created_named_armory_result(target, marker, created=False)

    try:
        initialize(target)
        marker = read_marker(target)
    except OSError as exc:
        return ToolResult(
            success=False,
            content=f"Error creating armory: {exc}",
            metadata={"path": str(target), "created": False},
            error="io_error",
        )
    return _created_named_armory_result(target, marker, created=True)


def run_import_materials(
    source_path: str,
    *,
    workspace: Path,
    target_armory: str = "",
    create_if_missing: bool = False,
    **_kwargs: object,
) -> ToolResult:
    source = _agent_import_source(source_path, workspace)
    if isinstance(source, ToolResult):
        return source
    if not source.exists():
        return ToolResult(
            success=False,
            content=f"Source path not found: {source}",
            metadata={"source_path": str(source)},
            error="source_not_found",
        )

    target = _import_target_armory(
        target_armory,
        workspace=workspace,
        create_if_missing=create_if_missing is True,
    )
    if isinstance(target, ToolResult):
        return target

    result = import_material_files(source, target / MATERIALS_DIR)
    current_armory = _same_resolved_path(target, workspace)
    content = _import_materials_content(result.imported, target)
    return ToolResult(
        success=True,
        content=content,
        metadata={
            "operation": "import_materials",
            "source_path": str(source),
            "target_armory_path": str(target),
            "current_armory": current_armory,
            "refresh_current_armory": current_armory and bool(result.imported),
            "imported": list(result.imported),
            "imported_count": len(result.imported),
            "considered_count": result.considered,
            "skipped_duplicates": result.skipped_duplicates,
            "skipped_unsupported": result.skipped_unsupported,
        },
    )


def _created_named_armory_result(
    target: Path,
    marker: dict[str, object],
    *,
    created: bool,
) -> ToolResult:
    state = "Created" if created else "Armory already exists"
    return ToolResult(
        success=True,
        content=(
            f"{state}: {target}\n"
            f"User source files belong in {MATERIALS_DIR}/.\n"
            "Use the exact armory name when opening or importing."
        ),
        metadata={
            "path": str(target),
            "created": created,
            "layout_version": marker.get("version", 0),
            "materials_dir": MATERIALS_DIR,
            "marker": str(MARKER_FILE),
        },
    )


def _named_armory_target(name: str) -> Path | ToolResult:
    cleaned = name.strip()
    if error := _exact_armory_name_error(cleaned):
        return ToolResult(
            success=False,
            content=error,
            metadata={"requested_name": name},
            error="invalid_armory_name",
        )
    return (_resolved_armory_home() / cleaned).resolve()


def _exact_armory_name_error(name: str) -> str:
    candidate = Path(name)
    if not name:
        return "Armory name is required."
    if candidate.is_absolute() or ".." in candidate.parts or len(candidate.parts) != 1:
        return "Armory name must be one exact folder name inside the armory home."
    return ""


def _resolved_armory_home() -> Path:
    return default_armory_home().expanduser().resolve()


def _import_target_armory(
    target_armory: str,
    *,
    workspace: Path,
    create_if_missing: bool,
) -> Path | ToolResult:
    target = _current_or_exact_armory_target(target_armory, workspace)
    if isinstance(target, ToolResult):
        return target
    if not target.exists():
        if not create_if_missing:
            return ToolResult(
                success=False,
                content=(
                    f"No exact armory found at {target}. "
                    "I did not create one because create_if_missing is false."
                ),
                metadata={"target_armory_path": str(target), "created": False},
                error="missing_armory",
            )
        try:
            initialize(target)
        except OSError as exc:
            return ToolResult(
                success=False,
                content=f"Error creating target armory: {exc}",
                metadata={"target_armory_path": str(target), "created": False},
                error="io_error",
            )
    try:
        validate(target)
        read_marker(target)
    except ArmoryValidationError as exc:
        return ToolResult(
            success=False,
            content=f"Target is not a valid Heph armory: {target}\n{exc}",
            metadata={"target_armory_path": str(target)},
            error="invalid_armory",
        )
    except OSError as exc:
        return ToolResult(
            success=False,
            content=f"Error reading target armory: {exc}",
            metadata={"target_armory_path": str(target)},
            error="io_error",
        )
    return target


def _current_or_exact_armory_target(target_armory: str, workspace: Path) -> Path | ToolResult:
    cleaned = target_armory.strip()
    if not cleaned:
        try:
            target = workspace.expanduser().resolve()
            validate(target)
            return target
        except (ArmoryValidationError, OSError) as exc:
            return ToolResult(
                success=False,
                content=f"Current workspace is not a valid Heph armory: {workspace}\n{exc}",
                metadata={"target_armory_path": str(workspace)},
                error="invalid_current_armory",
            )
    if _is_simple_armory_name(cleaned):
        return (_resolved_armory_home() / cleaned).resolve()
    return _explicit_armory_path(cleaned)


def _is_simple_armory_name(value: str) -> bool:
    candidate = Path(value)
    return (
        not candidate.is_absolute() and ".." not in candidate.parts and len(candidate.parts) == 1
    )


def _explicit_armory_path(raw_path: str) -> Path | ToolResult:
    try:
        target = Path(raw_path).expanduser().resolve()
        armory_home = _resolved_armory_home()
    except (OSError, RuntimeError) as exc:
        return ToolResult(
            success=False,
            content=f"Armory path cannot be resolved: {raw_path}\n{exc}",
            metadata={"target_armory": raw_path},
            error="invalid_armory_path",
        )
    if not target.is_relative_to(armory_home):
        return ToolResult(
            success=False,
            content=(
                f"Armory path must stay inside the armory home ({armory_home}). "
                f"Requested: {target}"
            ),
            metadata={"target_armory_path": str(target), "armory_home": str(armory_home)},
            error="path_escape",
        )
    return target


def _agent_import_source(raw_path: str, workspace: Path) -> Path | ToolResult:
    cleaned = _single_path_argument(raw_path)
    if not cleaned:
        return ToolResult(
            success=False,
            content="Source path is required.",
            error="missing_source_path",
        )
    candidate = Path(cleaned)
    if candidate.is_absolute() or (candidate.parts and candidate.parts[0].startswith("~")):
        return ToolResult(
            success=False,
            content=(
                "Absolute source paths and home shortcuts are not accepted in agent turns. "
                "Use a path relative to the current armory workspace."
            ),
            metadata={"source_path": cleaned},
            error="absolute_source_rejected",
        )
    if ".." in candidate.parts:
        return ToolResult(
            success=False,
            content=f"Source path escapes the current armory workspace: {raw_path}",
            metadata={"source_path": raw_path},
            error="path_escape",
        )

    return _workspace_import_source(candidate, workspace, raw_path)


def _workspace_import_source(candidate: Path, workspace: Path, raw_path: str) -> Path | ToolResult:
    try:
        workspace_root = workspace.expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        return ToolResult(
            success=False,
            content=f"Current workspace is not a valid Heph armory: {workspace}\n{exc}",
            metadata={"source_path": raw_path},
            error="invalid_current_armory",
        )

    current = workspace_root
    for part in candidate.parts:
        current /= part
        component_error = _source_component_error(current, workspace_root, raw_path)
        if component_error is not None:
            return component_error
    return current


def _source_component_error(
    current: Path,
    workspace_root: Path,
    raw_path: str,
) -> ToolResult | None:
    if current.is_symlink():
        return ToolResult(
            success=False,
            content=f"Source path must not traverse symlinks: {raw_path}",
            metadata={"source_path": raw_path},
            error="symlink_source_rejected",
        )
    try:
        resolved = current.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        return ToolResult(
            success=False,
            content=f"Source path cannot be resolved: {raw_path}\n{exc}",
            metadata={"source_path": raw_path},
            error="invalid_source_path",
        )
    if not resolved.is_relative_to(workspace_root):
        return ToolResult(
            success=False,
            content=f"Source path escapes the current armory workspace: {raw_path}",
            metadata={"source_path": raw_path},
            error="path_escape",
        )
    return None


def _single_path_argument(raw_path: str) -> str:
    cleaned = raw_path.strip()
    try:
        parts = shlex.split(cleaned)
    except ValueError:
        return cleaned
    if len(parts) == 1:
        return parts[0]
    return cleaned


def _same_resolved_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return False


def _import_materials_content(imported: Sequence[str], target: Path) -> str:
    if not imported:
        return (
            f"No new files imported into {target / MATERIALS_DIR}. "
            "Every supported source was already present or no supported files were found."
        )
    lines = [
        f"Imported {len(imported)} file{'s' if len(imported) != 1 else ''} "
        f"into {target / MATERIALS_DIR}:"
    ]
    lines.extend(f"  - {name}" for name in imported)
    return "\n".join(lines)
