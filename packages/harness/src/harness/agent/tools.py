"""Tool definitions, handlers, and registry for the agent harness.

Each tool has a JSON schema (for the OpenAI ``tools=`` param) and a
handler function.  Handlers receive the workspace root for path sandboxing.

**Registry protocol** - ``ToolRegistry`` is the single source of truth.
A global ``default_registry`` is pre-loaded with all built-in tools.
Armories can contribute extra tools by dropping ``*.py`` files into
``.harness/tools/`` only after the armory has been explicitly trusted.
Each plugin module must expose a top-level ``register(registry: ToolRegistry)
-> None`` function that calls ``registry.register(...)`` for every tool it
wants to add.
Tool philosophy for a document-grounded agent:
- Read/write tools are primary - the agent works with documents.
- Web fetch fills knowledge gaps, but with strict source attribution.
- The agent should NEVER guess. If information is not in the documents
  and cannot be fetched, it must say so.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Literal

from harness.agent.armory_tools import (
    run_create_armory,
    run_create_named_armory,
    run_import_materials,
    run_validate_armory,
)
from harness.agent.file_tools import (
    mutation_wrap,
    run_edit_file,
    run_list_files,
    run_read_file,
    run_search_files,
    run_write_file,
)
from harness.agent.material_tools import run_open_material, run_search_materials
from harness.agent.path_safety import safe_path
from harness.agent.shell_tools import BashResult, run_bash
from harness.agent.tool_registry import ToolRegistry
from harness.agent.tool_schema import (
    ToolHandlerResult,
    ToolParameter,
    ToolResult,
    ToolSchema,
    ToolSpec,
)
from harness.agent.web_tools import run_web_fetch
from harness.memory import MemoryEntry, MemoryStore, load_memory, save_memory

__all__ = [
    "TOOL_SCHEMAS",
    "BashResult",
    "ToolRegistry",
    "ToolResult",
    "ToolSpec",
    "default_registry",
    "get_handler",
    "run_bash",
    "run_create_armory",
    "run_create_named_armory",
    "run_edit_file",
    "run_import_materials",
    "run_list_files",
    "run_memory",
    "run_open_material",
    "run_read_file",
    "run_search_files",
    "run_search_materials",
    "run_validate_armory",
    "run_web_fetch",
    "run_write_file",
    "safe_path",
]


def _string(description: str) -> ToolParameter:
    return {"type": "string", "description": description}


def _integer(description: str) -> ToolParameter:
    return {"type": "integer", "description": description}


def _boolean(description: str) -> ToolParameter:
    return {"type": "boolean", "description": description}


def _tool(
    name: str,
    description: str,
    properties: dict[str, ToolParameter] | None = None,
    *,
    required: tuple[str, ...] = (),
) -> ToolSchema:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties if properties is not None else {},
                "required": list(required),
                "additionalProperties": False,
            },
        },
    }


_BUILTIN_SCHEMAS: list[ToolSchema] = [
    _tool(
        "compact",
        "Compress long conversation context.",
    ),
    _tool(
        "read_file",
        "Read workspace file contents.",
        {
            "path": _string("Relative path from workspace root."),
            "offset": _integer("Line number to start reading from (0-based)."),
            "limit": _integer("Maximum number of lines to read."),
        },
        required=("path",),
    ),
    _tool(
        "write_file",
        "Create or overwrite a workspace file.",
        {
            "path": _string("Relative path from workspace root."),
            "content": _string("The content to write."),
        },
        required=("path", "content"),
    ),
    _tool(
        "edit_file",
        "Replace exact text in a workspace file; supports atomic edits[].",
        {
            "path": _string("Relative path from workspace root."),
            "old_text": _string("Legacy single replacement text to find."),
            "new_text": _string("Legacy single replacement text to write."),
            "edits": {
                "type": "array",
                "description": (
                    "One or more exact replacements. Each old_text must be unique in the "
                    "original file and replacement ranges must not overlap."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "old_text": _string("Exact text to find."),
                        "new_text": _string("Replacement text."),
                    },
                    "required": ["old_text", "new_text"],
                    "additionalProperties": False,
                },
            },
        },
        required=("path",),
    ),
    _tool(
        "list_files",
        "List workspace directory contents.",
        {
            "path": _string("Relative directory path. Defaults to workspace root."),
            "pattern": _string("Glob pattern to filter files (e.g. '*.py')."),
        },
    ),
    _tool(
        "create_armory",
        "Create or repair a portable Heph armory.",
        {
            "path": _string("Relative path from workspace root for the armory folder."),
        },
        required=("path",),
    ),
    _tool(
        "validate_armory",
        "Validate an armory layout without modifying it.",
        {
            "path": _string("Relative path from workspace root for the armory folder."),
        },
        required=("path",),
    ),
    _tool(
        "create_named_armory",
        (
            "Create or repair an exact named Heph armory after an explicit user request; "
            "never fuzzy-match names."
        ),
        {
            "name": _string(
                "Exact single-folder armory name. No path separators, parent traversal, "
                "or fuzzy names."
            ),
        },
        required=("name",),
    ),
    _tool(
        "import_materials",
        (
            "Copy exact local files into armory materials; never move, delete, overwrite "
            "originals, or fuzzy-match target names."
        ),
        {
            "source_path": _string(
                "Workspace-relative file or directory path to copy. Absolute paths and ~ are "
                "rejected in agent turns."
            ),
            "target_armory": _string(
                "Optional exact armory name or explicit armory path. Defaults to current armory."
            ),
            "create_if_missing": _boolean(
                "Set true only when the user explicitly asked to create the target armory."
            ),
        },
        required=("source_path",),
    ),
    _tool(
        "search_files",
        "Search text files in the workspace.",
        {
            "pattern": _string("Literal text to search for."),
            "path": _string("Directory to search in. Defaults to workspace root."),
            "case_sensitive": {
                "type": "boolean",
                "description": "Whether the search is case-sensitive. Default: false.",
            },
        },
        required=("pattern",),
    ),
    _tool(
        "search_materials",
        "Search indexed armory materials.",
        {
            "query": _string("Natural-language topic, question, term, or formula to search for."),
            "top_k": _integer("Maximum number of excerpts to return. Default: 8."),
        },
        required=("query",),
    ),
    _tool(
        "open_material",
        "Read indexed material context around a source chunk.",
        {
            "source": _string("Indexed source path such as materials/lecture.pdf."),
            "chunk": _integer("Chunk number to center on. Defaults to the first chunk."),
            "context": _integer("Neighbor chunks to include on each side. Default: 1."),
        },
        required=("source",),
    ),
    _tool(
        "memory",
        (
            "Read or update armory memory for stable preferences, corrections, conventions, "
            "and durable facts; not temporary progress."
        ),
        {
            "action": _string("One of: read, add, replace, remove."),
            "query": _string("Optional substring filter for read."),
            "topic": _string("Short topic for add or replace."),
            "content": _string("Compact memory entry content for add or replace."),
            "old_text": _string("Short unique substring for replace or remove."),
            "source": _string("Optional source label. Defaults to conversation."),
        },
        required=("action",),
    ),
    _tool(
        "web_fetch",
        "Fetch a web page when armory material is insufficient.",
        {
            "url": _string("The URL to fetch (must start with http:// or https://)."),
        },
        required=("url",),
    ),
]


def _format_memory_entry(entry: MemoryEntry) -> str:
    source = f" ({entry.source})" if entry.source else ""
    return f"- [{entry.confidence}] {entry.topic}: {entry.content}{source}"


def _format_memory_entries(entries: Sequence[MemoryEntry]) -> str:
    if not entries:
        return "(no memory entries)"
    return "\n".join(_format_memory_entry(entry) for entry in entries)


def run_memory(
    action: str,
    *,
    workspace: Path,
    query: str = "",
    topic: str = "",
    content: str = "",
    old_text: str = "",
    source: str = "conversation",
    **_kwargs: object,
) -> ToolResult:
    memory = load_memory(workspace)
    cleaned_action = action.strip().lower()
    if cleaned_action == "read":
        return _memory_read(memory, query)
    if cleaned_action == "add":
        return _memory_add(memory, topic=topic, content=content, source=source)
    if cleaned_action == "replace":
        return _memory_replace(
            memory,
            old_text,
            topic=topic,
            content=content,
            source=source,
        )
    if cleaned_action == "remove":
        return _memory_remove(memory, old_text)
    return ToolResult(
        success=False,
        content=f"Unknown memory action: {action}. Use read, add, replace, or remove.",
        error="unknown_memory_action",
    )


def _memory_read(memory: MemoryStore, query: str) -> ToolResult:
    entries = memory.read(query)
    save_memory(memory)
    return ToolResult(
        success=True,
        content=_format_memory_entries(entries),
        metadata={"entries": len(entries), "query": query},
    )


def _memory_add(
    memory: MemoryStore,
    *,
    topic: str,
    content: str,
    source: str,
) -> ToolResult:
    entry = memory.add(topic, content, source=source or "conversation", confidence="verified")
    if entry is None:
        return ToolResult(
            success=False,
            content="Memory entry was not saved. Use a unique topic and compact safe content.",
            error="memory_add_failed",
        )
    save_memory(memory)
    return ToolResult(success=True, content=f"Saved memory: {_format_memory_entry(entry)}")


def _memory_replace(
    memory: MemoryStore,
    old_text: str,
    *,
    topic: str,
    content: str,
    source: str,
) -> ToolResult:
    result = memory.replace(
        old_text,
        topic=topic,
        content=content,
        source=source or "conversation",
        confidence="verified",
    )
    if isinstance(result, str):
        return ToolResult(success=False, content=result, error="memory_replace_failed")
    save_memory(memory)
    return ToolResult(success=True, content=f"Replaced memory: {_format_memory_entry(result)}")


def _memory_remove(memory: MemoryStore, old_text: str) -> ToolResult:
    result = memory.remove(old_text)
    if isinstance(result, str):
        return ToolResult(success=False, content=result, error="memory_remove_failed")
    save_memory(memory)
    return ToolResult(
        success=True,
        content="Removed memory entry.",
        metadata={"removed": result},
    )


def get_handler(name: str):
    return default_registry.get_handler(name)


_HANDLERS: dict[str, Callable[..., ToolHandlerResult]] = {
    "compact": lambda **_kw: "[compact triggered]",
    "bash": run_bash,
    "read_file": run_read_file,
    "write_file": lambda **kwargs: mutation_wrap(run_write_file, **kwargs),
    "edit_file": lambda **kwargs: mutation_wrap(run_edit_file, **kwargs),
    "list_files": run_list_files,
    "create_armory": run_create_armory,
    "validate_armory": run_validate_armory,
    "create_named_armory": run_create_named_armory,
    "import_materials": run_import_materials,
    "search_files": run_search_files,
    "search_materials": run_search_materials,
    "open_material": run_open_material,
    "memory": run_memory,
    "web_fetch": run_web_fetch,
}

_PROMPT_GUIDELINES: dict[str, tuple[str, ...]] = {
    "edit_file": (
        "For multiple edits in one file, use one `edit_file` call with `edits[]`; "
        "invalid blocks reject the whole call.",
    ),
}

default_registry = ToolRegistry()

for _schema in _BUILTIN_SCHEMAS:
    _name = _schema["function"]["name"]
    _handler = _HANDLERS[_name]
    _kind: Literal["normal", "control"] = "control" if _name == "compact" else "normal"
    default_registry.register(
        ToolSpec(
            schema=_schema,
            handler=_handler,
            kind=_kind,
            prompt_guidelines=_PROMPT_GUIDELINES.get(_name, ()),
        )
    )

# Backward-compatible alias: TOOL_SCHEMAS delegates to the registry.
TOOL_SCHEMAS: list[ToolSchema] = default_registry.schemas
