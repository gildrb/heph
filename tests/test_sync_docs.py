from __future__ import annotations

import tomllib
from xml.etree import ElementTree as ET

from scripts import sync_docs


def _shortcut_uses_function_key(keys: str) -> bool:
    for key in keys.split("/"):
        base_key = key.rsplit("+", maxsplit=1)[-1]
        if base_key.startswith("f") and base_key[1:].isdigit():
            return True
    return False


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


def test_collect_docs_model_reads_live_surfaces() -> None:
    model = sync_docs.collect_docs_model(sync_docs.ROOT)

    assert model.short_command == "heph"
    assert any(
        command.command == "heph materials index <path>"
        for command in model.cli_reference_commands
    )
    assert any(command.command == "heph index [path]" for command in model.cli_reference_commands)
    assert any(command.command == "/vocabulary" for command in model.slash_commands)
    assert any(command.command == "/materials" for command in model.slash_commands)
    assert any(command.command == "/keymap" for command in model.slash_commands)
    shortcut_keys = {shortcut.keys for shortcut in model.keyboard_shortcuts}
    assert {"ctrl+p", "ctrl+a", "ctrl+o"} <= shortcut_keys
    assert all(not _shortcut_uses_function_key(shortcut) for shortcut in shortcut_keys)


def test_repository_docs_are_synced() -> None:
    targets = sync_docs.render_targets(sync_docs.ROOT)

    for target in targets:
        assert target.path.read_text(encoding="utf-8") == target.content


