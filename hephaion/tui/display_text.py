from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from hephaion.armory.search import load_known_armories
from hephaion.materials import material_display_name
from hephaion.runtime import has_configured_access
from hephaion.terminal import current_palette
from hephaion.tui.dependencies import TuiDependencyError, tui_dependency_message
from hephaion.tui.keymap import armory_shortcut_key
from hephaion.tui.rich_transcript import evidence_summary_text
from hephaion.tui.session_state import TuiTranscriptEntry
from hephaion.tui.status import STATUS_FIELD_GAP, status_lines

try:
    from rich.text import Text as _RichText
except ImportError:
    _RichText = None  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from rich.text import Text

    from hephaion.chat.session import ChatSession

_INFO_PANEL_MATERIAL_NAME_WIDTH = 31
_INFO_PANEL_VISIBLE_WIDTH = 36
_RECENT_ARMORY_NAME_WIDTH = 16
_RECENT_ARMORY_PATH_WIDTH = 20
COMPOSER_PLACEHOLDER = "Ask a cited question about your materials..."


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
    _stylize_status_labels(text, plain)
    _stylize_status_values(text, plain)
    return text


def _stylize_status_labels(text: Text, plain: str) -> None:
    palette = current_palette()
    for label in ("armory", "model", "reasoning"):
        start = 0 if plain.startswith(f"{label} ") else plain.index(f" {label} ") + 1
        text.stylize(palette.text_secondary, start, start + len(label))


def _stylize_status_values(text: Text, plain: str) -> None:
    palette = current_palette()
    for label in ("armory", "model", "reasoning"):
        value_start = plain.index(f"{label} ") + len(label) + 1
        value_end = _status_value_end(plain, label, value_start)
        text.stylize(palette.text_muted, value_start, value_end)


def _status_value_end(plain: str, label: str, value_start: int) -> int:
    if label == "armory":
        return plain.index(f"{STATUS_FIELD_GAP}model ", value_start)
    if label == "model":
        return plain.index(f"{STATUS_FIELD_GAP}reasoning ", value_start)
    return len(plain)


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
    return _shortcut_hints_text(
        parts,
        ("armory", "enter", "esc", "arrows", "type", "n"),
        footer_style=footer_style,
        shortcut_style=shortcut_style,
        every_match=True,
    )


def footer_hints_text(
    session: ChatSession,
    *,
    busy: bool = False,
) -> Text:
    palette = current_palette()
    footer_style = palette.text_muted
    shortcut_style = palette.text_secondary

    if busy:
        return _shortcut_hints_text(
            ("esc stop", "ctrl+c exit"),
            ("esc", "ctrl+c"),
            footer_style=footer_style,
            shortcut_style=shortcut_style,
        )

    key_ok = has_configured_access(session.config, refresh_oauth=False)
    shortcut = armory_shortcut_key()
    parts = [
        f"{shortcut} armory",
        "ctrl+p commands",
        "shift+tab reasoning",
    ]
    if not key_ok:
        parts.append("api missing")
    text = _shortcut_hints_text(
        parts,
        (shortcut, "ctrl+p", "shift+tab"),
        footer_style=footer_style,
        shortcut_style=shortcut_style,
    )
    plain = text.plain
    if "api missing" in plain:
        api_start = plain.index("api missing")
        text.stylize(palette.status_error_text, api_start, api_start + len("api missing"))
    return text


def _shortcut_hints_text(
    parts: Sequence[str],
    labels: Sequence[str],
    *,
    footer_style: str,
    shortcut_style: str,
    every_match: bool = False,
) -> Text:
    plain = STATUS_FIELD_GAP.join(parts)
    text = require_rich_text()(plain, style=footer_style)
    for label in labels:
        if every_match:
            _stylize_all(text, plain, label, shortcut_style)
        else:
            _stylize_first(text, plain, label, shortcut_style)
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


def _active_material_count(session: ChatSession) -> int:
    return sum(1 for file in session.source_files if file not in session.disabled_source_files)


