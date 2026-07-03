from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.runtime import has_configured_access
from harness.materials import material_display_name

from interfaces.terminal import current_palette
from interfaces.tui.dependencies import TuiDependencyError, tui_dependency_message
from interfaces.tui.keybinds import footer_keybind_hints
from interfaces.tui.keymap import RuntimeKeymap, armory_shortcut_key, default_runtime_keymap
from interfaces.tui.rich_transcript import evidence_summary_text
from interfaces.tui.session_state import TuiTranscriptEntry
from interfaces.tui.shortcut_hints import ShortcutHint, shortcut_hint_part
from interfaces.tui.status import STATUS_FIELD_GAP, status_labels, status_lines

try:
    from rich.text import Text as _RichText
except ImportError:
    _RichText = None  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from harness.chat.session import ChatSession
    from harness.rag.context import TurnEvidence
    from rich.text import Text

_INFO_PANEL_MATERIAL_NAME_WIDTH = 35
_INFO_PANEL_VISIBLE_WIDTH = 38
_INFO_PANEL_SCOPE = "scope"
_INFO_PANEL_EVIDENCE = "evidence"
_INFO_PANEL_FILES = "files"
COMPOSER_PLACEHOLDER = "Ask a cited question about your materials..."


@dataclass(frozen=True)
class _InfoPanelLine:
    content: str
    is_heading: bool = False
    label: str = ""


def require_rich_text() -> type[Text]:
    if _RichText is None:
        raise TuiDependencyError(tui_dependency_message())
    return _RichText


def label_value_line(label: str, value: object) -> str:
    label_text = label.strip().upper()
    value_text = str(value).strip()
    if not value_text:
        return label_text
    return f"{label_text} {value_text}"


def menu_label_value(label: str, value: object) -> str:
    label_text = label.strip().upper()
    value_text = menu_value_text(value)
    if not value_text:
        return label_text
    return f"{label_text} {value_text}"


def menu_value_text(value: object) -> str:
    return str(value).strip().casefold()


def status_text(
    session: ChatSession,
    *,
    draft: str = "",
    title: str = "Heph",
    width: int | None = None,
) -> Text:
    display_title = title.strip() or "Heph"
    plain = status_lines(session, draft=draft, title=display_title, width=width)
    palette = current_palette()

    text_cls = require_rich_text()
    text = text_cls(plain, style=palette.text_muted)
    text.stylize(f"bold {palette.brand_primary}", 0, len(display_title))
    labels = _rendered_status_labels(plain, status_labels(session))
    _stylize_status_labels(text, plain, labels)
    _stylize_status_values(text, plain, labels)
    return text


def status_render_width(widget_width: int) -> int | None:
    # The status widget is auto-width. Its measured width can briefly reflect a
    # previous, shorter render, so using it as a fitting constraint makes stable
    # identity fields such as ARMORY flicker or truncate while typing.
    del widget_width
    return None


def _rendered_status_labels(plain: str, labels: Sequence[str]) -> tuple[str, ...]:
    label_set = frozenset(labels)
    rendered: list[str] = []
    for field in plain.split(STATUS_FIELD_GAP)[1:]:
        label = field.partition(" ")[0]
        if label in label_set:
            rendered.append(label)
    return tuple(rendered)


def _stylize_status_labels(text: Text, plain: str, labels: Sequence[str]) -> None:
    palette = current_palette()
    for label in labels:
        start = _status_label_start(plain, label)
        if start is None:
            continue
        text.stylize(palette.text_secondary, start, start + len(label))


def _stylize_status_values(text: Text, plain: str, labels: Sequence[str]) -> None:
    palette = current_palette()
    for index, label in enumerate(labels):
        label_start = _status_label_start(plain, label)
        if label_start is None:
            continue
        value_start = label_start + len(label) + 1
        value_end = _status_value_end(plain, labels, index, value_start)
        text.stylize(palette.text_muted, value_start, value_end)


def _status_label_start(plain: str, label: str) -> int | None:
    if plain.startswith(f"{label} "):
        return 0
    marker = f"{STATUS_FIELD_GAP}{label} "
    start = plain.find(marker)
    if start < 0:
        return None
    return start + len(STATUS_FIELD_GAP)


def _status_value_end(
    plain: str,
    labels: Sequence[str],
    index: int,
    value_start: int,
) -> int:
    if index + 1 < len(labels):
        return plain.index(f"{STATUS_FIELD_GAP}{labels[index + 1]} ", value_start)
    return len(plain)