def test_readme_logo_is_repo_owned_svg_asset() -> None:
    assert sync_docs.README_LOGO_PATH.is_file()
    ET.parse(sync_docs.README_LOGO_PATH)

    logo_text = sync_docs.README_LOGO_PATH.read_text(encoding="utf-8")
    assert "prefers-color-scheme: dark" in logo_text
    assert "fill: #000000" in logo_text
    assert "fill: #ffffff" in logo_text

    root_readme = sync_docs.README_PATH
    root_text = root_readme.read_text(encoding="utf-8")
    assert 'src="assets/logo-auto.svg"' in root_text
    assert f'width="{sync_docs.README_LOGO_WIDTH}"' in root_text
    root_hero = (
        '<p align="center">\n  Local agent for accurate, cited answers from your files\n</p>'
    )
    assert root_hero in root_text
    hero_text = "Local agent for accurate, cited answers from your files"
    assert root_text.index('src="assets/logo-auto.svg"') < root_text.index(hero_text)
    assert root_text.index(hero_text) < root_text.index('src="assets/app-screenshot.png')
    screenshot_cache_key = sync_docs._asset_cache_key(sync_docs.README_SCREENSHOT_PATH)
    assert f'href="{sync_docs.README_SCREENSHOT_RAW_URL}?v={screenshot_cache_key}"' in root_text
    assert f'src="assets/app-screenshot.png?v={screenshot_cache_key}"' in root_text
    assert "## Installation" in root_text
    assert "### Using UV (recommended)" in root_text
    assert "## Armory layout" in root_text
    assert "An armory is a normal folder:" in root_text
    assert (
        "`materials/` holds files Heph can index and cite. `.harness/` holds local state:"
        in root_text
    )
    assert root_text.index("## Quick Start") < root_text.index("## Armory layout")
    assert root_text.index("## Armory layout") < root_text.index("## Installation")
    assert "curl -LsSf https://astral.sh/uv/install.sh | sh" in root_text
    assert "Install UV:" in root_text
    assert "Then Heph:" in root_text
    assert "### Using Pip" in root_text
    assert "# Create an armory for your files" in root_text
    assert "# Add materials that Heph can answer from" in root_text
    assert "# Start Heph in that armory" in root_text
    root_docs = (
        "## Docs\n\n"
        "[Getting started](docs/getting-started.md)<br>\n"
        "[Armories](docs/armories.md)<br>\n"
        "[CLI reference](docs/cli-reference.md)<br>\n"
        "[Configuration](docs/configuration.md)<br>\n"
        "[Models](docs/models.md)<br>\n"
        "[Trust and ownership](docs/trust.md)<br>\n"
        "[Privacy](docs/privacy.md)<br>\n"
        "[Architecture](docs/architecture.md)<br>\n"
        "[SDK](docs/sdk.md)<br>\n"
        "[Troubleshooting](docs/troubleshooting.md)<br>\n"
        "[Developers](docs/developers.md)<br>\n"
        "[Runbooks](docs/runbooks.md)"
    )
    assert root_docs in root_text

    docs_index_text = sync_docs.DOCS_INDEX_PATH.read_text(encoding="utf-8")
    assert 'src="../assets/logo-auto.svg"' in docs_index_text
    assert f'width="{sync_docs.README_LOGO_WIDTH}"' in docs_index_text
    assert root_hero in docs_index_text
    assert (
        f'href="{sync_docs.README_SCREENSHOT_RAW_URL}?v={screenshot_cache_key}"' in docs_index_text
    )
    assert f'src="../assets/app-screenshot.png?v={screenshot_cache_key}"' in docs_index_text
    assert "## Installation" in docs_index_text
    assert "### Using UV (recommended)" in docs_index_text
    assert "## Armory layout" in docs_index_text
    assert "An armory is a normal folder:" in docs_index_text
    assert (
        "`materials/` holds files Heph can index and cite. `.harness/` holds local state:"
        in docs_index_text
    )
    assert docs_index_text.index("## Quick Start") < docs_index_text.index("## Armory layout")
    assert docs_index_text.index("## Armory layout") < docs_index_text.index("## Installation")
    assert "curl -LsSf https://astral.sh/uv/install.sh | sh" in docs_index_text
    assert "Install UV:" in docs_index_text
    assert "Then Heph:" in docs_index_text
    assert "### Using Pip" in docs_index_text
    assert "# Create an armory for your files" in docs_index_text
    assert "# Add materials that Heph can answer from" in docs_index_text
    assert "# Start Heph in that armory" in docs_index_text
    docs_index_docs = (
        "## Docs\n\n"
        "[Getting started](getting-started.md)<br>\n"
        "[Armories](armories.md)<br>\n"
        "[CLI reference](cli-reference.md)<br>\n"
        "[Configuration](configuration.md)<br>\n"
        "[Models](models.md)<br>\n"
        "[Trust and ownership](trust.md)<br>\n"
        "[Privacy](privacy.md)<br>\n"
        "[Architecture](architecture.md)<br>\n"
        "[SDK](sdk.md)<br>\n"
        "[Troubleshooting](troubleshooting.md)<br>\n"
        "[Developers](developers.md)<br>\n"
        "[Runbooks](runbooks.md)<br>\n"
        "[Contributing](../CONTRIBUTING.md)"
    )
    assert docs_index_docs in docs_index_text

    package_readmes = (
        sync_docs.ROOT / "packages" / "ai" / "README.md",
        sync_docs.ROOT / "packages" / "extensions" / "README.md",
        sync_docs.ROOT / "packages" / "heph" / "README.md",
        sync_docs.ROOT / "packages" / "harness" / "README.md",
        sync_docs.ROOT / "packages" / "interfaces" / "README.md",
    )
    for readme in package_readmes:
        text = readme.read_text(encoding="utf-8")
        assert f'src="{sync_docs.README_LOGO_RAW_URL}"' in text
        assert f'width="{sync_docs.README_LOGO_WIDTH}"' in text

    heph_readme_text = (sync_docs.ROOT / "packages" / "heph" / "README.md").read_text(
        encoding="utf-8"
    )
    assert root_hero in heph_readme_text

    heph_project = tomllib.loads(sync_docs.HEPH_PYPROJECT_PATH.read_text(encoding="utf-8"))[
        "project"
    ]
    assert heph_project["description"] == "Local document agent for accurate, cited answers."