def _info_panel_material_lines(session: ChatSession) -> list[str]:
    visible_materials = list(session.source_files[:8])
    active_count = _active_material_count(session)
    material_lines = [
        "scope",
        f"  {active_count}/{len(session.source_files)} materials active",
    ]
    if not visible_materials:
        material_lines.append("  no materials attached")
        return material_lines

    material_lines.extend(f"  @{_material_panel_display_name(name)}" for name in visible_materials)
    if len(session.source_files) > len(visible_materials):
        material_lines.append(f"  +{len(session.source_files) - len(visible_materials)} more")
    return material_lines


def _info_panel_evidence_lines(
    session: ChatSession,
    *,
    busy: bool,
    progress: str,
) -> list[str]:
    if busy:
        detail = progress or "working"
        return ["grounding", f"  {detail}"]
    evidence = session.last_turn_evidence
    if evidence is None or not evidence.items:
        return ["grounding", "  no evidence used yet"]
    return ["grounding", f"  {evidence_summary_text(evidence)}", "  f8 or /evidence details"]


def _info_panel_lines(
    session: ChatSession,
    session_seconds: int,
    *,
    busy: bool,
    progress: str,
) -> list[str]:
    return [
        session.title or "Grounding",
        f"time {_session_duration(session_seconds)}",
        "",
        *_info_panel_material_lines(session),
        "",
        *_info_panel_evidence_lines(session, busy=busy, progress=progress),
    ]


def _ellipsize_end(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    if max_length <= 3:
        return "." * max_length
    return f"{text[: max_length - 3].rstrip()}..."


def _indented_info_panel_line(line: str) -> str:
    if not line:
        return ""
    return _ellipsize_end(f"  {line}", _INFO_PANEL_VISIBLE_WIDTH)


def _indented_panel_text(lines: Sequence[str]) -> str:
    return "\n".join(_indented_info_panel_line(line) for line in lines)


def _stylize_all(text: Text, plain: str, label: str, style: str) -> None:
    start = 0
    while True:
        idx = plain.find(label, start)
        if idx == -1:
            return
        text.stylize(style, idx, idx + len(label))
        start = idx + len(label)


def _stylize_first(text: Text, plain: str, label: str, style: str) -> None:
    idx = plain.find(label)
    if idx != -1:
        text.stylize(style, idx, idx + len(label))


def _stylize_info_panel_labels(text: Text, plain: str) -> None:
    palette = current_palette()
    for label in ("time", "scope", "grounding"):
        _stylize_all(text, plain, label, palette.text_secondary)


def _stylize_info_panel_materials(text: Text, plain: str, session: ChatSession) -> None:
    palette = current_palette()
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
            else palette.status_success_text
        )
        text.stylize(style, idx, idx + len(token))


def _stylize_hidden_material_count(text: Text, plain: str, session: ChatSession) -> None:
    hidden_material_count = max(0, len(session.source_files) - 8)
    if not hidden_material_count:
        return
    palette = current_palette()
    detail = f"+{hidden_material_count} more"
    detail_start = plain.index(detail)
    text.stylize(palette.text_muted, detail_start, detail_start + len(detail))


def info_panel_default_text(
    session: ChatSession,
    *,
    session_seconds: int = 0,
    busy: bool = False,
    progress: str = "",
) -> Text:
    palette = current_palette()
    plain = _indented_panel_text(
        _info_panel_lines(session, session_seconds, busy=busy, progress=progress)
    )
    text = require_rich_text()(plain, style=palette.text_muted)
    display_title = plain.splitlines()[0].strip()
    title_start = plain.index(display_title)
    text.stylize(
        f"bold {palette.text_primary}",
        title_start,
        title_start + len(display_title),
    )
    _stylize_info_panel_labels(text, plain)
    duration = _session_duration(session_seconds)
    duration_start = plain.index(duration, plain.index("time "))
    text.stylize(palette.text_muted, duration_start, duration_start + len(duration))
    _stylize_hidden_material_count(text, plain, session)
    _stylize_info_panel_materials(text, plain, session)
    return text


