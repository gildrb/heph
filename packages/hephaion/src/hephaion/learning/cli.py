"""CLI commands for local harness policy training."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hephaion.armory.storage import ArmoryError, normalize_path, validate
from hephaion.learning.training import train_attempt_policy


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    learning = subparsers.add_parser(
        "learning",
        help="Train and inspect local harness policy artifacts.",
    )
    learning_sub = learning.add_subparsers(dest="learning_command", required=True)
    train = learning_sub.add_parser(
        "train",
        help="Train a local harness action policy from replay data.",
    )
    train.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the armory folder. Defaults to the current directory.",
    )
    train.add_argument(
        "--dataset",
        action="append",
        default=[],
        help="JSONL replay dataset. Repeat to combine datasets.",
    )
    train.add_argument(
        "--no-local",
        action="store_true",
        help="Do not include armory-local replay attempts.",
    )
    train.add_argument(
        "--backend",
        choices=("table",),
        default="table",
        help="Training backend. Only the dependency-free table backend is supported.",
    )
    train.add_argument(
        "--promote",
        action="store_true",
        help="Promote only when held-out gates beat the static fallback.",
    )
    train.set_defaults(handler=_cmd_learning_train)


def _cmd_learning_train(args: argparse.Namespace) -> None:
    armory_path = _validated_armory_path(args.path)
    dataset_paths = tuple(Path(path).expanduser() for path in args.dataset)
    try:
        report = train_attempt_policy(
            armory_path=armory_path,
            dataset_paths=dataset_paths,
            include_local=not args.no_local,
            backend=args.backend,
            promote=args.promote,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))


def _validated_armory_path(path: str) -> Path:
    try:
        armory_path = normalize_path(path)
        validate(armory_path)
    except (ArmoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    return armory_path
