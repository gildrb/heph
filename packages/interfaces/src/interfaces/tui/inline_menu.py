"""Generic inline-menu rendering and selection helpers for the TUI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar

from hephaion.chat import storage as chat_storage
from hephaion.chat.titles import sanitize_title_text
from hephaion.chat.turn_history import TurnSnapshot
from hephaion.matching import ranked_matches

from interfaces.terminal import current_palette
from interfaces.tui.flow_state import InlineFlow
from interfaces.tui.slash_completion import completion_menu_visible_slice

try:
    from rich.text import Text as _RichText
    from textual.widgets import OptionList
except ImportError:
    _RichText = None  # ty:ignore[invalid-assignment]
    OptionList = None  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from rich.text import Text
    from textual import events

_WidgetT = TypeVar("_WidgetT")

_INLINE_MENU_DESCRIPTION_GAP = 4
_INLINE_MENU_FALLBACK_VISIBLE_ROWS = 7
_LOCAL_OPTION_SEPARATOR = "\t"
_LOCAL_COLUMN_GAP = 2
_LOCAL_MIN_DETAIL_WIDTH = 10
_LOCAL_PROMPT_FALLBACK_WIDTH = 96
_LOCAL_SOURCE_WIDTH = 8
_LOCAL_STATUS_WIDTH = 13
_LOCAL_QUANT_WIDTH = 8
_LOCAL_SIZE_WIDTH = 8
_LOCAL_PROVIDER_PREFIX = "llama-cpp/"
_SESSION_OPTION_SEPARATOR = "\t"
_SESSION_TITLE_GAP = 2
_SESSION_METADATA_GAP = 2
_OPTION_HORIZONTAL_PADDING = 4
_INLINE_SELECTED_PREFIX = "→ "
_INLINE_UNSELECTED_PREFIX = "  "
_SESSION_PROMPT_FALLBACK_WIDTH = 80
_TURN_PREVIEW_LIMIT = 64


class _InlineMenuHost(Protocol):
    _inline_flow: InlineFlow

    def query_one(self, selector: str, expect_type: type[_WidgetT]) -> _WidgetT: ...


def _inline_menu_option_text(
    label: str,
    description: str,
    *,
    selected: bool,
    label_width: int = 0,
) -> str | Text:
    label = _inline_menu_visible_text(label)
    description = _inline_menu_description_text(description)
    padded_width = max(label_width, len(label))
    prefix = _inline_selection_prefix(selected)
    if _RichText is None:
        if description:
            return (
                f"{prefix}{label:<{padded_width}}{' ' * _INLINE_MENU_DESCRIPTION_GAP}{description}"
            )
        return f"{prefix}{label}"
    palette = current_palette()
    label_style = palette.brand_primary if selected else palette.text_secondary
    description_style = palette.text_muted
    prefix_style = palette.brand_primary if selected else palette.text_muted
    text = _RichText()
    text.append(prefix, style=prefix_style)
    text.append(f"{label:<{padded_width}}" if description else label, style=label_style)
    if description:
        text.append(" " * _INLINE_MENU_DESCRIPTION_GAP, style=description_style)
        text.append(description, style=description_style)
    return text


def _inline_selection_prefix(selected: bool) -> str:
    return _INLINE_SELECTED_PREFIX if selected else _INLINE_UNSELECTED_PREFIX


def _inline_menu_visible_text(value: str) -> str:
    return sanitize_title_text(value, max_chars=max(1, len(value)))


def _inline_menu_description_text(value: str) -> str:
    needs_cleanup = any(char != " " and (char.isspace() or ord(char) < 32) for char in value)
    if needs_cleanup:
        return sanitize_title_text(value, max_chars=max(1, len(value)))
    return value.strip()


def _session_option_description(entry: chat_storage.SessionRecord) -> str:
    title = _inline_menu_visible_text(entry["title"]) or "(untitled)"
    metadata = _inline_menu_visible_text(entry["updated_at"])
    return f"{title}{_SESSION_OPTION_SEPARATOR}{metadata}"


def _prompt_width(widget_width: int, fallback_width: int | None) -> int:
    width = widget_width
    if width <= _OPTION_HORIZONTAL_PADDING:
        width = fallback_width or _SESSION_PROMPT_FALLBACK_WIDTH
    return max(1, width - _OPTION_HORIZONTAL_PADDING)


def _split_session_option_description(description: str) -> tuple[str, str]:
    title, separator, metadata = description.partition(_SESSION_OPTION_SEPARATOR)
    if separator:
        return _inline_menu_visible_text(title), _inline_menu_visible_text(metadata)
    return _inline_menu_visible_text(description), ""


def _truncate_with_ellipsis(value: str, width: int) -> str:
    if width <= 0:
        return ""
    if len(value) <= width:
        return value
    if width <= 3:
        return "." * width
    return f"{value[: width - 3]}..."


def _session_menu_option_parts(
    label: str,
    description: str,
    *,
    label_width: int,
    prompt_width: int,
) -> tuple[str, str, str, str, str]:
    label = _inline_menu_visible_text(label)
    title, metadata = _split_session_option_description(description)
    padded_label_width = max(label_width, len(label))
    if prompt_width <= padded_label_width:
        return _truncate_with_ellipsis(label, prompt_width), "", "", "", ""

    label_text = f"{label:<{padded_label_width}}"
    remaining_width = prompt_width - len(label_text)
    title_gap = " " * min(_SESSION_TITLE_GAP, remaining_width)
    remaining_width -= len(title_gap)

    metadata_gap_width = 0
    if metadata and remaining_width > _SESSION_METADATA_GAP:
        metadata_gap_width = _SESSION_METADATA_GAP
        metadata_width = remaining_width - metadata_gap_width
        metadata = _truncate_with_ellipsis(metadata, metadata_width)
    else:
        metadata = ""

    metadata_width = len(metadata)
    title_width = remaining_width - metadata_gap_width - metadata_width
    title_text = _truncate_with_ellipsis(title, title_width)
    metadata_gap = ""
    if metadata:
        used_width = len(label_text) + len(title_gap) + len(title_text) + metadata_width
        metadata_gap = " " * max(_SESSION_METADATA_GAP, prompt_width - used_width)
    return label_text, title_gap, title_text, metadata_gap, metadata


def _session_menu_option_text(
    label: str,
    description: str,
    *,
    selected: bool,
    label_width: int,
    prompt_width: int,
) -> str | Text:
    prefix = _inline_selection_prefix(selected)
    parts = _session_menu_option_parts(
        label,
        description,
        label_width=label_width,
        prompt_width=max(1, prompt_width - len(prefix)),
    )
    if _RichText is None:
        return f"{prefix}{''.join(parts)}"
    palette = current_palette()
    label_style = palette.brand_primary if selected else palette.text_secondary
    title_style = palette.text_primary if selected else palette.text_muted
    metadata_style = palette.text_muted
    prefix_style = palette.brand_primary if selected else palette.text_muted
    text = _RichText()
    label_text, title_gap, title_text, metadata_gap, metadata = parts
    text.append(prefix, style=prefix_style)
    text.append(label_text, style=label_style)
    text.append(title_gap, style=title_style)
    text.append(title_text, style=title_style)
    text.append(metadata_gap, style=metadata_style)
    text.append(metadata, style=metadata_style)
    return text


def local_model_option_description(
    source: str,
    status: str,
    quant: str,
    size: str,
    detail: str,
) -> str:
    fields = (
        _inline_menu_visible_text(source),
        _inline_menu_visible_text(status),
        _inline_menu_visible_text(quant),
        _inline_menu_visible_text(size),
        _inline_menu_description_text(detail),
    )
    return _LOCAL_OPTION_SEPARATOR.join(fields)


def _local_model_option_text(
    label: str,
    description: str,
    *,
    selected: bool,
    prompt_width: int,
) -> str | Text:
    prefix = _inline_selection_prefix(selected)
    parts = _local_model_option_parts(
        label,
        description,
        prompt_width=max(1, prompt_width - len(prefix)),
    )
    if _RichText is None:
        return f"{prefix}{''.join(parts)}"
    palette = current_palette()
    label_style = palette.brand_primary if selected else palette.text_secondary
    metadata_style = palette.text_muted
    quant_style = palette.text_primary if selected else palette.text_secondary
    prefix_style = palette.brand_primary if selected else palette.text_muted
    text = _RichText()
    label_text, gap, source, status, quant, size, detail_gap, detail = parts
    text.append(prefix, style=prefix_style)
    text.append(label_text, style=label_style)
    text.append(gap, style=metadata_style)
    text.append(source, style=metadata_style)
    text.append(status, style=metadata_style)
    text.append(quant, style=quant_style)
    text.append(size, style=metadata_style)
    text.append(detail_gap, style=metadata_style)
    text.append(detail, style=metadata_style)
    return text


def _local_model_option_parts(
    label: str,
    description: str,
    *,
    prompt_width: int,
) -> tuple[str, str, str, str, str, str, str, str]:
    label = _local_model_visible_label(label)
    source, status, quant, size, detail = _split_local_model_description(description)
    metadata = _local_model_metadata(source, status, quant, size)
    metadata_width = sum(len(part) for part in metadata)
    gap = " " * _LOCAL_COLUMN_GAP
    label_width = prompt_width - len(gap) - metadata_width
    if label_width <= 0:
        return (_truncate_with_ellipsis(label, prompt_width), "", "", "", "", "", "", "")

    detail_gap = ""
    if detail and label_width > len(label) + len(gap) + _LOCAL_MIN_DETAIL_WIDTH:
        detail_gap = gap
        detail_width = label_width - len(label) - len(detail_gap)
        detail = _truncate_with_ellipsis(detail, detail_width)
        label_width = len(label)
    else:
        detail = ""

    label_text = _truncate_with_ellipsis(label, label_width)
    return (label_text.ljust(label_width), gap, *metadata, detail_gap, detail)


def _local_model_metadata(
    source: str,
    status: str,
    quant: str,
    size: str,
) -> tuple[str, str, str, str]:
    return (
        _local_model_column(source, _LOCAL_SOURCE_WIDTH),
        _local_model_column(status, _LOCAL_STATUS_WIDTH),
        _local_model_column(quant, _LOCAL_QUANT_WIDTH),
        _local_model_column(size, _LOCAL_SIZE_WIDTH),
    )


def _local_model_column(value: str, width: int) -> str:
    return _truncate_with_ellipsis(value, width).ljust(width)


def _local_model_visible_label(label: str) -> str:
    visible = _inline_menu_visible_text(label)
    return visible.removeprefix(_LOCAL_PROVIDER_PREFIX)


def _split_local_model_description(description: str) -> tuple[str, str, str, str, str]:
    parts = description.split(_LOCAL_OPTION_SEPARATOR, maxsplit=4)
    if len(parts) == 5:
        source, status, quant, size, detail = parts
        return (
            _inline_menu_visible_text(source),
            _inline_menu_visible_text(status),
            _inline_menu_visible_text(quant),
            _inline_menu_visible_text(size),
            _inline_menu_description_text(detail),
        )
    return "", _inline_menu_description_text(description), "", "", ""


def _inline_menu_label_width(options: list[tuple[str, str]]) -> int:
    return max((_inline_menu_visible_width(label) for label, _description in options), default=0)


def _inline_menu_visible_width(value: str) -> int:
    return len(_inline_menu_visible_text(value))


def _turn_option_description(snapshot: TurnSnapshot) -> str:
    preview = " ".join(snapshot.user_input.split())
    if len(preview) > _TURN_PREVIEW_LIMIT:
        preview = f"{preview[: _TURN_PREVIEW_LIMIT - 3]}..."
    evidence_count = len(snapshot.evidence.items) if snapshot.evidence is not None else 0
    evidence_label = f"{evidence_count} evidence" if evidence_count else "no evidence"
    return f"{preview}  {evidence_label}"


def _inline_menu_visible_label_width(
    options: list[tuple[str, str]],
    *,
    highlighted: int,
    rendered_height: int,
) -> int:
    if rendered_height <= 0:
        rendered_height = min(len(options), _INLINE_MENU_FALLBACK_VISIBLE_ROWS)
    if rendered_height <= 0:
        return _inline_menu_label_width(options)
    visible_options = options[
        completion_menu_visible_slice(
            max(0, highlighted),
            len(options),
            rendered_height,
        )
    ]
    if not visible_options:
        return _inline_menu_label_width(options)
    return _inline_menu_label_width(visible_options)


def _inline_menu_scrolled_label_width(
    options: list[tuple[str, str]],
    *,
    scroll_y: int,
    rendered_height: int,
) -> int:
    if not options:
        return 0
    if rendered_height <= 0:
        rendered_height = min(len(options), _INLINE_MENU_FALLBACK_VISIBLE_ROWS)
    if rendered_height <= 0:
        return 0
    visible_count = len(
        options[
            completion_menu_visible_slice(
                0,
                len(options),
                rendered_height,
            )
        ]
    )
    if visible_count <= 0:
        return _inline_menu_label_width(options)
    return _inline_menu_label_width(options[scroll_y : scroll_y + visible_count])


def _filtered_inline_options(
    options: list[tuple[str, str]],
    query: str,
) -> list[tuple[str, str]]:
    cleaned = query.strip()
    if not cleaned:
        return list(options)

    normalized = cleaned.casefold()
    direct = [option for option in options if normalized in f"{option[0]} {option[1]}".casefold()]
    fuzzy = ranked_matches(
        cleaned,
        options,
        key=lambda option: f"{option[0]} {option[1]}",
        limit=len(options),
        min_score=45.0,
    )
    return _dedupe_inline_options([*direct, *(match.value for match in fuzzy)])


def _dedupe_inline_options(options: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[tuple[str, str]] = []
    for label, description in options:
        key = (label.strip().casefold(), description.strip().casefold())
        if key in seen:
            continue
        seen.add(key)
        deduped.append((label, description))
    return deduped


def _consume_inline_key(event: events.Key) -> bool:
    event.prevent_default()
    event.stop()
    return True


def _inline_option_index(options: list[tuple[str, str]], label: str | None) -> int:
    if label is None:
        return 0
    for index, (option_label, _description) in enumerate(options):
        if option_label == label:
            return index
    return 0


def _selected_inline_label(host: _InlineMenuHost, value: str) -> str:
    if label := _typed_inline_label(host, value):
        return label
    selected = _highlighted_inline_option_index(host)
    return host._inline_flow.options[selected][0]


def _typed_inline_label(host: _InlineMenuHost, value: str) -> str:
    cleaned = value.strip().casefold()
    if not cleaned:
        return ""
    for candidate, _description in [*host._inline_flow.options, *host._inline_flow.all_options]:
        if candidate.casefold() == cleaned:
            return candidate
    return ""


def _highlighted_inline_option_index(host: _InlineMenuHost) -> int:
    suggestions = host.query_one("#suggestions", OptionList)
    selected = suggestions.highlighted if suggestions.highlighted is not None else 0
    return min(selected, len(host._inline_flow.options) - 1)
