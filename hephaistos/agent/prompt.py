"""Rich system prompt builder with tool docs and anti-hallucination guardrails.

Builds a structured system prompt that gives the LLM:
1. Its role as a study drill engine
2. Tool documentation (so it knows exactly how to use each tool)
3. Anti-hallucination directives (cite evidence, never fabricate)
4. Context: current date, armory info, memory of what's been studied

This is the single most important file for answer quality — a well-informed
model with clear guardrails hallucinates far less.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from hephaistos.agent.persona import DEFAULT as _DEFAULT_PERSONA
from hephaistos.agent.persona import Persona
from hephaistos.agent.tools import ToolRegistry, ToolSchema, default_registry
from hephaistos.logging import get_logger
from hephaistos.materials import MaterialRole, infer_material_role

_log = get_logger("agent.prompt")

_ANTI_HALLUCINATION = """\
## Accuracy Rules (CRITICAL — violation is the worst possible outcome)

1. **Never fabricate information.** If you are not certain, say "I'm not certain" and explain why.
2. **Always cite retrieved evidence.** When a "Retrieved evidence for this question"
   section appears, cite evidence IDs like `[E1]` or `[E1][E2]` after factual claims.
   Do **not** cite raw filenames by themselves.
3. **Never guess at values.** Numbers, formulas, dates, names — if you're not sure, say so.
   Use read_file or search_files to verify before answering.
4. **Distinguish certain from uncertain.** Use "according to [source]" for verified facts.
   Use "I believe..." or "this is my understanding" for inferences, and flag them.
5. **If the source doesn't cover it, say so.** Do NOT draw on outside knowledge to fill gaps.
   Say: "The armory documents don't cover this topic. I can search online if you'd like."
6. **Verify before correcting the student.** Read the relevant source document before telling
   a student they are wrong. You might be the one who's wrong.
7. **When describing diagrams/figures, be precise.** Every label, axis, unit, and value must
   come from the actual image — never approximate or invent details.
8. **No retrieved evidence for a question.** If no "Retrieved evidence for this question"
   section appears before a question, the armory had no relevant documents. Answer from your
   own knowledge only if you are confident, and explicitly say the answer is not grounded in
   armory evidence. Do NOT fabricate evidence citations.
"""

_STUDY_LOOP = """\
## Study Loop

A deterministic controller tracks the active study phase
and injects exact turn-by-turn constraints.
Follow the controller's current phase instructions
over any generic tutoring instinct.

Every question follows this cycle:

1. **PRESENT**: When a student asks about a question or topic, show the complete solution
   or method from the source material. Cite the document. Walk through reasoning step by step.
2. **READY**: After presenting, ask the student to signal when they are ready to recall.
3. **RECALL**: The student reproduces the solution from memory. Wait for their attempt.
4. **ASSESS**: Compare their attempt against the source. Do NOT show the original again.
   - **Correct**: Move to the next question.
   - **Partial**: State what is missing in one sentence. Do not fill in the gap.
   - **Wrong**: Give a hint about the first step only. Nothing more.
5. **LOOP**: Repeat until the student gets it right, then present the next question.

If the student asks to skip, present the next question.
If the student asks for the answer, remind them to try recalling first.
"""

_HEPHAISTOS_OPERATIONS = """\
## Hephaistos Operations

You are an expert operator of Hephaistos itself. The user should focus on studying,
not on configuring the app or memorizing filesystem rules.

Armory contract:
- A Hephaistos armory is a portable study workspace identified by `.hephaistos/armory.toml`.
- User study files belong in `materials/`. This includes lecture notes, PDFs, slides,
  codebases, assignments, vocabulary tables, and past exams.
- Internal app state belongs in `.hephaistos/`. Do not tell users to manage internal files
  unless debugging or repairing an armory.
- Do not create `source/`, `library/`, or `notes/` folders. Use `materials/`.
- If the user wants to create, initialize, fix, validate, or organize a Hephaistos workspace,
  use `create_armory` or `validate_armory` instead of manually approximating the layout.
- After creating an armory, tell the user to put their files in `materials/` and ask what
  they want to study first.
"""

_FORMAT_RULES = """\
## Format

