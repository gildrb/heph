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

_TIER_ORDER: dict[str, int] = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "unsafe": 4,
}


_TIER_DESCRIPTIONS = {
    "none": "Read-only — ls, cat, grep, git status. No writes.",
    "low": "Low-risk file ops — touch, mkdir, cp, mv. No system changes.",
    "medium": "Dev ops — installs, git commit/pull, builds, tests. No push/sudo.",
    "high": "Production — git push, sudo, scripts, deployments.",
    "unsafe": "Everything allowed. Sandbox only!",
}

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
    parts: list[str] = []
    segments = command.split(";")
    for seg in segments:
        sub_parts = re.split(r"\s*(?:&&|\|\|)\s*", seg)
        for sub in sub_parts:
            pipe_parts = re.split(r"(?<!\|)\|(?!\|)", sub)
            parts.extend(pipe_parts)
    return [p.strip() for p in parts if p.strip()]


def _classify_single(command: str) -> str:
    """Classify a single (non-compound) command to a tier."""
    stripped = command.strip()
    if re.search(r"\bsudo\b|\bdoas\b|\bru?n0\b", stripped):
        return "high"
    for pattern in _HIGH_PATTERNS:
        if pattern in stripped:
            return "high"
    if re.search(r"\|\s*(ba)?sh\b", stripped):
        return "high"
    for pattern in _MEDIUM_PATTERNS:
        if pattern in stripped:
            return "medium"
    try:
        tokens = shlex.split(stripped, posix=False)
    except ValueError:
        tokens = stripped.split()

    if not tokens:
        return "none"

    base_cmd = tokens[0]
    if base_cmd in ("bash", "sh", "zsh", "fish", "dash", "ksh", "csh", "tcsh"):
        return "high"
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
        return "low"
    if base_cmd in ("python", "python3", "node"):
        args_str = " ".join(tokens[1:])
        if "pytest" in args_str or "unittest" in args_str:
            return "medium"
        if re.match(r"-c\s", args_str):
            return _classify_inline_code(args_str)
        return "low"
    if base_cmd in _NONE_COMMANDS:
        return "none"
    if base_cmd in _LOW_COMMANDS:
        return "low"
    if base_cmd in _MEDIUM_COMMANDS:
        return "medium"
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


_TOOL_TIER_MAP: dict[str, str] = {
    "read_file": "none",
    "list_files": "none",
    "grep": "none",
    "web_fetch": "none",
    "web_search": "none",
    "question": "none",
    "write_file": "low",
    "edit_file": "low",
    "multi_edit": "low",
    "apply_patch": "low",
    "bash": "none",  # actual tier determined by classify_bash_command
    "execute": "none",
}


def tier_allows(required: str, current: str) -> bool:
    """Check if the current autonomy level allows the required tier."""
    return _TIER_ORDER.get(current, 0) >= _TIER_ORDER.get(required, 0)
