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
    if rendered_height <= 0:
        return visible_capacity
    if _needs_growth_option_capacity(
        next_option_count=next_option_count,
        current_option_count=current_option_count,
        rendered_height=rendered_height,
        visible_capacity=visible_capacity,
    ):
        return visible_capacity
    if _needs_stale_full_list_capacity(
        next_option_count=next_option_count,
        current_option_count=current_option_count,
        rendered_height=rendered_height,
        visible_capacity=visible_capacity,
    ):
        return visible_capacity
    return rendered_height


def _needs_growth_option_capacity(
    *,
    next_option_count: int,
    current_option_count: int,
    rendered_height: int,
    visible_capacity: int,
) -> bool:
    list_is_growing = next_option_count > current_option_count
    stale_height = max(1, current_option_count)
    return (
        list_is_growing
        and current_option_count < visible_capacity
        and rendered_height <= stale_height
    )


def _needs_stale_full_list_capacity(
    *,
    next_option_count: int,
    current_option_count: int,
    rendered_height: int,
    visible_capacity: int,
) -> bool:
    list_fills_capacity = next_option_count >= visible_capacity
    previous_list_filled_capacity = current_option_count >= visible_capacity
    return (
        list_fills_capacity
        and previous_list_filled_capacity
        and rendered_height < visible_capacity
    )
