"""Thin wrapper entrypoints for alternate command names."""

from hephaistos.app.cli import main as hephaistos_main


def main() -> None:
    hephaistos_main()

