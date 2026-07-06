"""System prompt builder for Heph's source-grounded agent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from ai.logging import get_logger

from harness.agent.tools import (
    ToolRegistry,
    ToolSchema,
    ToolSpec,
    default_registry,
)
from harness.armory.state_files import read_armory_state_text
from harness.armory.trust import armory_path_trusted
from harness.materials import MaterialRole, infer_material_role

if TYPE_CHECKING:
    from collections.abc import Sequence

    from harness.rag.health import ExtractionHealthIssue

_log = get_logger("harness.agent.prompt")

_DEFAULT_ROLE_BLOCK = """\
You are running inside Heph.
"""

_BASE_GUIDELINES = (
    "Answer with the minimum useful text.",
    "No greetings, filler, praise, reassurance, emoji, stickers, or decorative symbols.",
    "Do not fabricate. If evidence is missing or uncertain, say what is missing.",
    "For material-specific claims, reason from retrieved evidence and cite IDs like `[E1]`.",
    "Use general reasoning to explain evidence, never as pretend file evidence.",
    "Verify exact file/source details, numbers, formulas, dates, labels, units, and wording.",
    "If asked what `[E1]` means, quote that evidence and name its source.",
    "During recall, follow injected recall instructions and keep the answer hidden.",
    "Armory: portable workspace with `.harness/armory.toml`.",
    "User files go in `materials/`; app state stays in `.harness/`.",
    "Use `create_armory` or `validate_armory` for armory setup/repair.",
    "Use structure only when useful; use numbered steps for procedures and fenced code for code.",
    "Render math as readable Unicode when practical; preserve exact source formulas when needed.",
    "Preserve exact table values from sources.",
)


_CUSTOM_PROMPT_FILE = Path(".harness/system_prompt.md")
ARMORY_PROMPT_TRUST_ENV = "HARNESS_TRUST_ARMORY_PROMPTS"


@dataclass(frozen=True, slots=True)
class SystemPrompt:
    role: str
    tool_docs: str
    guidelines: str
    context: str
    memory: str = ""

    def render(self) -> str:
        return "\n\n".join(part.strip() for part in self.sections if part.strip())

    @property
    def sections(self) -> tuple[str, ...]:
        return (
            self.role,
            self.tool_docs,
            self.guidelines,
            self.context,
            self.memory,
        )


def _one_line(text: str) -> str:
    return " ".join(text.split())


def _tool_specs_from_schemas(schemas: list[ToolSchema]) -> list[ToolSpec]:
    return [
        ToolSpec(
            schema=schema,
            handler=lambda **_kwargs: "",
        )
        for schema in schemas
    ]


def render_tool_docs(registry_or_schemas: ToolRegistry | list[ToolSchema]) -> str:
    specs = (
        registry_or_schemas.specs
        if isinstance(registry_or_schemas, ToolRegistry)
        else _tool_specs_from_schemas(registry_or_schemas)
    )
    lines = ["Available tools:"]
    for spec in specs:
        function = spec.schema["function"]
        snippet = _one_line(function["description"])
        lines.append(f"- {spec.name}: {snippet}")

    return "\n".join(lines)


def render_guidelines(registry_or_schemas: ToolRegistry | list[ToolSchema]) -> str:
    specs = (
        registry_or_schemas.specs
        if isinstance(registry_or_schemas, ToolRegistry)
        else _tool_specs_from_schemas(registry_or_schemas)
    )
    guidelines = (*_BASE_GUIDELINES, *_tool_prompt_guidelines(specs))
    return "\n".join(["## Guidelines", "", *(f"- {guideline}" for guideline in guidelines)])


def _tool_prompt_guidelines(specs: Sequence[ToolSpec]) -> tuple[str, ...]:
    seen: set[str] = set()
    guidelines: list[str] = []
    for spec in specs:
        for guideline in spec.prompt_guidelines:
            guideline = _one_line(guideline)
            if guideline and guideline not in seen:
                seen.add(guideline)
                guidelines.append(guideline)
    return tuple(guidelines)


def _prompt_role(armory_path: Path | None) -> str:
    if armory_path is None:
        return _DEFAULT_ROLE_BLOCK

    custom_prompt_file = armory_path / _CUSTOM_PROMPT_FILE
    if not custom_prompt_file.is_file():
        return _DEFAULT_ROLE_BLOCK
    if not armory_path_trusted(armory_path, ARMORY_PROMPT_TRUST_ENV):
        _log.warning(
            "custom system prompt skipped; explicit armory trust not enabled",
            extra={
                "fields": {
                    "armory": str(armory_path),
                    "file": str(_CUSTOM_PROMPT_FILE),
                    "env": ARMORY_PROMPT_TRUST_ENV,
                }
            },
        )
        return _DEFAULT_ROLE_BLOCK

    try:
        custom_prompt = read_armory_state_text(armory_path, _CUSTOM_PROMPT_FILE).strip()
    except OSError as exc:
        _log.warning(
            "custom system prompt skipped; prompt file could not be read safely",
            extra={"fields": {"armory": str(armory_path), "error": str(exc)}},
        )
        return _DEFAULT_ROLE_BLOCK
    if not custom_prompt:
        return _DEFAULT_ROLE_BLOCK

    _log.info(
        "using custom system prompt",
        extra={"fields": {"armory": str(armory_path), "file": str(_CUSTOM_PROMPT_FILE)}},
    )
    return custom_prompt


def _source_file_context(source_files: list[str] | None) -> list[str]:
    if not source_files:
        return []

    file_list = "\n".join(f"  - {f}" for f in source_files[:50])
    parts = [f"Available material files:\n{file_list}"]
    if role_hints := _material_role_hints(source_files):
        parts.append(role_hints)
    return parts


def _material_role_hints(source_files: list[str]) -> str:
    role_counts: dict[MaterialRole, int] = {}
    role_examples: dict[MaterialRole, str] = {}
    for rel_path in source_files:
        material_role, _confidence, _reason = infer_material_role(rel_path)
        role_counts[material_role] = role_counts.get(material_role, 0) + 1
        role_examples.setdefault(material_role, rel_path)

    role_lines = ["Material role hints:"]
    for material_role, count in sorted(role_counts.items()):
        label = material_role.replace("_", " ")
        plural = "s" if count != 1 else ""
        example = role_examples[material_role]
        role_lines.append(f"  - {label}: {count} file{plural}; e.g. {example}")
    return "\n".join(role_lines)


def _unindexable_files_warning(unindexable_files: dict[str, str] | None) -> str:
    if not unindexable_files:
        return ""

    lines = ["WARNING: The following files could not be indexed for retrieval:"]
    for rel, reason in sorted(unindexable_files.items()):
        lines.append(f"  - {rel}: {reason}")
    lines.append(
        "These files are visible but NOT searchable via read_file or search_files. "
        "Do NOT attempt to read them. Do NOT answer questions about their contents "
        "from outside knowledge. Say the material is visible but unavailable as "
        "armory evidence until document conversion or indexing succeeds."
    )
    return "\n".join(lines)


def _extraction_health_warning(issues: Sequence[ExtractionHealthIssue]) -> str:
    if not issues:
        return ""

    lines = ["WARNING: The following indexed files contain extraction health issues:"]
    for issue in issues[:10]:
        markers = ", ".join(issue.forbidden_text_present)
        lines.append(f"  - {issue.source}: {markers}")
    remaining = len(issues) - 10
    if remaining > 0:
        lines.append(f"  - ... and {remaining} more file(s)")
    lines.append(
        "Treat affected indexed chunks as unreliable extraction output. Do NOT "
        "answer from affected files unless clean retrieved evidence directly "
        "supports the claim. Tell the user to run `heph health` and rebuild or "
        "reconvert the affected material before relying on it."
    )
    return "\n".join(lines)


def _context_section(
    *,
    armory_path: Path | None,
    source_files: list[str] | None,
    unindexable_files: dict[str, str] | None,
    extraction_health_issues: Sequence[ExtractionHealthIssue],
) -> str:
    context_parts = [f"Current date: {datetime.now(UTC).strftime('%Y-%m-%d')}"]
    if armory_path is None:
        return "\n\n".join(context_parts)

    context_parts.append(f"Armory workspace: {armory_path}")
    context_parts.extend(_source_file_context(source_files))
    if warning := _unindexable_files_warning(unindexable_files):
        context_parts.append(warning)
    if warning := _extraction_health_warning(extraction_health_issues):
        context_parts.append(warning)
    return "\n\n".join(context_parts)


def build_system_prompt_sections(
    *,
    armory_path: Path | None = None,
    source_files: list[str] | None = None,
    unindexable_files: dict[str, str] | None = None,
    extraction_health_issues: Sequence[ExtractionHealthIssue] = (),
    memory_context: str = "",
    registry: ToolRegistry | None = None,
) -> SystemPrompt:
    tool_registry = default_registry if registry is None else registry

    return SystemPrompt(
        role=_prompt_role(armory_path),
        tool_docs=render_tool_docs(tool_registry),
        guidelines=render_guidelines(tool_registry),
        context=_context_section(
            armory_path=armory_path,
            source_files=source_files,
            unindexable_files=unindexable_files,
            extraction_health_issues=extraction_health_issues,
        ),
        memory=memory_context,
    )


def build_system_prompt(
    *,
    armory_path: Path | None = None,
    source_files: list[str] | None = None,
    unindexable_files: dict[str, str] | None = None,
    extraction_health_issues: Sequence[ExtractionHealthIssue] = (),
    memory_context: str = "",
    registry: ToolRegistry | None = None,
) -> str:
    return build_system_prompt_sections(
        armory_path=armory_path,
        source_files=source_files,
        unindexable_files=unindexable_files,
        extraction_health_issues=extraction_health_issues,
        memory_context=memory_context,
        registry=registry,
    ).render()
