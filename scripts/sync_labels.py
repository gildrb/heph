"""Sync GitHub repository labels from .github/labels.yml.

Creates or updates labels to match the declarative config. Optionally removes
labels not defined in the config file.

Usage:
    python scripts/sync_labels.py              # create/update only
    python scripts/sync_labels.py --prune      # also delete stale labels
    python scripts/sync_labels.py --dry-run    # preview changes without applying
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LABELS_FILE = ROOT / ".github" / "labels.yml"


def gh(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=check,
    )


def get_existing_labels() -> dict[str, dict[str, str]]:
    """Return {name: {color, description}} for all repo labels."""
    result = gh("label", "list", "--json", "name,color,description")
    if result.returncode != 0:
        print(f"Error listing labels: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    labels: dict[str, dict[str, str]] = {}
    for entry in json.loads(result.stdout):
        labels[entry["name"]] = {
            "color": entry["color"].lstrip("#"),
            "description": entry.get("description", ""),
        }
    return labels


def load_desired_labels() -> list[dict[str, str]]:
    if not LABELS_FILE.exists():
        print(f"Labels file not found: {LABELS_FILE}", file=sys.stderr)
        sys.exit(1)

    with LABELS_FILE.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, list):
        print("Expected a list of label entries in labels.yml", file=sys.stderr)
        sys.exit(1)

    return data


def sync_labels(dry_run: bool = False, prune: bool = False) -> None:
    desired = load_desired_labels()
    existing = get_existing_labels()

    desired_names = {lbl["name"] for lbl in desired}

    created = 0
    updated = 0

    for lbl in desired:
        name = lbl["name"]
        color = lbl["color"].lstrip("#")
        description = lbl.get("description", "")

        if name not in existing:
            print(f"  + {name}")
            created += 1
            if not dry_run:
                result = gh(
                    "label",
                    "create",
                    name,
                    "--color",
                    color,
                    "--description",
                    description,
                    check=False,
                )
                if result.returncode != 0:
                    gh("label", "edit", name, "--color", color, "--description", description)
        else:
            ex = existing[name]
            if ex["color"] != color or ex["description"] != description:
                print(f"  ~ {name} (color/description changed)")
                updated += 1
                if not dry_run:
                    gh(
                        "label",
                        "edit",
                        name,
                        "--color",
                        color,
                        "--description",
                        description,
                    )

    deleted = 0
    if prune:
        for name in existing:
            if name not in desired_names:
                print(f"  - {name}")
                deleted += 1
                if not dry_run:
                    gh("label", "delete", name, "--yes")

    action = "Would sync" if dry_run else "Synced"
    print(f"\n{action}: {created} created, {updated} updated, {deleted} deleted")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync GitHub labels from .github/labels.yml")
    parser.add_argument("--prune", action="store_true", help="Delete labels not in config")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changes")
    args = parser.parse_args()
    sync_labels(dry_run=args.dry_run, prune=args.prune)


if __name__ == "__main__":
    main()
