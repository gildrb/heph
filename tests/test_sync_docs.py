from __future__ import annotations

import re
import tomllib
from pathlib import Path
from xml.etree import ElementTree as ET

from scripts import sync_docs

_TEXT_SUFFIXES = frozenset({".json", ".md", ".py", ".toml", ".yaml", ".yml"})
_TEXT_SCAN_ROOTS = (
    sync_docs.ROOT / ".devcontainer",
    sync_docs.ROOT / ".github",
    sync_docs.ROOT / "docs",
    sync_docs.ROOT / "packages",
    sync_docs.ROOT / "scripts",
    sync_docs.ROOT / "tests",
)
_TEXT_SCAN_FILES = (
    sync_docs.ROOT / ".gitleaks.toml",
    sync_docs.ROOT / "CONTRIBUTING.md",
    sync_docs.ROOT / "README.md",
    sync_docs.ROOT / "SECURITY.md",
    sync_docs.ROOT / "pyproject.toml",
    sync_docs.ROOT / "vulture-whitelist.py",
)
_PRODUCT_DECLARATION = "Heph is the " + "product"
_MODEL_HARNESS_DECLARATION = "selected model " + "plus"
_PUBLIC_NAMING_PATTERNS = (
    (
        re.compile(r"\btogether\s+they\s+are\s+Heph\b", flags=re.IGNORECASE),
        "Let the app name stand on its own in public copy.",
    ),
    (
        re.compile(rf"\b{_PRODUCT_DECLARATION}\b"),
        "Use direct descriptions of what Heph does.",
    ),
    (
        re.compile(rf"\b{_MODEL_HARNESS_DECLARATION}\b"),
        "Use direct descriptions of what Heph does.",
    ),
)


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


def test_lint_legacy_commands_flags_stale_refs(tmp_path: Path) -> None:
    doc = tmp_path / "guide.md"
    doc.write_text(
        "Use `harness start` if you want to launch the app.\nThen run `heph source reindex`.\n",
        encoding="utf-8",
    )

    errors = sync_docs.lint_legacy_commands(tmp_path)

    assert any("heph` or `heph <path>`" in error for error in errors)
    assert any("materials index" in error for error in errors)


def test_collect_docs_model_reads_live_surfaces() -> None:
    model = sync_docs.collect_docs_model(sync_docs.ROOT)

    assert model.short_command == "heph"
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
    shortcut_keys = {shortcut.keys for shortcut in model.keyboard_shortcuts}
    assert {"ctrl+p", "ctrl+a", "ctrl+o"} <= shortcut_keys
    assert not any(
        _shortcut_uses_function_key(shortcut.keys) for shortcut in model.keyboard_shortcuts
    )
    assert not any(
        shortcut.keys in {"alt+m", "f4", "ctrl+t"} for shortcut in model.keyboard_shortcuts
    )
    assert any(env.name == "HARNESS_POSTHOG_PROJECT_TOKEN" for env in model.env_vars)


def test_repository_docs_are_synced() -> None:
    targets = sync_docs.render_targets(sync_docs.ROOT)

    for target in targets:
        assert target.path.read_text(encoding="utf-8") == target.content


def test_public_copy_uses_heph_naming() -> None:
    paths = set(_TEXT_SCAN_FILES)
    for root in _TEXT_SCAN_ROOTS:
        paths.update(path for path in root.rglob("*") if path.suffix in _TEXT_SUFFIXES)

    errors: list[str] = []
    for path in sorted(paths):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern, message in _PUBLIC_NAMING_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path.relative_to(sync_docs.ROOT)}: {message}")

    assert not errors, "\n".join(errors)


def test_text_files_do_not_use_long_dash_character() -> None:
    long_dash = chr(0x2014)
    paths = set(_TEXT_SCAN_FILES)
    for root in _TEXT_SCAN_ROOTS:
        paths.update(path for path in root.rglob("*") if path.suffix in _TEXT_SUFFIXES)

    errors: list[str] = []
    for path in sorted(paths):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if long_dash in line:
                errors.append(f"{path.relative_to(sync_docs.ROOT)}:{line_number}")

    assert not errors, "\n".join(errors)


