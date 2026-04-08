"""Autonomy tiers for tool execution.

Instead of gating per-tool-name, we classify *what* the tool is actually doing
and compare against the session's autonomy level.

Tiers (ordered low → high):
  none   — Read-only: cat, ls, grep, git status/log/diff, etc.
  low    — Low-risk file ops: touch, mkdir, cp, mv (no sudo).
  medium — Dev operations: package installs (no sudo), git commit/pull, builds, tests.
  high   — Production: git push, sudo, arbitrary scripts, deployments.
  unsafe — Everything allowed (sandboxed envs only).

The key insight: a bash("cat file.txt") is harmless but bash("rm -rf /") is
catastrophic. We parse the command and classify based on the actual operations.
"""

from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path

from hephaistos.app.display import STYLE_DIM, STYLE_PROMPT, styled

# ---------------------------------------------------------------------------
# Tier ordering
# ---------------------------------------------------------------------------

_TIER_ORDER: dict[str, int] = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "unsafe": 4,
}

VALID_TIERS = list(_TIER_ORDER)

_TIER_DESCRIPTIONS = {
    "none": "Read-only — ls, cat, grep, git status. No writes.",
    "low": "Low-risk file ops — touch, mkdir, cp, mv. No system changes.",
    "medium": "Dev ops — installs, git commit/pull, builds, tests. No push/sudo.",
    "high": "Production — git push, sudo, scripts, deployments.",
    "unsafe": "Everything allowed. Sandbox only!",
}

# ---------------------------------------------------------------------------
# Bash command classification
# ---------------------------------------------------------------------------

# Commands that are always read-only
_NONE_COMMANDS = frozenset(
    {
        "cat",
        "head",
        "tail",
        "less",
        "more",
        "ls",
        "file",
        "wc",
        "diff",
        "pwd",
        "echo",
        "whoami",
        "date",
        "uname",
        "hostname",
        "uptime",
        "ps",
        "top",
        "htop",
        "df",
        "du",
        "free",
        "env",
        "printenv",
        "which",
        "where",
        "type",
        "command",
        "true",
        "false",
        "test",
        "basename",
        "dirname",
        "realpath",
        "readlink",
        "stat",
        "find",
        "locate",
        "tree",
        "grep",
        "rg",
        "ag",
        "ack",
        "fgrep",
        "egrep",
        "sort",
        "uniq",
        "cut",
        "tr",
        "paste",
        "tee",
        "fmt",
        "md5sum",
        "sha256sum",
        "sha1sum",
        "xxd",
        "hexdump",
        "seq",
        "bc",
        "expr",
        "factor",
        "id",
        "groups",
        "ulimit",
        "git",  # git is special-cased below
        "curl",
        "wget",  # GETs without pipe-to-bash are read-only
        "python",
        "python3",
        "node",  # running a script is classified by args
    }
)

# Commands that are low-risk (file creation/modification, no system changes)
_LOW_COMMANDS = frozenset(
    {
        "touch",
        "mkdir",
        "cp",
        "mv",
        "chmod",
        "chown",
        "ln",
        "rmdir",
        "zip",
        "unzip",
        "tar",
        "gzip",
        "gunzip",
        "bzip2",
        "xz",
        "sed",
        "awk",
        "perl",
        "ruby",  # text processing — typically safe
        "patch",
    }
)

# Commands that are medium-risk (dev operations, recoverable)
_MEDIUM_COMMANDS = frozenset(
    {
        "pip",
        "pip3",
        "npm",
        "yarn",
        "pnpm",
        "bun",
        "cargo",
        "go",
        "rustc",
        "gcc",
        "g++",
        "cc",
        "make",
        "cmake",
        "pytest",
        "jest",
        "mocha",
        "vitest",
        "cargo-test",
        "dotnet",
        "gradle",
        "maven",
        "mvn",
        "ant",
        "docker",
        "podman",  # container ops
        "npm-run",
        "npx",
    }
)

# Patterns that immediately escalate to high
_HIGH_PATTERNS = frozenset(
    {
        "sudo",
        "su ",
        "doas",
        "run0",
        "rm -rf",
        "rm -r /",
        "rm -rf /",
        "mkfs",
        "dd if=",
        "dd of=/dev",
        "chmod 777",
        "chmod -R 777",
        "> /dev/",  # writing to device files
        "iptables",
        "nft ",
        "ufw ",
        "systemctl",
        "service ",
        "crontab -",
        "at now",
        "ssh ",
        "scp ",
        "rsync ",  # network writes
        "kill -9",
        "killall",
        "pkill",
        "nohup",
        "disown",
        "eval ",
        "exec ",
    }
)

