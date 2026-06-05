from __future__ import annotations

from collections.abc import Iterable

from heph_ai.providers.registry import get_registry

DEFAULT_REASONING_LEVEL = "low"
REASONING_LEVELS = ("low", "medium", "high", "xhigh")


def normalize_reasoning_level(value: object) -> str:
    if isinstance(value, str) and value.casefold() in REASONING_LEVELS:
        return value.casefold()
    return DEFAULT_REASONING_LEVEL


def next_reasoning_level(current: object, *, levels: Iterable[str] = REASONING_LEVELS) -> str:
    choices = tuple(level for level in levels if level in REASONING_LEVELS)
    if not choices:
        return DEFAULT_REASONING_LEVEL
    normalized = normalize_reasoning_level(current)
    try:
        index = choices.index(normalized)
    except ValueError:
        return choices[0]
    return choices[(index + 1) % len(choices)]


def reasoning_levels_for_model(model: str, provider: str | None = None) -> tuple[str, ...]:
    info = get_registry().get(model, provider=provider)
    if info is None or "reasoning" not in info.tags:
        return ()
    return info.reasoning_efforts or ("low", "medium", "high")