def armory_footer_hints_text(*, creating: bool = False, filtering: bool = False) -> Text:
    palette = current_palette()
    footer_style = palette.text_muted
    shortcut_style = palette.text_secondary
    if creating:
        hints = (
            ShortcutHint("Create", "enter"),
            ShortcutHint("Cancel", "esc"),
        )
    elif filtering:
        hints = (
            ShortcutHint("Open", "enter"),
            ShortcutHint("Clear", "esc"),
            ShortcutHint("Move", "arrows"),
        )
    else:
        hints = (
            ShortcutHint("Open", "enter"),
            ShortcutHint("Close", "esc"),
        )
    return _shortcut_hints_text(
        hints,
        footer_style=footer_style,
        shortcut_style=shortcut_style,
    )


def footer_hints_text(
    session: ChatSession,
    *,
    busy: bool = False,
    keymap: RuntimeKeymap | None = None,
) -> Text:
    palette = current_palette()
    footer_style = palette.text_muted
    shortcut_style = palette.text_secondary

    if busy:
        stop_key = keymap.primary_key("cancel_turn") if keymap is not None else "esc"
        return _shortcut_hints_text(
            (
                ShortcutHint("Stop", stop_key),
                ShortcutHint("Exit", "ctrl+c"),
            ),
            footer_style=footer_style,
            shortcut_style=shortcut_style,
        )

    key_ok = has_configured_access(session.config, refresh_oauth=False)
    hints = tuple(ShortcutHint(hint.label, hint.key) for hint in footer_keybind_hints(keymap))
    text = _shortcut_hints_text(
        hints,
        extra_parts=("api missing",) if not key_ok else (),
        footer_style=footer_style,
        shortcut_style=shortcut_style,
    )
    plain = text.plain
    if "api missing" in plain:
        api_start = plain.index("api missing")
        text.stylize(palette.status_error_text, api_start, api_start + len("api missing"))
    return text


def _shortcut_hints_text(
    hints: Sequence[ShortcutHint],
    *,
    footer_style: str,
    shortcut_style: str,
    section: str = "",
    extra_parts: Sequence[str] = (),
) -> Text:
    labels: list[str] = []
    parts: list[str] = []
    if section:
        section_label = section.strip().upper()
        labels.append(section_label)
        parts.append(section_label)
    for hint in hints:
        labels.append(hint.label.strip().upper())
        parts.append(shortcut_hint_part(hint))
    parts.extend(extra_parts)
    plain = STATUS_FIELD_GAP.join(parts)
    text = require_rich_text()(plain, style=footer_style)
    for label in labels:
        _stylize_first(text, plain, label, shortcut_style)
    return text


def _material_panel_display_name(name: str) -> str:
    display_name = material_display_name(name)
    if len(display_name) <= _INFO_PANEL_MATERIAL_NAME_WIDTH:
        return display_name
    return f"{display_name[: _INFO_PANEL_MATERIAL_NAME_WIDTH - 3]}..."


def _active_material_count(session: ChatSession) -> int:
    return sum(1 for file in session.source_files if file not in session.disabled_source_files)


def _count_label(count: int, singular: str, plural: str | None = None) -> str:
    word = singular if count == 1 else (plural or f"{singular}s")
    return f"{count} {word}"


def _info_panel_label_line(label: str, value: str) -> _InfoPanelLine:
    label_text = label.strip().upper()
    return _InfoPanelLine(label_value_line(label_text, value), label=label_text)


def _info_panel_more_line(count: int) -> _InfoPanelLine:
    return _info_panel_label_line("more", f"+{count}")


def _info_panel_material_lines(
    session: ChatSession,
    *,
    show_items: bool = True,
) -> list[_InfoPanelLine]:
    visible_materials = list(session.source_files[:8])
    active_count = _active_material_count(session)
    material_lines = [
        _info_panel_label_line(
            _INFO_PANEL_EVIDENCE.upper(),
            _evidence_shortcut_key(),
        ),
        _InfoPanelLine(""),
        _info_panel_label_line(
            _INFO_PANEL_SCOPE.upper(),
            f"{active_count}/{len(session.source_files)}",
        ),
        _InfoPanelLine(""),
        _info_panel_label_line(_INFO_PANEL_FILES.upper(), str(len(session.source_files))),
    ]
    if not visible_materials:
        material_lines.append(_info_panel_label_line("state", "no materials"))
        return material_lines
    if not show_items:
        return material_lines

    material_lines.extend(
        _InfoPanelLine(f"@{_material_panel_display_name(name)}") for name in visible_materials
    )
    if len(session.source_files) > len(visible_materials):
        hidden_count = len(session.source_files) - len(visible_materials)
        material_lines.append(_info_panel_more_line(hidden_count))
    return material_lines