# Patterns that are medium (package installs, builds, git local ops)
_MEDIUM_PATTERNS = frozenset(
    {
        "install",
        "pip install",
        "pip3 install",
        "npm install",
        "yarn add",
        "git commit",
        "git checkout",
        "git switch",
        "git pull",
        "git rebase",
        "git stash",
        "git cherry-pick",
        "git merge",
        "git reset",
        "make ",
        "cmake ",
        "cargo build",
        "cargo test",
        "cargo run",
        "go build",
        "go test",
        "go run",
        "go mod",
        "pytest",
        "jest",
        "mocha ",
        "vitest ",
        "npm run ",
        "npm build",
        "npx ",
        "python -m pytest",
        "python3 -m pytest",
    }
)


def _split_compound(command: str) -> list[str]:
    """Split a command into sub-commands on &&, ||, ;, and pipes."""
    # Simple approach: split on && || ; |
    # We don't try to handle nested quotes perfectly — heuristic is fine.
    parts: list[str] = []
    # Split on ; first
    segments = command.split(";")
    for seg in segments:
        # Split on && and ||
        sub_parts = re.split(r"\s*(?:&&|\|\|)\s*", seg)
        for sub in sub_parts:
            # Split on | (pipes) — but not || (already handled)
            pipe_parts = re.split(r"(?<!\|)\|(?!\|)", sub)
            parts.extend(pipe_parts)
    return [p.strip() for p in parts if p.strip()]


def _classify_single(command: str) -> str:
    """Classify a single (non-compound) command to a tier."""
    stripped = command.strip()

    # Check for sudo/doas anywhere
    if re.search(r"\bsudo\b|\bdoas\b|\bru?n0\b", stripped):
        return "high"

    # Check high-risk patterns
    for pattern in _HIGH_PATTERNS:
        if pattern in stripped:
            return "high"

    # Check for pipe-to-bash patterns (curl | bash, wget -qO- | sh)
    if re.search(r"\|\s*(ba)?sh\b", stripped):
        return "high"

    # Check medium patterns
    for pattern in _MEDIUM_PATTERNS:
        if pattern in stripped:
            return "medium"

    # Try to extract the base command
    try:
        # Handle simple cases
        tokens = shlex.split(stripped, posix=False)
    except ValueError:
        # If shlex fails (unmatched quotes), use simple split
        tokens = stripped.split()

    if not tokens:
        return "none"

    base_cmd = tokens[0]

    # Bare shell invocation = arbitrary execution (high risk)
    if base_cmd in ("bash", "sh", "zsh", "fish", "dash", "ksh", "csh", "tcsh"):
        return "high"

    # Handle "git" subcommands specially
    if base_cmd == "git":
        git_sub = tokens[1] if len(tokens) > 1 else ""
        if git_sub in (
            "status",
            "log",
            "diff",
            "branch",
            "tag",
            "remote",
            "show",
            "config",
            "rev-parse",
            "shortlog",
            "blame",
            "reflog",
            "stash list",
            "notes",
            "ls-files",
            "ls-tree",
            "ls-remote",
        ):
            return "none"
        if git_sub in (
            "commit",
            "checkout",
            "switch",
            "pull",
            "rebase",
            "stash",
            "stash pop",
            "stash apply",
            "stash drop",
            "cherry-pick",
            "merge",
            "reset",
            "restore",
            "add",
            "rm",
            "mv",
            "init",
        ):
            return "medium"
        if git_sub in ("push", "force-push", "push --force"):
            return "high"
        # Unknown git subcommand — default to low
        return "low"

    # Handle "python/python3/node" — check if it's a test/build runner
    if base_cmd in ("python", "python3", "node"):
        args_str = " ".join(tokens[1:])
        if "pytest" in args_str or "unittest" in args_str:
            return "medium"
        if re.match(r"-c\s", args_str):
            # python -c "..." — classify by the code content
            return _classify_inline_code(args_str)
        return "low"

    # Check against known command sets
    if base_cmd in _NONE_COMMANDS:
        return "none"
    if base_cmd in _LOW_COMMANDS:
        return "low"
    if base_cmd in _MEDIUM_COMMANDS:
        return "medium"

    # Unknown command — default to low (safe default)
    return "low"


def _classify_inline_code(code: str) -> str:
    """Rough heuristic for inline code passed via python -c, etc."""
    if any(p in code for p in ("os.system", "subprocess", "shutil.rmtree", "os.remove")):
        return "high"
    if any(p in code for p in ("open(", "with open", "Path(")):
        return "low"
    return "none"


