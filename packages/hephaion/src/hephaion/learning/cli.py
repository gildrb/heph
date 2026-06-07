"""CLI commands for local harness policy training."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hephaion.armory.storage import ArmoryError, normalize_path, validate
from hephaion.learning.automation import AutoTrainingConfig, maybe_auto_train_attempt_policy
from hephaion.learning.constellation import (
    CONSTELLATION_EXPERIMENTS_PATH,
    export_armory_constellation,
)
from hephaion.learning.training import train_attempt_policy


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    learning = subparsers.add_parser(
        "learning",
        help="Train and inspect local harness policy artifacts.",
    )
    learning_sub = learning.add_subparsers(dest="learning_command", required=True)
    _register_train_parser(learning_sub)
    _register_auto_train_parser(learning_sub)
    _register_constellation_parser(learning_sub)
    learning_sub.metavar = "{train,auto-train,constellation-export}"


def _register_train_parser(
    learning_sub: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
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
        choices=("pufferlib",),
        default="pufferlib",
        help="Training backend. PufferLib is the supported local RL trainer.",
    )
    train.add_argument(
        "--promote",
        action="store_true",
        help="Promote only when held-out gates beat the static fallback.",
    )
    train.set_defaults(handler=_cmd_learning_train)


def _register_auto_train_parser(
    learning_sub: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    auto_train = learning_sub.add_parser(
        "auto-train",
        help="Train and promote when enough new local attempts are available.",
    )
    auto_train.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the armory folder. Defaults to the current directory.",
    )
    auto_train.add_argument(
        "--dataset",
        action="append",
        default=[],
        help="Additional JSONL replay dataset. Repeat to combine datasets.",
    )
    auto_train.add_argument(
        "--no-public-fixture",
        action="store_true",
        help="Use only armory-local attempts and explicitly supplied datasets.",
    )
    auto_train.add_argument(
        "--min-total-attempts",
        type=int,
        default=8,
        help="Minimum local attempts before automated training can run.",
    )
    auto_train.add_argument(
        "--min-new-attempts",
        type=int,
        default=20,
        help="Minimum local attempts added since the last automated training run.",
    )
    auto_train.set_defaults(handler=_cmd_learning_auto_train)


def _register_constellation_parser(
    learning_sub: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    constellation = learning_sub.add_parser(
        "constellation-export",
        help="Export local learning attempts for PufferLib Constellation.",
    )
    constellation.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the armory folder. Defaults to the current directory.",
    )
    constellation.add_argument(
        "--output",
        default=None,
        help=(
            "Output experiments.json path. Defaults to the armory-local "
            f"{CONSTELLATION_EXPERIMENTS_PATH}."
        ),
    )
    constellation.add_argument(
        "--env-name",
        help="Top-level Constellation group name. Defaults to the armory folder name.",
    )
    constellation.set_defaults(handler=_cmd_learning_constellation_export)


def _cmd_learning_train(args: argparse.Namespace) -> None:
    armory_path = _validated_armory_path(args.path)
    dataset_paths = tuple(Path(path).expanduser() for path in args.dataset) or None
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


def _cmd_learning_auto_train(args: argparse.Namespace) -> None:
    armory_path = _validated_armory_path(args.path)
    dataset_paths = tuple(Path(path).expanduser() for path in args.dataset)
    try:
        decision = maybe_auto_train_attempt_policy(
            armory_path,
            config=AutoTrainingConfig(
                min_total_attempts=max(1, args.min_total_attempts),
                min_new_attempts=max(1, args.min_new_attempts),
                include_public_fixture=not args.no_public_fixture,
                dataset_paths=dataset_paths,
            ),
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(json.dumps(decision.to_dict(), indent=2, sort_keys=True))


def _cmd_learning_constellation_export(args: argparse.Namespace) -> None:
    armory_path = _validated_armory_path(args.path)
    output_path = Path(args.output).expanduser() if args.output else None
    try:
        export = export_armory_constellation(
            armory_path,
            output_path=output_path,
            env_name=args.env_name,
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(json.dumps(export.to_dict(), indent=2, sort_keys=True))


def _validated_armory_path(path: str) -> Path:
    try:
        armory_path = normalize_path(path)
        validate(armory_path)
    except (ArmoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    return armory_path