def _info_panel_evidence_lines(
    session: ChatSession,
    *,
    busy: bool,
    progress: str,
) -> list[_InfoPanelLine]:
    if busy:
        detail = progress or "working"
        return [
            _info_panel_label_line(_INFO_PANEL_EVIDENCE.upper(), detail),
        ]
    evidence = session.last_turn_evidence
    if evidence is None or not evidence.items:
        return [
            _info_panel_label_line(_INFO_PANEL_EVIDENCE.upper(), "none yet"),
        ]
    return _info_panel_evidence_used_lines(session, evidence)


def _info_panel_evidence_used_lines(
    session: ChatSession,
    evidence: TurnEvidence,
) -> list[_InfoPanelLine]:
    lines = [
        _info_panel_label_line(
            _INFO_PANEL_EVIDENCE.upper(),
            _evidence_shortcut_key(),
        ),
        _InfoPanelLine(""),
        _info_panel_label_line(
            _INFO_PANEL_SCOPE.upper(),
            _info_panel_evidence_scope(session, evidence),
        ),
        _InfoPanelLine(""),
        _info_panel_label_line("excerpts", str(len(evidence.items))),
    ]
    lines.extend(_info_panel_evidence_item_lines(evidence))
    return lines


def _info_panel_evidence_scope(session: ChatSession, evidence: TurnEvidence) -> str:
    if session.source_files:
        return f"{_active_material_count(session)}/{len(session.source_files)}"
    sampled_sources = evidence.sampled_source_count or len(
        {item.source for item in evidence.items}
    )
    total_sources = evidence.total_source_count or sampled_sources
    return f"{sampled_sources}/{total_sources}"


def _info_panel_evidence_item_lines(evidence: TurnEvidence) -> list[_InfoPanelLine]:
    visible_items = evidence.items[:4]
    return [
        _InfoPanelLine(
            f"{item.evidence_id} @{_material_panel_display_name(item.source)}",
            label=item.evidence_id,
        )
        for item in visible_items
    ]


def _visible_info_panel_line(line: _InfoPanelLine) -> _InfoPanelLine:
    content = _info_panel_line(line.content)
    label = line.label if line.label and content.startswith(line.label) else ""
    return _InfoPanelLine(content, is_heading=line.is_heading, label=label)


def _info_panel_lines(
    session: ChatSession,
    *,
    busy: bool,
    progress: str,
) -> list[_InfoPanelLine]:
    if busy:
        return _info_panel_evidence_lines(session, busy=busy, progress=progress)
    evidence_visible = session.last_turn_evidence is not None and bool(
        session.last_turn_evidence.items
    )
    if evidence_visible:
        return _info_panel_evidence_lines(session, busy=busy, progress=progress)
    return _info_panel_material_lines(session)


