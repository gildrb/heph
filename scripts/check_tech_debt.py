"""Scan Python source files for TODO/FIXME comments lacking issue references.

Exit codes:
    0 - all TODO/FIXME comments have issue links (or none found)
    1 - one or more TODO/FIXME comments are missing issue links (--strict mode)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PATTERNS = [
    re.compile(r"#\s*TODO\b", re.IGNORECASE),
    re.compile(r"#\s*FIXME\b", re.IGNORECASE),
]

ISSUE_RE = re.compile(r"#\d+|GH-\d+|https?://\S+/issues/\d+")

EXCLUDE_DIRS = {
    ".artifacts",
    ".venv",
    "__pycache__",
    ".git",
    "node_modules",
    "dist",
    ".mypy_cache",
}


def find_python_files(root: Path) -> list[Path]:
    """Return all .py files under *root*, skipping known junk directories."""
    return sorted(
        p
        for p in root.rglob("*.py")
        if not any(part in EXCLUDE_DIRS for part in p.relative_to(root).parts)
    )


def check_file(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (line_number, full_line, pattern_type) for offending lines."""
    offences: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for pat in PATTERNS:
            if pat.search(line):
                if not ISSUE_RE.search(line):
                    tag = "TODO" if "TODO" in pat.pattern else "FIXME"
                    offences.append((lineno, line.strip(), tag))
                break
    return offences


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check that TODO/FIXME comments reference an issue.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error if any unlinked TODO/FIXME is found.",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print a summary report even when there are no offences.",
    )
    args = parser.parse_args()

    py_files = find_python_files(ROOT)
    total_offences = 0

    for path in py_files:
        rel = path.relative_to(ROOT)
        for lineno, line, tag in check_file(path):
            total_offences += 1
            print(f"{rel}:{lineno}: {tag} missing issue reference: {line}")

    if args.report or total_offences > 0:
        print(f"\n{total_offences} unlinked TODO/FIXME item(s) in {len(py_files)} file(s).")

    if args.strict and total_offences > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
