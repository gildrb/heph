"""Model picker option helpers for TUI inline flows."""

from __future__ import annotations

from interfaces.tui.display_text import menu_label_value


def _duplicate_model_names(choices: list[tuple[str, str, str, bool]]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for _slug, model, _display_name, _is_free in choices:
        if model in seen:
            duplicates.add(model)
        seen.add(model)
    return duplicates


def _model_flow_option(
    *,
    model: str,
    display_name: str,
    is_free: bool,
    is_duplicate: bool,
    is_current: bool,
) -> tuple[str, str]:
    description_tags = [
        menu_label_value("cost", "free") if is_free else "",
        menu_label_value("state", "current") if is_current else "",
    ]
    description = "  ".join(
        [menu_label_value("provider", display_name), *(tag for tag in description_tags if tag)]
    )
    return _model_choice_label(model, display_name, duplicate=is_duplicate), description


def _model_choice_label(model: str, display_name: str, *, duplicate: bool) -> str:
    if not duplicate:
        return model
    return f"{model} [{display_name}]"


def _model_choice_from_label(
    label: str,
    choices: list[tuple[str, str, str, bool]],
) -> tuple[str, str, str, bool] | None:
    model, provider = _parse_model_choice_label(label)
    for choice in choices:
        _slug, choice_model, display_name, _is_free = choice
        if choice_model != model:
            continue
        if provider is not None and display_name != provider:
            continue
        return choice
    return None


def _parse_model_choice_label(label: str) -> tuple[str, str | None]:
    model = label.strip()
    if model.endswith("]") and " [" in model:
        model, bracketed_provider = model.rsplit(" [", 1)
        return model, bracketed_provider[:-1]
    return model, None
