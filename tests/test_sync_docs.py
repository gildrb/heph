from __future__ import annotations

import os
from pathlib import Path
from xml.etree import ElementTree as ET

from scripts import sync_docs


def test_replace_managed_block_updates_named_section() -> None:
    text = "\n".join(
        [
            "before",
            "<!-- sync-docs:demo:start -->",
            "old content",
            "<!-- sync-docs:demo:end -->",
            "after",
        ]
    )

    updated = sync_docs.replace_managed_block(text, "demo", "new content")

    assert updated == "\n".join(
        [
            "before",
            "<!-- sync-docs:demo:start -->",
            "new content",
            "<!-- sync-docs:demo:end -->",
            "after",
        ]
    )


def test_lint_legacy_commands_flags_stale_refs(tmp_path: Path) -> None:
    doc = tmp_path / "guide.md"
    doc.write_text(
        "Use `hephaion start` if you want to launch the app.\nThen run `heph source reindex`.\n",
        encoding="utf-8",
    )

    errors = sync_docs.lint_legacy_commands(tmp_path)

    assert any("hephaion` or `hephaion <name-or-path>`" in error for error in errors)
    assert any("materials index" in error for error in errors)


def test_collect_docs_model_reads_live_surfaces() -> None:
    model = sync_docs.collect_docs_model(sync_docs.ROOT)

    assert model.short_command == "heph"
    assert model.long_command == "hephaion"
    assert any(
        command.command == "heph materials index <path>"
        for command in model.cli_reference_commands
    )
    assert any(command.command == "heph index [path]" for command in model.cli_reference_commands)
    assert not any("reindex" in command.command for command in model.cli_reference_commands)
    assert not any("heph source" in command.command for command in model.cli_reference_commands)
    assert any(command.command == "/vocabulary" for command in model.slash_commands)
    assert any(command.command == "/materials" for command in model.slash_commands)
    assert any(command.command == "/keymap" for command in model.slash_commands)
    assert not any(command.command == "/persona" for command in model.slash_commands)
    assert not any(command.command == "/edit" for command in model.slash_commands)
    assert any(shortcut.keys == "ctrl+a" for shortcut in model.keyboard_shortcuts)
    assert any(shortcut.keys == "ctrl+o" for shortcut in model.keyboard_shortcuts)
    assert not any(
        shortcut.keys in {"alt+m", "f4", "ctrl+t"} for shortcut in model.keyboard_shortcuts
    )
    assert any(env.name == "HEPHAION_POSTHOG_PROJECT_TOKEN" for env in model.env_vars)


def test_repository_docs_are_synced() -> None:
    targets = sync_docs.render_targets(sync_docs.ROOT)

    for target in targets:
        assert target.path.read_text(encoding="utf-8") == target.content


def test_readme_logo_is_repo_owned_svg_asset() -> None:
    assert sync_docs.README_LOGO_PATH.is_file()
    ET.parse(sync_docs.README_LOGO_PATH)

    root_readme = sync_docs.README_PATH
    root_logo_path = os.path.relpath(sync_docs.README_LOGO_PATH, root_readme.parent)
    root_text = root_readme.read_text(encoding="utf-8")
    assert f'src="{Path(root_logo_path).as_posix()}"' in root_text

    package_readmes = (
        sync_docs.ROOT / "packages" / "ai" / "README.md",
        sync_docs.ROOT / "packages" / "extensions" / "README.md",
        sync_docs.ROOT / "packages" / "heph" / "README.md",
        sync_docs.ROOT / "packages" / "hephaion" / "README.md",
        sync_docs.ROOT / "packages" / "interfaces" / "README.md",
    )
    for readme in package_readmes:
        text = readme.read_text(encoding="utf-8")
        assert f'src="{sync_docs.README_LOGO_RAW_URL}"' in text
        assert "https://gildrb.github.io/heph/logo-auto.svg" not in text
