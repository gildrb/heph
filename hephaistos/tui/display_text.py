"""Rich text builders for the TUI package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from hephaistos.armory.search import load_known_armories
from hephaistos.memory.supermemory import supermemory_configured
from hephaistos.providers.endpoints import is_keyless_endpoint
from hephaistos.terminal import current_palette
from hephaistos.tui.dependencies import TuiDependencyError, tui_dependency_message
from hephaistos.tui.keymap import armory_shortcut_key
from hephaistos.tui.materials_view import MATERIAL_DISABLED_COLOR, MATERIAL_ENABLED_COLOR
from hephaistos.tui.rich_transcript import evidence_summary_text
from hephaistos.tui.session_state import TuiTranscriptEntry
from hephaistos.tui.status import status_lines

try:
    from rich.text import Text as _RichText
except ImportError:
    _RichText = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from rich.text import Text

    from hephaistos.chat.session import ChatSession


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
    shortcut = armory_shortcut_key()
    parts = [
        "enter send",
        "tab complete",
        "ctrl+p commands",
        f"{shortcut} armory",
        "ctrl+d exit",
    ]
    if not key_ok:
        parts.append("api missing")
    plain = "  ".join(parts)
    text = require_rich_text()(plain, style=palette.dim)
    for label in ("enter", "tab", "ctrl+p", shortcut, "ctrl+c", "ctrl+d"):
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


def _session_duration(seconds: int) -> str:
    hours, remainder = divmod(max(0, seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def _material_panel_lines(session: ChatSession) -> list[str]:
    files = list(session.source_files)
    if not files:
        return ["materials", "  none"]

    lines = ["materials"]
    visible = files[:8]
    for name in visible:
        display_name = name.removeprefix("materials/")
        lines.append(f"  @{display_name}")
    if len(files) > len(visible):
        lines.append(f"  +{len(files) - len(visible)} more")
    return lines


def info_panel_default_text(session: ChatSession, *, session_seconds: int = 0) -> Text:
    """Build the default info panel content showing session length and material names."""
    title = session.title or "Study session"

    lines: list[str] = [
        title,
        "\u2500" * 40,
        f"time {_session_duration(session_seconds)}",
        "",
        *_material_panel_lines(session),
    ]
    plain = "\n".join(lines)
    text = require_rich_text()(plain, style="#808080")
    title_end = len(lines[0])
    text.stylize("bold #9B4A2E", 0, title_end)
    for label in ("time", "materials"):
        start = 0
        while True:
            idx = plain.find(label, start)
            if idx == -1:
                break
            text.stylize("dim #808080", idx, idx + len(label))
            start = idx + len(label)
    for name in session.source_files:
        display_name = name.removeprefix("materials/")
        token = f"@{display_name}"
        idx = plain.find(token)
        if idx == -1:
            continue
        style = (
            MATERIAL_DISABLED_COLOR
            if name in session.disabled_source_files
            else MATERIAL_ENABLED_COLOR
        )
        text.stylize(style, idx, idx + len(token))
    return text


def armory_home_text() -> str:
    """Return the no-armory home card shown on first TUI launch."""
    recent = load_known_armories()[:5]
    if recent:
        lines = [
            "No armory attached.",
            "",
            "Existing armories found.",
            f"Press {armory_shortcut_key()} to choose an armory or create a new one.",
            "Armories are saved locally in ~/.armories/",
            "Add your study materials (PDFs, notes, textbooks) to ~/.armories/<module>/materials/",
        ]
        lines.extend(["", "Recent armories:"])
        lines.extend(f"  {path.name}  {path}" for path in recent)
        return "\n".join(lines)
    lines = [
        "No armory attached.",
        "",
        "What module or topic are you studying for?",
        f"Press {armory_shortcut_key()} to create or open an armory.",
        "Armories are saved locally in ~/.armories/",
        "Add your study materials (PDFs, notes, textbooks) to ~/.armories/<module>/materials/",
    ]
    return "\n".join(lines)


def info_panel_message_text(entry: TuiTranscriptEntry, session: ChatSession) -> Text:
    """Build info panel content for a focused transcript message."""
    is_user = entry.kind == "user"
    is_assistant = entry.kind == "markdown"

    if is_user:
        content = entry.content
        preview = content[:120] + ("..." if len(content) > 120 else "")
        sep = "\u2500" * 26
        plain = f"You message\n{sep}\n{preview}"
    elif is_assistant:
        model = session.config.model or "unknown"
        evidence_str = evidence_summary_text(entry.evidence or session.last_turn_evidence)
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
