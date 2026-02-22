"""CLI commands for parameter profile management."""

from __future__ import annotations

import argparse


def _cmd_parameters_list(args: argparse.Namespace) -> None:
    print("[todo] parameters list")


def _cmd_parameters_set(args: argparse.Namespace) -> None:
    print(f"[todo] parameters set {args.key}={args.value}")


def _cmd_parameters_save(args: argparse.Namespace) -> None:
    print(f"[todo] parameters save name={args.name}")


def register_parameters_commands(subparsers) -> None:
    parameters = subparsers.add_parser("parameters", help="Manage model parameters.")
    params_sub = parameters.add_subparsers(dest="parameters_command", required=True)

    list_cmd = params_sub.add_parser("list", help="List saved parameter profiles.")
    list_cmd.set_defaults(handler=_cmd_parameters_list)

    set_cmd = params_sub.add_parser("set", help="Set one parameter value.")
    set_cmd.add_argument("key", help="Parameter name.")
    set_cmd.add_argument("value", help="Parameter value.")
    set_cmd.set_defaults(handler=_cmd_parameters_set)

    save = params_sub.add_parser("save", help="Save current parameters as a profile.")
    save.add_argument("name", help="Profile name.")
    save.set_defaults(handler=_cmd_parameters_save)
