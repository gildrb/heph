from __future__ import annotations

from typing import TYPE_CHECKING

from hephaistos.armory.search import load_known_armories
from hephaistos.materials import material_display_name
from hephaistos.runtime import has_configured_access
from hephaistos.terminal import current_palette
from hephaistos.tui.dependencies import TuiDependencyError, tui_dependency_message
from hephaistos.tui.keymap import armory_shortcut_key
from hephaistos.tui.rich_transcript import evidence_summary_text
from hephaistos.tui.session_state import TuiTranscriptEntry
from hephaistos.tui.status import status_lines

try:
    from rich.text import Text as _RichText
except ImportError:
    _RichText = None  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from rich.text import Text

    from hephaistos.chat.session import ChatSession

_INFO_PANEL_MATERIAL_NAME_WIDTH = 39


def require_rich_text() -> type[Text]:
    if _RichText is None:
        raise TuiDependencyError(tui_dependency_message())
    return _RichText


def status_text(session: ChatSession) -> Text:
    plain = status_lines(session)
    palette = current_palette()

    text_cls = require_rich_text()
    text = text_cls(plain, style=palette.text_muted)
    text.stylize(f"bold {palette.brand_primary}", 0, len("Heph"))

    for label in ("armory", "model", "mode"):
        start = 0 if plain.startswith(f"{label} ") else plain.index(f" {label} ") + 1
        text.stylize(palette.text_secondary, start, start + len(label))

    for label in ("armory", "model"):
        value_start = plain.index(f"{label} ") + len(label) + 1
        next_label = " model " if label == "armory" else " mode "
        value_end = plain.index(next_label, value_start)
        text.stylize(palette.text_muted, value_start, value_end)

    mode = session.study_state.autonomy_mode.value
    mode_start = plain.index(mode, plain.index("mode "))
    mode_style = palette.text_muted
    if mode == "guided":
        mode_style = palette.text_primary
    elif mode != "manual":
        mode_style = f"bold {palette.status_error_text}"
    text.stylize(mode_style, mode_start, mode_start + len(mode))

    return text


def armory_footer_hints_text(*, creating: bool = False, filtering: bool = False) -> Text:
    palette = current_palette()
    footer_style = palette.text_muted
    shortcut_style = palette.text_secondary
    if creating:
        parts = ["armory", "enter create", "esc cancel"]
    elif filtering:
        parts = ["armory", "enter open", "esc clear", "arrows move", "n new"]
    else:
        parts = ["armory", "type filter", "enter open", "n new", "esc close"]
    plain = "  ".join(parts)
    text = require_rich_text()(plain, style=footer_style)
    for label in ("armory", "enter", "esc", "arrows", "type", "n"):
        start = 0
        while True:
            idx = plain.find(label, start)
            if idx == -1:
                break
            text.stylize(shortcut_style, idx, idx + len(label))
            start = idx + len(label)
    return text


def footer_hints_text(
    session: ChatSession,
    *,
    busy: bool = False,
) -> Text:
    palette = current_palette()
    footer_style = palette.text_muted
    shortcut_style = palette.text_secondary

    if busy:
        plain = "esc stop  ctrl+c exit"
        text = require_rich_text()(plain, style=footer_style)
        for label in ("esc", "ctrl+c"):
            start = plain.index(label)
            text.stylize(shortcut_style, start, start + len(label))
        return text

    key_ok = has_configured_access(session.config, refresh_oauth=False)
    shortcut = armory_shortcut_key()
    parts = [
        "enter send",
        "tab complete",
        "ctrl+p commands",
        f"{shortcut} armory",
        "ctrl+c exit",
        "ctrl+d exit",
    ]
    if not key_ok:
        parts.append("api missing")
    plain = "  ".join(parts)
    text = require_rich_text()(plain, style=footer_style)
    for label in ("enter", "tab", "ctrl+p", shortcut, "ctrl+c", "ctrl+d"):
        try:
            start = plain.index(label)
        except ValueError:
            continue
        text.stylize(shortcut_style, start, start + len(label))
    if "api missing" in plain:
        api_start = plain.index("api missing")
        text.stylize(palette.status_error_text, api_start, api_start + len("api missing"))
    return text