def startup_card_text() -> str:
    return "\n".join(
        [
            "  Tips",
            "    Add files to materials/.",
            "    Use @file for focus.",
            "    Ask for summaries or gaps.",
            "    /priority finds next steps.",
            "    /evidence shows sources.",
            "",
            "  Warnings",
            "    Verify important claims.",
        ]
    )


def new_chat_card_text() -> str:
    return "Tip: use @file for focused document analysis; inspect citations with /evidence."


def _ellipsize_middle(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    if max_length <= 3:
        return "." * max_length
    head_length = max(1, (max_length - 3) // 2)
    tail_length = max_length - 3 - head_length
    return f"{text[:head_length]}...{text[-tail_length:]}"


def _compact_armory_path(path: Path) -> str:
    resolved = path.expanduser()
    try:
        display = f"~/{resolved.relative_to(Path.home())}"
    except ValueError:
        display = str(path)
    return _ellipsize_middle(display, _RECENT_ARMORY_PATH_WIDTH)


def _recent_armory_line(path: Path) -> str:
    name = _ellipsize_middle(path.name, _RECENT_ARMORY_NAME_WIDTH)
    return f"  {name:<{_RECENT_ARMORY_NAME_WIDTH}}  {_compact_armory_path(path)}"


def armory_home_text() -> str:
    recent = load_known_armories()[:5]
    if recent:
        lines = [
            "No armory attached.",
            "",
            "Existing armories found.",
            f"Press {armory_shortcut_key()} to open/create.",
            "Saved in ~/.armories/.",
            "Add docs to materials/.",
        ]
        lines.extend(["", "Recent armories:"])
        lines.extend(_recent_armory_line(path) for path in recent)
        return "\n".join(lines)
    lines = [
        "No armory attached.",
        "",
        "What document set are you working on?",
        f"Press {armory_shortcut_key()} to open/create.",
        "Saved in ~/.armories/.",
        "Add docs to materials/.",
    ]
    return "\n".join(lines)


def info_panel_message_text(entry: TuiTranscriptEntry, session: ChatSession) -> Text:
    palette = current_palette()
    lines = [_indented_info_panel_line(line) for line in _info_panel_message_lines(entry, session)]
    plain = "\n".join(lines)
    text = require_rich_text()(plain, style=palette.text_muted)
    _stylize_message_panel_title(text, plain, lines[0].strip())
    _stylize_message_panel_labels(text, plain)
    return text


def _info_panel_message_lines(entry: TuiTranscriptEntry, session: ChatSession) -> list[str]:
    sep = "\u2500" * 26

    if entry.kind == "user":
        return _user_message_panel_lines(entry.content, sep)
    if entry.kind == "markdown":
        return _assistant_message_panel_lines(entry, session, sep)
    return ["Message", sep, entry.kind]


def _user_message_panel_lines(content: str, sep: str) -> list[str]:
    preview = content[:120] + ("..." if len(content) > 120 else "")
    return ["You message", sep, preview]


def _assistant_message_panel_lines(
    entry: TuiTranscriptEntry,
    session: ChatSession,
    sep: str,
) -> list[str]:
    model = session.config.model or "unknown"
    evidence_str = evidence_summary_text(entry.evidence or session.last_turn_evidence)
    usage = session.usage.summary()
    return [
        "Assistant reply",
        sep,
        f"model   {model}",
        f"tokens  {usage['total_tokens']}",
        f"cost    ${usage['cost_usd']:.4f}",
        f"evidence {evidence_str}",
        "details f8 or /evidence",
    ]


def _stylize_message_panel_title(text: Text, plain: str, title: str) -> None:
    palette = current_palette()
    title_start = plain.index(title)
    text.stylize(f"bold {palette.text_primary}", title_start, title_start + len(title))


def _stylize_message_panel_labels(text: Text, plain: str) -> None:
    palette = current_palette()
    for label in ("model", "tokens", "cost", "evidence", "details"):
        _stylize_first(text, plain, label, f"dim {palette.text_muted}")