def classify_bash_command(command: str) -> str:
    """Classify a bash command (possibly compound) to its required autonomy tier.

    Returns one of: "none", "low", "medium", "high".
    For compound commands (&&, ||, ;, |), returns the maximum tier of all parts.
    """
    sub_commands = _split_compound(command)
    if not sub_commands:
        return "none"

    max_tier = "none"
    for sub in sub_commands:
        tier = _classify_single(sub)
        if _TIER_ORDER[tier] > _TIER_ORDER[max_tier]:
            max_tier = tier
            if max_tier == "high":
                break  # Can't go higher (ignoring unsafe from classification)
    return max_tier


# ---------------------------------------------------------------------------
# Tool-level tier mapping
# ---------------------------------------------------------------------------

_TOOL_TIER_MAP: dict[str, str] = {
    # Read-only tools
    "read_file": "none",
    "list_files": "none",
    "grep": "none",
    "web_fetch": "none",
    "web_search": "none",
    "question": "none",
    # File modification tools
    "write_file": "low",
    "edit_file": "low",
    "multi_edit": "low",
    "apply_patch": "low",
    # Execution tools — classified by command content
    "bash": "none",  # actual tier determined by classify_bash_command
    "execute": "none",
}


def get_required_tier(tool_name: str, args: dict) -> str:
    """Get the autonomy tier required for a tool call.

    For bash/execute tools, inspects the actual command.
    For other tools, uses the static _TOOL_TIER_MAP.
    """
    if tool_name in ("bash", "execute"):
        command = args.get("command", "")
        return classify_bash_command(command)

    return _TOOL_TIER_MAP.get(tool_name, "low")


def tier_allows(required: str, current: str) -> bool:
    """Check if the current autonomy level allows the required tier."""
    return _TIER_ORDER.get(current, 0) >= _TIER_ORDER.get(required, 0)


# ---------------------------------------------------------------------------
# Interactive permission prompt
# ---------------------------------------------------------------------------


def request_permission(
    tool_name: str,
    args: dict,
    required_tier: str,
    current_tier: str,
) -> bool:
    """Prompt the user for one-time approval of an over-tier operation.

    Returns True if approved.
    """
    summary = _format_tool_summary(tool_name, args)
    warn_style = "\033[1m\033[33m"
    sys.stdout.write(
        f"\n{styled('Permission required:', warn_style)} "
        f"{summary}\n"
        f"  Required: {styled(required_tier, STYLE_PROMPT)}  "
        f"Current: {styled(current_tier, STYLE_DIM)}\n"
        f"  {styled('[y]', STYLE_PROMPT)}es / "
        f"{styled('[n]', STYLE_PROMPT)}o / "
        f"{styled('[a]', STYLE_PROMPT)}lways allow this tier: "
    )
    sys.stdout.flush()
    try:
        answer = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        sys.stdout.write("\n")
        sys.stdout.flush()
        return False

    return answer in ("y", "yes", "a", "always")


def _format_tool_summary(name: str, args: dict) -> str:
    """Format a brief summary of a tool call for the confirmation prompt."""
    if name in ("bash", "execute"):
        cmd = args.get("command", "")
        return f"bash: {cmd[:120]}{'...' if len(cmd) > 120 else ''}"
    if name in ("write_file", "edit_file"):
        return f"{name}: {args.get('path', '')}"
    if name in ("multi_edit", "apply_patch"):
        return f"{name}: {args.get('path', '')} ({len(args.get('edits', []))} edits)"
    return f"{name}: {args}"


# ---------------------------------------------------------------------------
# Config loading (unchanged interface)
# ---------------------------------------------------------------------------

_CONFIG_PATH = ".hephaistos/config.toml"


def load_permissions(workspace: Path | None = None) -> dict:
    """Load permission overrides from project config.

    Returns a dict with optional keys:
      - autonomy: str — default autonomy level (default: "low")
      - auto_approve: set[str] — tools to always allow
      - deny: set[str] — tools to always block
    """
    auto_approve: set[str] = set()
    deny: set[str] = set()
    result: dict[str, str | set[str]] = {
        "autonomy": "low",
        "auto_approve": auto_approve,
        "deny": deny,
    }

    if workspace is None:
        return result

    config_path = workspace / _CONFIG_PATH
    if not config_path.is_file():
        return result

    try:
        from hephaistos.parameters.cli import _parse_toml_simple

        data = _parse_toml_simple(config_path)
    except Exception:
        return result

    # Read autonomy level
    autonomy = data.get("autonomy", "").strip().strip('"').strip("'")
    if autonomy in _TIER_ORDER:
        result["autonomy"] = autonomy

    # Read auto-approve tools
    for val in data.get("auto_approve", "").split(","):
        val = val.strip().strip('"').strip("'")
        if val:
            auto_approve.add(val)

    # Read denied tools
    for val in data.get("deny", "").split(","):
        val = val.strip().strip('"').strip("'")
        if val:
            deny.add(val)

    return result
