"""Terminal cell-width text helpers for fixed-column TUI layouts."""

from __future__ import annotations

from rich.cells import cell_len, chop_cells


def cell_width(value: str) -> int:
    return cell_len(value)


def chop_to_cell_width(value: str, width: int) -> str:
    if width <= 0:
        return ""
    return chop_cells(value, width)[0]


def truncate_with_ellipsis(value: str, width: int) -> str:
    if width <= 0:
        return ""
    if cell_width(value) <= width:
        return value
    if width <= 3:
        return "." * width
    return f"{chop_to_cell_width(value, width - 3)}..."


def pad_cell_left(value: str, width: int) -> str:
    padding = width - cell_width(value)
    if padding <= 0:
        return value
    return f"{' ' * padding}{value}"


def pad_cell_right(value: str, width: int) -> str:
    padding = width - cell_width(value)
    if padding <= 0:
        return value
    return f"{value}{' ' * padding}"
