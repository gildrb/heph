"""Rich text builders for the TUI package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from hephaistos.chat.session import ChatSession
from hephaistos.memory.supermemory import supermemory_configured
from hephaistos.providers.endpoints import is_keyless_endpoint
from hephaistos.search_index import load_known_armories
from hephaistos.terminal import current_palette
from hephaistos.tui.dependencies import TuiDependencyError, tui_dependency_message
from hephaistos.tui.rich_transcript import evidence_summary_text
from hephaistos.tui.session_state import TuiTranscriptEntry
from hephaistos.tui.status import status_lines

try:
    from rich.text import Text as _RichText
except ImportError:
    _RichText = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from rich.text import Text


def require_rich_text() -> type[Text]:
    if _RichText is None:
        raise TuiDependencyError(tui_dependency_message())
    return _RichText  # type: ignore[return-value]


def status_text(session: ChatSession, state: str = "ready") -> Text:
    plain = status_lines(session, state)
    palette = current_palette()
    keyless = is_keyless_endpoint(session.config.base_url)
    key_ok = keyless or bool(session.config.resolved_api_key)
    if keyless:
        api = "free"
        api_style = palette.dim
    elif key_ok:
        api = "configured"
        api_style = palette.configured
    else:
        api = "missing"
        api_style = palette.error

    mem_configured = supermemory_configured()
    mem_status = "on" if mem_configured else "/memory"
    mem_style = palette.configured if mem_configured else palette.dim

    text_cls = require_rich_text()
    text = text_cls(plain, style=palette.dim)

    hep_idx = plain.index("Hephaistos")
    text.stylize(f"bold {palette.ember}", hep_idx, hep_idx + len("Hephaistos"))

    for label in ("armory", "model", "api", "memory", "materials"):
        start = plain.index(label)
        text.stylize(f"dim {palette.dim}", start, start + len(label))

    api_start = plain.index(api, plain.index("api "))
    text.stylize(api_style, api_start, api_start + len(api))

    mem_value_start = plain.index(mem_status, plain.index("memory "))
    text.stylize(mem_style, mem_value_start, mem_value_start + len(mem_status))
    return text


def armory_footer_hints_text(*, creating: bool = False, filtering: bool = False) -> Text:
    """Build footer hints for inline armory mode."""
    palette = current_palette()
    if creating:
        parts = ["armory", "enter create", "esc cancel"]
    elif filtering:
        parts = ["armory", "enter open", "esc clear", "arrows move", "n new"]
    else:
        parts = ["armory", "type filter", "enter open", "c choose", "n new", "esc close"]
    plain = "  ".join(parts)
    text = require_rich_text()(plain, style=palette.dim)
    for label in ("armory", "enter", "esc", "arrows", "type", "c", "n"):
        start = 0
        while True:
            idx = plain.find(label, start)
            if idx == -1:
                break
            style = f"bold {palette.ember}" if label == "armory" else palette.dim
            text.stylize(style, idx, idx + len(label))
            start = idx + len(label)
    return text


def footer_hints_text(session: ChatSession, *, busy: bool = False) -> Text:
    """Build contextual footer hints that change based on current state."""
    palette = current_palette()

    if busy:
        plain = "ctrl+c cancel"
        text = require_rich_text()(plain, style=palette.dim)
        start = plain.index("ctrl+c")
        text.stylize(f"dim {palette.dim}", start, start + len("ctrl+c"))
        return text

    key_ok = is_keyless_endpoint(session.config.base_url) or bool(session.config.resolved_api_key)
    parts = [
        "enter send",
        "tab complete",
        "ctrl+p commands",
        "ctrl+a armory",
        "ctrl+d exit",
    ]
    if not key_ok:
        parts.append("api missing")
    plain = "  ".join(parts)
    text = require_rich_text()(plain, style=palette.dim)
    for label in ("enter", "tab", "ctrl+p", "ctrl+a", "ctrl+c", "ctrl+d"):
        try:
            start = plain.index(label)
        except ValueError:
            continue
        text.stylize(f"dim {palette.dim}", start, start + len(label))
    try:
        start = plain.index("ctrl+p")
        text.stylize(f"bold {palette.ember}", start, start + len("ctrl+p"))
    except ValueError:
        pass
    if "api missing" in plain:
        api_start = plain.index("api missing")
        text.stylize(palette.error, api_start, api_start + len("api missing"))
    return text


def info_panel_default_text(session: ChatSession) -> Text:
    """Build the default info panel content showing armory, model, materials."""
    title = session.title or "New conversation"
    armory_name = session.armory_path.name if session.armory_path is not None else "none"
    model = session.config.model or "none"
    sources = session.source_file_count or 0
    source_str = str(sources) if sources else "none"
    evidence_str = evidence_summary_text(session.last_turn_evidence)

    lines: list[str] = [
        title,
        "\u2500" * 26,
        f"armory  {armory_name}",
        f"model   {model}",
        f"materials {source_str}",
        f"evidence {evidence_str}",
    ]
    plain = "\n".join(lines)
    text = require_rich_text()(plain, style="#808080")
    title_end = len(lines[0])
    text.stylize("bold #9B4A2E", 0, title_end)
    for label in ("armory", "model", "materials", "evidence"):
        try:
            start = plain.index(label)
            text.stylize("dim #808080", start, start + len(label))
        except ValueError:
            pass
    return text


def armory_home_text() -> str:
    """Return the no-armory home card shown on first TUI launch."""
    recent = load_known_armories()[:5]
    lines = [
        "No armory attached.",
        "",
        "Press ctrl+a to open or create an armory.",
        "Put study files in materials/.",
        "Hephaistos handles indexing, retrieval, memory, chats, traces, and usage.",
    ]
    if recent:
        lines.extend(["", "Recent armories:"])
        lines.extend(f"  {path.name}  {path}" for path in recent)
    return "\n".join(lines)


def info_panel_message_text(entry: TuiTranscriptEntry, session: ChatSession) -> Text:
    """Build info panel content for a focused transcript message."""
    is_user = entry.content.startswith("[bold #E0E0E0]You:")
    is_assistant = entry.kind == "markdown" and "Hephaistos:" in entry.content

    if is_user:
        content = entry.content.replace("[bold #E0E0E0]You:[/bold #E0E0E0] ", "")
        preview = content[:120] + ("..." if len(content) > 120 else "")
        sep = "\u2500" * 26
        plain = f"You message\n{sep}\n{preview}"
    elif is_assistant:
        model = session.config.model or "unknown"
        evidence_str = evidence_summary_text(session.last_turn_evidence)
        usage = session.usage.summary()
        sep = "\u2500" * 26
        plain = (
            f"Assistant reply\n{sep}"
            f"\nmodel   {model}"
            f"\ntokens  {usage['total_tokens']}"
            f"\ncost    ${usage['cost_usd']:.4f}"
            f"\nevidence {evidence_str}"
        )
    else:
        sep = "\u2500" * 26
        plain = f"Message\n{sep}\n{entry.kind}"

    text = require_rich_text()(plain, style="#808080")
    first_newline = plain.index("\n") if "\n" in plain else len(plain)
    text.stylize("bold #9B4A2E", 0, first_newline)
    for label in ("model", "tokens", "cost", "evidence"):
        try:
            start = plain.index(label)
            text.stylize("dim #808080", start, start + len(label))
        except ValueError:
            pass
    return text