def test_readme_logo_is_repo_owned_svg_asset() -> None:
    assert sync_docs.README_LOGO_PATH.is_file()
    ET.parse(sync_docs.README_LOGO_PATH)

    logo_text = sync_docs.README_LOGO_PATH.read_text(encoding="utf-8")
    assert "prefers-color-scheme: dark" in logo_text
    assert "fill: #000000" in logo_text
    assert "fill: #ffffff" in logo_text

    root_readme = sync_docs.README_PATH
    root_text = root_readme.read_text(encoding="utf-8")
    assert '<h1 align="center">Heph</h1>' not in root_text
    assert 'src="assets/logo-auto.svg"' in root_text
    assert f'width="{sync_docs.README_LOGO_WIDTH}"' in root_text
    assert "<strong>A local document agent for accurate, cited answers.</strong><br>" in root_text
    assert "Heph indexes armory files, answers from them, and shows citations.<br>" in root_text
    assert (
        "Armory materials and Heph state stay local; hosted providers receive "
        "the selected context needed to answer."
    ) in root_text
    assert "Heph CLI is a local document agent." not in root_text
    assert root_text.index('src="assets/logo-auto.svg"') < root_text.index(
        "A local document agent for accurate, cited answers."
    )
    assert root_text.index(
        "A local document agent for accurate, cited answers."
    ) < root_text.index('src="assets/app-screenshot.png')
    assert "img.shields.io" not in root_text
    assert '<a href="#installation"><img alt="uv"' not in root_text
    assert '<a href="https://docs.astral.sh/uv/"><img alt="uv"' not in root_text
    screenshot_cache_key = sync_docs._asset_cache_key(sync_docs.README_SCREENSHOT_PATH)
    assert f'href="{sync_docs.README_SCREENSHOT_RAW_URL}?v={screenshot_cache_key}"' in root_text
    assert f'src="assets/app-screenshot.png?v={screenshot_cache_key}"' in root_text
    assert "## Installation" in root_text
    assert "### Using UV (recommended)" in root_text
    assert "## The armory is the interface" not in root_text
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
    assert "# Inside Heph, run /login if needed" not in root_text
    assert "heph trust ~/.armories/[name]" not in root_text
    assert "# Start the JSONL SDK service for native clients and automation" not in root_text
    assert "## Commands" not in root_text
    assert "Inside Heph:" not in root_text
    assert "If you do not use uv:" not in root_text
    assert "uv tool upgrade heph" not in root_text
    assert "uv tool install git+https://github.com/gildrb/heph" not in root_text
    assert "## Models" not in root_text
    assert "## License" not in root_text
    assert "[Getting started](docs/getting-started.md)" in root_text
    assert "[docs/getting-started.md](docs/getting-started.md)" not in root_text
    assert "[docs/armories.md](docs/armories.md)" not in root_text

    docs_index_text = sync_docs.DOCS_INDEX_PATH.read_text(encoding="utf-8")
    assert '<h1 align="center">Heph</h1>' not in docs_index_text
    assert 'src="../assets/logo-auto.svg"' in docs_index_text
    assert f'width="{sync_docs.README_LOGO_WIDTH}"' in docs_index_text
    assert (
        "<strong>A local document agent for accurate, cited answers.</strong><br>"
        in docs_index_text
    )
    assert (
        "Heph indexes armory files, answers from them, and shows citations.<br>" in docs_index_text
    )
    assert (
        "Armory materials and Heph state stay local; hosted providers receive "
        "the selected context needed to answer."
    ) in docs_index_text
    assert "Heph CLI is a local document agent." not in docs_index_text
    assert "img.shields.io" not in docs_index_text
    assert '<a href="#installation"><img alt="uv"' not in docs_index_text
    assert '<a href="https://docs.astral.sh/uv/"><img alt="uv"' not in docs_index_text
    assert (
        f'href="{sync_docs.README_SCREENSHOT_RAW_URL}?v={screenshot_cache_key}"' in docs_index_text
    )
    assert f'src="../assets/app-screenshot.png?v={screenshot_cache_key}"' in docs_index_text
    assert "## Installation" in docs_index_text
    assert "### Using UV (recommended)" in docs_index_text
    assert "## The armory is the interface" not in docs_index_text
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
    assert "# Inside Heph, run /login if needed" not in docs_index_text
    assert "heph trust ~/.armories/[name]" not in docs_index_text
    assert "# Start the JSONL SDK service for native clients and automation" not in docs_index_text
    assert "## Commands" not in docs_index_text
    assert "Inside Heph:" not in docs_index_text
    assert "If you do not use uv:" not in docs_index_text
    assert "uv tool upgrade heph" not in docs_index_text
    assert "uv tool install git+https://github.com/gildrb/heph" not in docs_index_text
    assert "## Models" not in docs_index_text
    assert "## Next Steps" not in docs_index_text
    assert "[Getting started](getting-started.md)" in docs_index_text
    assert "[getting-started.md](getting-started.md)" not in docs_index_text
    assert "[armories.md](armories.md)" not in docs_index_text

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
        assert "https://gildrb.github.io/heph/logo-auto.svg" not in text

    heph_readme_text = (sync_docs.ROOT / "packages" / "heph" / "README.md").read_text(
        encoding="utf-8"
    )
    assert "<strong>A local document agent for accurate, cited answers.</strong><br>" in (
        heph_readme_text
    )
    assert "Heph indexes armory files, answers from them, and shows citations.<br>" in (
        heph_readme_text
    )
    assert "Heph CLI is a local document agent." not in heph_readme_text

    heph_project = tomllib.loads(sync_docs.HEPH_PYPROJECT_PATH.read_text(encoding="utf-8"))[
        "project"
    ]
    assert heph_project["description"] == "Local document agent for accurate, cited answers."
