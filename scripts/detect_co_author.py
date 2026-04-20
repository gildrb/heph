"""Detect agent co-authorship on the latest commit or PR commits.

Looks for Factory/Droid signatures in commit messages and co-author trailers.
Outputs a summary suitable for CI annotations.

Exit codes:
    0 — detection completed (agent-authored or not)
    1 — error during detection
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

AGENT_PATTERNS = [
    re.compile(r"Co-authored-by:\s*Droid", re.IGNORECASE),
    re.compile(r"Co-authored-by:\s*.*[Ff]actory", re.IGNORECASE),
    re.compile(r"\[agent\]", re.IGNORECASE),
    re.compile(r"ai:", re.IGNORECASE),
]

KNOWN_AGENT_EMAILS = {"droid@factory.ai", "agent@factory.ai"}


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"git error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def get_commit_message(ref: str) -> str:
    return git("log", "-1", "--format=%B", ref)


def get_co_author_trailers(ref: str) -> list[str]:
    output = git("log", "-1", "--format=%(trailers:key=Co-authored-by)", ref)
    return [line.strip() for line in output.splitlines() if line.strip()]


def detect_agent(commitish: str = "HEAD") -> dict[str, object]:
    message = get_commit_message(commitish)
    trailers = get_co_author_trailers(commitish)

    matched_patterns = [pat.pattern for pat in AGENT_PATTERNS if pat.search(message)]

    agent_trailers = [
        t for t in trailers if any(email in t.lower() for email in KNOWN_AGENT_EMAILS)
    ]

    is_agent = bool(matched_patterns) or bool(agent_trailers)

    return {
        "commit": git("rev-parse", "--short", commitish),
        "is_agent": is_agent,
        "matched_patterns": matched_patterns,
        "agent_trailers": agent_trailers,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect agent co-authorship on commits.",
    )
    parser.add_argument(
        "--commit",
        default="HEAD",
        help="Commit ref to check (default: HEAD).",
    )
    parser.add_argument(
        "--pr",
        action="store_true",
        help="Check all commits in the PR (base..HEAD).",
    )
    args = parser.parse_args()

    if args.pr:
        merge_base = git("merge-base", "origin/main", "HEAD")
        commits = git("log", "--format=%H", f"{merge_base}..HEAD").splitlines()
        results = [detect_agent(c) for c in commits if c]
    else:
        results = [detect_agent(args.commit)]

    agent_commits = [r for r in results if r["is_agent"]]
    total = len(results)

    if agent_commits:
        print(f"Agent-authored commits: {len(agent_commits)}/{total}")
        for r in agent_commits:
            pats = r["matched_patterns"]
            trails = r["agent_trailers"]
            print(f"  {r['commit']}: patterns={pats}, trailers={trails}")
    else:
        print(f"No agent-authored commits detected ({total} commit(s) checked).")


if __name__ == "__main__":
    main()
