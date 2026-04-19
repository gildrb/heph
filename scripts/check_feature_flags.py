#!/usr/bin/env python3
"""Check for dead feature flags.

Scans the codebase for feature flag references and reports any flags
that are defined but never checked, or checked but never defined.

A flag is "defined" if it appears in:
  - HEPHAISTOS_FEATURE_FLAGS documentation
  - _parse_feature_flags() comments or code
  - pyproject.toml or config defaults

A flag is "used" if it appears in is_feature_enabled() calls or
feature_flags iteration.

Usage:
    python scripts/check_feature_flags.py
    python scripts/check_feature_flags.py --strict  # exit 1 on any finding
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "hephaistos"

# Known feature flags and their descriptions.
# Update this set when adding new flags.
KNOWN_FLAGS: dict[str, str] = {
    # Add flags here as they are introduced, e.g.:
    # "rag": "Enable RAG retrieval in chat sessions",
}

FLAG_DEFINITION_PATTERNS = [
    re.compile(r"is_feature_enabled\(['\"](\w+)['\"]\)"),
    re.compile(r"feature_flags.*['\"](\w+)['\"]"),
    re.compile(r"HEPHAISTOS_FEATURE_FLAGS.*['\"](\w+)['\"]"),
    re.compile(r"#.*flag[:\s]+(\w+)", re.IGNORECASE),
]

FLAG_IN_CONFIG_PATTERN = re.compile(r"feature_flags\s*=\s*['\"]([^'\"]+)['\"]")

# Names to exclude from flag detection — these are config keys / env var
# names, not actual feature flag names.
_SKIP_NAMES: frozenset[str] = frozenset(
    {
        "feature_flags",  # config key name, not a flag
        "HEPHAISTOS_FEATURE_FLAGS",  # env var name, not a flag
    }
)


def _find_flag_references() -> set[str]:
    """Scan source files for all feature flag name references."""
    found: set[str] = set()
    for py_file in SOURCE_DIR.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for pattern in FLAG_DEFINITION_PATTERNS:
            for match in pattern.finditer(text):
                flag = match.group(1)
                if flag.isidentifier() and not flag.startswith("_"):
                    found.add(flag)
    found.difference_update(_SKIP_NAMES)
    return found


def _find_flags_in_docs() -> set[str]:
    """Scan documentation for feature flag references."""
    found: set[str] = set()
    for md_file in REPO_ROOT.rglob("*.md"):
        if ".hephaistos" in str(md_file) or "site" in str(md_file):
            continue
        text = md_file.read_text(encoding="utf-8")
        for pattern in FLAG_DEFINITION_PATTERNS:
            for match in pattern.finditer(text):
                flag = match.group(1)
                if flag.isidentifier() and not flag.startswith("_"):
                    found.add(flag)
        for match in FLAG_IN_CONFIG_PATTERN.finditer(text):
            for flag in match.group(1).split(","):
                flag = flag.strip()
                if flag and flag.isidentifier():
                    found.add(flag)
    found.difference_update(_SKIP_NAMES)
    return found


def main() -> int:
    strict = "--strict" in sys.argv

    defined = set(KNOWN_FLAGS.keys())
    referenced = _find_flag_references() | _find_flags_in_docs()

    if not defined and not referenced:
        print("No feature flags found. Register flags in KNOWN_FLAGS to enable detection.")
        return 0

    # Flags defined but never referenced = potentially dead
    dead = defined - referenced
    # Flags referenced but not defined = undocumented
    undocumented = referenced - defined

    exit_code = 0

    if dead:
        print("Dead feature flags (defined but never referenced):")
        for flag in sorted(dead):
            desc = KNOWN_FLAGS.get(flag, "")
            print(f"  - {flag}" + (f": {desc}" if desc else ""))
        if strict:
            exit_code = 1

    if undocumented:
        print("Undocumented feature flags (referenced but not in KNOWN_FLAGS):")
        for flag in sorted(undocumented):
            print(f"  - {flag}")
        if strict:
            exit_code = 1

    if not dead and not undocumented:
        print(f"All {len(defined)} feature flags are accounted for.")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
