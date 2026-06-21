from __future__ import annotations

import importlib.metadata
import importlib.util


def _module_is_importable(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except ModuleNotFoundError:
        return False


def test_moved_import_paths_are_not_compatibility_shimmed() -> None:
    moved_modules = (
        "cli",
        "commands",
        "heph_ai",
        "heph_ai.providers",
        "heph_ai.runtime",
        "heph_extensions",
        "heph_interfaces",
        "heph_interfaces.terminal",
        "heph_interfaces.tui",
        "providers",
        "runtime",
        "self_knowledge",
    )

    for module_name in moved_modules:
        assert not _module_is_importable(module_name)


def test_package_concern_modules_are_importable() -> None:
    concern_modules = (
        "ai",
        "ai.providers",
        "ai.runtime",
        "extensions",
        "extensions.contracts",
        "heph",
        "heph.cli",
        "heph.commands",
        "hephaion",
        "hephaion.agent",
        "hephaion.chat",
        "interfaces",
        "interfaces.terminal",
        "interfaces.tui",
    )

    for module_name in concern_modules:
        assert _module_is_importable(module_name)


def test_heph_and_hephaion_console_commands_share_heph_entrypoint() -> None:
    scripts = {
        entry_point.name: entry_point.value
        for entry_point in importlib.metadata.entry_points(group="console_scripts")
        if entry_point.name in {"heph", "hephaion"}
    }

    assert scripts == {
        "heph": "heph.cli.main:main",
        "hephaion": "heph.cli.main:main",
    }