- State things directly.
- No greetings. No sign-offs. No pleasantries.
- Never use Em-Dashes (\u2014) or Emojis in any output.
- Use numbered steps for procedures.
- Use fenced code blocks for code.
- Use LaTeX for mathematical expressions ($...$ for inline, $$...$$ for display).
- Keep responses short. One idea per response when possible.
- Tables: reproduce structure with exact values from source.
"""


_CUSTOM_PROMPT_FILE = Path(".hephaistos/system_prompt.md")


@dataclass(frozen=True, slots=True)
class SystemPrompt:
    """Structured system prompt sections."""

    role: str
    study_loop: str
    anti_hallucination: str
    tool_docs: str
    hephaistos_operations: str
    format_rules: str
    context: str
    memory: str = ""

    def render(self) -> str:
        """Render the prompt using the legacy section separator."""
        return "\n\n".join(part for part in self.sections if part)

    @property
    def sections(self) -> tuple[str, ...]:
        return (
            self.role,
            self.study_loop,
            self.anti_hallucination,
            self.tool_docs,
            self.hephaistos_operations,
            self.format_rules,
            self.context,
            self.memory,
        )


def render_tool_docs(schemas: list[ToolSchema]) -> str:
    """Render Markdown tool documentation from OpenAI-compatible schemas."""
    lines = [
        "## Tools",
        "",
        "You have access to these tools. Use them to read source material and verify answers.",
    ]
    for schema in schemas:
        function = schema["function"]
        params = function["parameters"]
        required = set(params["required"])
        lines.extend(["", f"### {function['name']}", function["description"]])
        for name, param in params["properties"].items():
            marker = "required" if name in required else "optional"
            description = param.get("description", "")
            lines.append(f"- `{name}` ({marker}): {description}")
    return "\n".join(lines)


def _material_role_summary(source_files: list[str]) -> str:
    """Render cheap material role hints for the model."""
    counts: dict[MaterialRole, int] = {}
    examples: dict[MaterialRole, str] = {}
    for rel_path in source_files:
        role, _confidence, _reason = infer_material_role(rel_path)
        counts[role] = counts.get(role, 0) + 1
        examples.setdefault(role, rel_path)
    if not counts:
        return ""
    lines = ["Material role hints:"]
    for role, count in sorted(counts.items()):
        label = role.replace("_", " ")
        example = examples[role]
        plural = "s" if count != 1 else ""
        lines.append(f"  - {label}: {count} file{plural}; e.g. {example}")
    return "\n".join(lines)


def _load_custom_prompt(armory_path: Path) -> str | None:
    """Load a custom system prompt from the armory, if one exists.

    Looks for ``.hephaistos/system_prompt.md`` in the armory root.
    Returns its contents stripped, or ``None`` if the file is absent.
    """
    prompt_file = armory_path / _CUSTOM_PROMPT_FILE
    if prompt_file.is_file():
        content = prompt_file.read_text(encoding="utf-8").strip()
        if content:
            _log.info(
                "using custom system prompt",
                extra={"fields": {"armory": str(armory_path), "file": str(_CUSTOM_PROMPT_FILE)}},
            )
            return content
    return None


def build_system_prompt_sections(
    *,
    armory_path: Path | None = None,
    source_files: list[str] | None = None,
    memory_context: str = "",
    persona: Persona | None = None,
    registry: ToolRegistry | None = None,
) -> SystemPrompt:
    """Build structured system prompt sections.

    Parameters
    ----------
    armory_path :
        Path to the armory workspace (for context and custom prompt).
    source_files :
        List of material file names available in the armory.
    memory_context :
        Pre-built memory context string (from MemoryStore.build_system_context).
    persona :
        The active persona.  Falls back to the default drill persona.

    Returns
    -------
    str
        The complete system prompt.

    Notes
    -----
    If the armory contains ``.hephaistos/system_prompt.md``, its contents
        replace the hardcoded core role and study loop sections.  This lets an
    armory define its own persona (quiz mode, debate mode, etc.) without
    touching Python code.
    """
    if persona is None:
        persona = _DEFAULT_PERSONA
    date = datetime.now(UTC).strftime("%Y-%m-%d")

    # 1. Persona role block (custom prompt file takes priority)
    role = persona.role_block
    study_loop = _STUDY_LOOP
    if armory_path is not None:
        custom = _load_custom_prompt(armory_path)
        if custom is not None:
            role = custom
            study_loop = ""

    tool_registry = default_registry if registry is None else registry
    tool_docs = render_tool_docs(tool_registry.schemas)

    context_parts = [f"Current date: {date}"]

    if armory_path is not None:
        context_parts.append(f"Armory workspace: {armory_path}")
        if source_files:
            file_list = "\n".join(f"  - {f}" for f in source_files[:50])
            context_parts.append(f"Available material files:\n{file_list}")
            role_summary = _material_role_summary(source_files)
            if role_summary:
                context_parts.append(role_summary)

    return SystemPrompt(
        role=role,
        study_loop=study_loop,
        anti_hallucination=_ANTI_HALLUCINATION,
        tool_docs=tool_docs,
        hephaistos_operations=_HEPHAISTOS_OPERATIONS,
        format_rules=_FORMAT_RULES,
        context="\n\n".join(context_parts),
        memory=memory_context,
    )


def build_system_prompt(
    *,
    armory_path: Path | None = None,
    source_files: list[str] | None = None,
    memory_context: str = "",
    persona: Persona | None = None,
    registry: ToolRegistry | None = None,
) -> str:
    """Build the complete system prompt."""

    return build_system_prompt_sections(
        armory_path=armory_path,
        source_files=source_files,
        memory_context=memory_context,
        persona=persona,
        registry=registry,
    ).render()
