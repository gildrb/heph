"""Material inventory tools for the agent harness."""

from __future__ import annotations

from pathlib import Path

from hephaistos.agent.tool_schema import ToolResult
from hephaistos.armory.storage import (
    ARMORY_DIRS,
    MARKER_FILE,
    ArmoryValidationError,
    initialize,
    read_marker,
    validate,
)
from hephaistos.materials import material_manifest


def run_create_armory(
    path: str,
    *,
    workspace: Path,
    **_kwargs: object,
) -> ToolResult:
    """Create or repair a Hephaistos armory inside the workspace."""
    try:
        target = _safe_path(workspace, path)
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
        "User study files belong in materials/.",
        "Internal Hephaistos state belongs in .hephaistos/.",
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
    """Validate a Hephaistos armory inside the workspace."""
    try:
        target = _safe_path(workspace, path)
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
            f"Valid Hephaistos armory: {target}\n"
            "Use materials/ for user study files. .hephaistos/ is internal state."
        ),
        metadata={
            "path": str(target),
            "layout_version": marker.get("version", 0),
            "materials_dir": "materials",
            "marker": str(MARKER_FILE),
        },
    )


def run_inspect_materials(
    *,
    workspace: Path,
    path: str = "",
    **_kwargs: object,
) -> ToolResult:
    """Return the material manifest with transparent role classification."""
    try:
        armory = _safe_path(workspace, path or ".")
    except ValueError as exc:
        return ToolResult(success=False, content=str(exc), error="path_escape")
    try:
        materials = material_manifest(armory)
    except OSError as exc:
        return ToolResult(
            success=False,
            content=f"Error reading materials: {exc}",
            error="io_error",
        )
    if not materials:
        return ToolResult(
            success=True,
            content="No visible materials found.",
            metadata={"count": 0, "roles": {}},
        )

    role_counts: dict[str, int] = {}
    rows = ["Material inventory:"]
    for material in materials:
        role_counts[material.role] = role_counts.get(material.role, 0) + 1
        rows.append(
            f"- {material.rel_path}: {material.role} "
            f"({material.confidence:.2f}; {material.reason})"
        )
    return ToolResult(
        success=True,
        content="\n".join(rows),
        metadata={"count": len(materials), "roles": role_counts},
    )


def _safe_path(workspace: Path, rel_path: str) -> Path:
    resolved = (workspace / rel_path).resolve()
    if not resolved.is_relative_to(workspace.resolve()):
        raise ValueError(f"Path escapes workspace: {rel_path}")
    return resolved
