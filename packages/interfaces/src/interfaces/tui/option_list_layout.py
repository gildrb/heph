"""Shared OptionList layout calculations."""

from __future__ import annotations


def visible_option_height(
    *,
    next_option_count: int,
    current_option_count: int,
    rendered_height: int,
    max_visible_rows: int,
) -> int:
    if next_option_count <= 0 or max_visible_rows <= 0:
        return 0
    visible_capacity = min(next_option_count, max_visible_rows)
    if rendered_height <= 0 and next_option_count > 0:
        return visible_capacity
    stale_growth_height = max(1, current_option_count)
    if (
        next_option_count > current_option_count
        and current_option_count < visible_capacity
        and rendered_height <= stale_growth_height
    ):
        return visible_capacity
    if (
        next_option_count >= visible_capacity
        and current_option_count >= visible_capacity
        and rendered_height < visible_capacity
    ):
        return visible_capacity
    return rendered_height