def _session_duration(seconds: int) -> str:
    hours, remainder = divmod(max(0, seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def _material_panel_display_name(name: str) -> str:
    display_name = material_display_name(name)
    if len(display_name) <= _INFO_PANEL_MATERIAL_NAME_WIDTH:
        return display_name
    return f"{display_name[: _INFO_PANEL_MATERIAL_NAME_WIDTH - 3]}..."


def info_panel_default_text(session: ChatSession, *, session_seconds: int = 0) -> Text:
    palette = current_palette()
    title = session.title or "Session"
    visible_materials = list(session.source_files[:8])
    material_lines = ["materials"]
    if visible_materials:
        material_lines.extend(
            f"  @{_material_panel_display_name(name)}" for name in visible_materials
        )
        if len(session.source_files) > len(visible_materials):
            material_lines.append(f"  +{len(session.source_files) - len(visible_materials)} more")
    else:
        material_lines.append("  none")

    lines: list[str] = [
        title,
        f"time {_session_duration(session_seconds)}",
        "",
        *material_lines,
        "",
        "next",
        "  /exam active recall",
        "  /priority plan focus",
        "  /remind due review",
    ]
    lines = [f"  {line}" if line else "" for line in lines]
    plain = "\n".join(lines)
    text = require_rich_text()(plain, style=palette.text_muted)
    title_start = plain.index(title)
    text.stylize(f"bold {palette.text_primary}", title_start, title_start + len(title))
    for label in ("time", "materials", "next"):
        start = 0
        while True:
            idx = plain.find(label, start)
            if idx == -1:
                break
            text.stylize(palette.text_secondary, idx, idx + len(label))
            start = idx + len(label)
    duration = _session_duration(session_seconds)
    duration_start = plain.index(duration, plain.index("time "))
    text.stylize(palette.text_muted, duration_start, duration_start + len(duration))
    hidden_material_count = max(0, len(session.source_files) - 8)
    if hidden_material_count:
        detail = f"+{hidden_material_count} more"
        detail_start = plain.index(detail)
        text.stylize(palette.text_muted, detail_start, detail_start + len(detail))
    search_from = 0
    for name in session.source_files:
        display_name = _material_panel_display_name(name)
        token = f"@{display_name}"
        idx = plain.find(token, search_from)
        if idx == -1:
            continue
        search_from = idx + len(token)
        style = (
            palette.status_error_text
            if name in session.disabled_source_files
            else palette.action_primary_bg
        )
        text.stylize(style, idx, idx + len(token))
    return text


def startup_card_text() -> str:
    return "\n".join(
        [
            "Tips",
            "  Put PDFs, notes, drafts, and references in the armory materials/ folder.",
            "  Mention @file names to narrow the context for analysis or editing.",
            "  Ask for summaries, contradictions, gaps, timelines, and action items.",
            "  Use /priority to map what needs attention across the document set.",
            "  Use /evidence after an answer to inspect retrieved source snippets.",
            "",
            "Warnings",
            "  Answers are only as good as the indexed documents and citations.",
            "  Verify important claims before relying on them in serious work.",
        ]
    )


def new_chat_card_text() -> str:
    return "Tip: use @file for focused document analysis; inspect citations with /evidence."


def armory_home_text() -> str:
    recent = load_known_armories()[:5]
    if recent:
        lines = [
            "No armory attached.",
            "",
            "Existing armories found.",
            f"Press {armory_shortcut_key()} to choose an armory or create a new one.",
            "Armories are saved locally in ~/.armories/",
            "Add documents (PDFs, notes, drafts, references) to ~/.armories/<module>/materials/",
        ]
        lines.extend(["", "Recent armories:"])
        lines.extend(f"  {path.name}  {path}" for path in recent)
        return "\n".join(lines)
    lines = [
        "No armory attached.",
        "",
        "What document set are you working on?",
        f"Press {armory_shortcut_key()} to create or open an armory.",
        "Armories are saved locally in ~/.armories/",
        "Add documents (PDFs, notes, drafts, references) to ~/.armories/<module>/materials/",
    ]
    return "\n".join(lines)


def info_panel_message_text(entry: TuiTranscriptEntry, session: ChatSession) -> Text:
    palette = current_palette()
    is_user = entry.kind == "user"
    is_assistant = entry.kind == "markdown"
    sep = "\u2500" * 26

    if is_user:
        content = entry.content
        preview = content[:120] + ("..." if len(content) > 120 else "")
        lines = ["You message", sep, preview]
    elif is_assistant:
        model = session.config.model or "unknown"
        evidence_str = evidence_summary_text(entry.evidence or session.last_turn_evidence)
        usage = session.usage.summary()
        lines = [
            "Assistant reply",
            sep,
            f"model   {model}",
            f"tokens  {usage['total_tokens']}",
            f"cost    ${usage['cost_usd']:.4f}",
            f"evidence {evidence_str}",
        ]
    else:
        lines = ["Message", sep, entry.kind]

    lines = [f"  {line}" if line else "" for line in lines]
    plain = "\n".join(lines)
    text = require_rich_text()(plain, style=palette.text_muted)
    first_line = lines[0].strip()
    title_start = plain.index(first_line)
    text.stylize(f"bold {palette.text_primary}", title_start, title_start + len(first_line))
    for label in ("model", "tokens", "cost", "evidence"):
        try:
            start = plain.index(label)
            text.stylize(f"dim {palette.text_muted}", start, start + len(label))
        except ValueError:
            pass
    return text
