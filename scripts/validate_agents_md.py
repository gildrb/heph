"""Validate that commands documented in AGENTS.md actually exist.

Extracts fenced code blocks from AGENTS.md, identifies executable commands,
and checks that the referenced tools/commands are available.

Exit codes:
    0 — all commands valid
    1 — one or more commands are invalid or missing
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS_MD = ROOT / "AGENTS.md"

CODE_BLOCK_RE = re.compile(r"```bash\s*\n(.*?)```", re.DOTALL)

# Commands that require network, auth, or are interactive — skip them
SKIP_COMMANDS = {
    "uv sync",
    "uv build",
    "uv run heph",
    "uv run heph armory",
}

# Tools that must be present on the hook runner itself. Commands invoked through
# ``uv run`` are project tools, so they should not have to exist in pre-commit's
# own virtual environment.
REQUIRED_TOOLS = ["uv"]
PROJECT_RUN_TOOLS = {
    "heph",
    "hephaistos",
    "lint-imports",
    "pylint",
    "pytest",
    "python",
    "ruff",
    "ty",
    "vulture",
}


def extract_commands(text: str) -> list[str]:
    """Extract runnable command lines from bash code blocks."""
    commands: list[str] = []
    for match in CODE_BLOCK_RE.finditer(text):
        block = match.group(1)
        for line in block.splitlines():
            line = line.strip()
            # Skip comments, empty lines, and continued lines
            if not line or line.startswith("#"):
                continue
            # Take only the first command before '#' comment or '&&' chain
            # Strip inline comments
            if "  # " in line:
                line = line[: line.index("  # ")].strip()
            commands.append(line)
    return commands


def check_tool_available(tool: str) -> bool:
    return shutil.which(tool) is not None


def validate_commands(commands: list[str]) -> list[str]:
    """Return list of validation error messages."""
    errors = [
        f"Required tool not found: {tool}"
        for tool in REQUIRED_TOOLS
        if not check_tool_available(tool)
    ]

    # Validate individual commands
    for cmd in commands:
        # Skip known-interactive or network commands
        if any(cmd.startswith(skip) for skip in SKIP_COMMANDS):
            continue

        # Extract the base command
        parts = cmd.split()
        if not parts:
            continue

        base = parts[0]

        # uv run <tool> — check the inner tool
        if base == "uv" and len(parts) >= 2 and parts[1] == "run":
            inner_tool = parts[2] if len(parts) > 2 else ""
            if inner_tool and inner_tool not in PROJECT_RUN_TOOLS:
                errors.append(f"Command references unavailable tool: {cmd}")

        # Check that the base tool exists
        elif not check_tool_available(base) and base != "uv":
            errors.append(f"Command references unavailable tool: {cmd}")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate commands in AGENTS.md.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error on any validation failure.",
    )
    parser.add_argument(
        "--file",
        default=str(AGENTS_MD),
        help="Path to the markdown file to validate.",
    )
    args = parser.parse_args()

    md_path = Path(args.file)
    if not md_path.exists():
        print(f"File not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    text = md_path.read_text(encoding="utf-8")
    commands = extract_commands(text)

    print(f"Found {len(commands)} command(s) in {md_path.name}:")
    for cmd in commands:
        print(f"  {cmd}")

    errors = validate_commands(commands)

    if errors:
        print(f"\n{len(errors)} validation error(s):")
        for err in errors:
            print(f"  ✗ {err}")
        if args.strict:
            sys.exit(1)
    else:
        print("\nAll commands valid.")


if __name__ == "__main__":
    main()