def _ellipsize_end(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    if max_length <= 3:
        return "." * max_length
    return f"{text[: max_length - 3].rstrip()}..."


def _info_panel_line(line: str) -> str:
    if not line:
        return ""
    return _ellipsize_end(line, _INFO_PANEL_VISIBLE_WIDTH)


def _visible_info_panel_lines(lines: Sequence[_InfoPanelLine]) -> list[_InfoPanelLine]:
    return [_visible_info_panel_line(line) for line in lines]


def _info_panel_text(lines: Sequence[_InfoPanelLine]) -> str:
    return "\n".join(line.content for line in _visible_info_panel_lines(lines))


def info_panel_evidence_id_at_line(
    session: ChatSession,
    line_index: int,
    *,
    busy: bool = False,
    progress: str = "",
) -> str | None:
    if line_index < 0:
        return None
    lines = _visible_info_panel_lines(_info_panel_lines(session, busy=busy, progress=progress))
    if line_index >= len(lines):
        return None
    label = lines[line_index].label
    if label.startswith("E") and label[1:].isdigit():
        return label
    return None


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


def _stylize_info_panel_labels(text: Text, lines: Sequence[_InfoPanelLine]) -> None:
    palette = current_palette()
    offset = 0
    for index, line in enumerate(lines):
        label = line.label or (line.content if line.is_heading else "")
        if label:
            label_start = offset + line.content.index(label)
            text.stylize(palette.text_secondary, label_start, label_start + len(label))
        offset += len(line.content)
        if index + 1 < len(lines):
            offset += 1


def _stylize_info_panel_materials(
    text: Text,
    lines: Sequence[_InfoPanelLine],
    session: ChatSession,
) -> None:
    palette = current_palette()
    offset = 0
    material_index = 0
    for line_index, line in enumerate(lines):
        if (
            not line.label
            and line.content.startswith("@")
            and material_index < len(session.source_files)
        ):
            name = session.source_files[material_index]
            style = (
                palette.text_muted
                if name in session.disabled_source_files
                else palette.text_primary
            )
            text.stylize(style, offset, offset + len(line.content))
            material_index += 1
        offset += len(line.content)
        if line_index + 1 < len(lines):
            offset += 1


def _stylize_hidden_material_count(text: Text, plain: str, session: ChatSession) -> None:
    hidden_material_count = max(0, len(session.source_files) - 8)
    if not hidden_material_count:
        return
    palette = current_palette()
    detail = label_value_line("more", f"+{hidden_material_count}")
    detail_start = plain.find(detail)
    if detail_start < 0:
        return
    text.stylize(palette.text_muted, detail_start, detail_start + len(detail))


def info_panel_default_text(
    session: ChatSession,
    *,
    busy: bool = False,
    progress: str = "",
) -> Text:
    palette = current_palette()
    lines = _visible_info_panel_lines(_info_panel_lines(session, busy=busy, progress=progress))
    plain = "\n".join(line.content for line in lines)
    text = require_rich_text()(plain, style=palette.text_muted)
    _stylize_info_panel_labels(text, lines)
    _stylize_hidden_material_count(text, plain, session)
    _stylize_info_panel_materials(text, lines, session)
    return text


def startup_card_text() -> str:
    return "\n".join(
        [
            label_value_line("materials", "materials/"),
            label_value_line("armory", "exact names or paths"),
            label_value_line("focus", "@file"),
            label_value_line("review", "summaries or gaps"),
            label_value_line("priority", "/priority"),
            label_value_line("evidence", "/evidence"),
            "",
            label_value_line("verify", "important claims"),
        ]
    )


def new_chat_card_text() -> str:
    return f"{label_value_line('focus', '@file')}  {label_value_line('evidence', '/evidence')}"


def armory_home_text(keymap: RuntimeKeymap | None = None) -> str:
    open_key = keymap.primary_key("open_armory_home") if keymap is not None else ""
    if not open_key:
        open_key = armory_shortcut_key()
    hints = [
        label_value_line("open", open_key),
        label_value_line("open", "exact armory name"),
        label_value_line("scope", "~/.armories"),
        label_value_line("materials", "materials/"),
    ]
    return "\n".join(hints)


def info_panel_message_text(entry: TuiTranscriptEntry, session: ChatSession) -> Text:
    palette = current_palette()
    lines = [_info_panel_line(line) for line in _info_panel_message_lines(entry, session)]
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
    fields = (
        ("model", model),
        ("tokens", usage["total_tokens"]),
        ("cost", f"${usage['cost_usd']:.4f}"),
        ("evidence", evidence_str),
        ("details", f"{_evidence_shortcut_key()} or /evidence"),
    )
    return [
        "Assistant reply",
        sep,
        *(f"{label.upper():<8} {str(value).lower()}" for label, value in fields),
    ]


def _evidence_shortcut_key() -> str:
    return default_runtime_keymap().primary_key("evidence")


def _stylize_message_panel_title(text: Text, plain: str, title: str) -> None:
    palette = current_palette()
    title_start = plain.index(title)
    text.stylize(f"bold {palette.text_primary}", title_start, title_start + len(title))


def _stylize_message_panel_labels(text: Text, plain: str) -> None:
    palette = current_palette()
    offset = 0
    for line in plain.splitlines(keepends=True):
        visible_line = line.removesuffix("\n")
        label = visible_line.split(maxsplit=1)[0] if visible_line else ""
        if label.isupper():
            label_start = offset + visible_line.index(label)
            text.stylize(f"dim {palette.text_muted}", label_start, label_start + len(label))
        offset += len(line)
