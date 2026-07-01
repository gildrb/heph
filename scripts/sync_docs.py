"""Synchronize repo-native docs from code-backed sources."""

from __future__ import annotations

import argparse
import argparse as _argparse
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from ai.logging import LOG_FILE_ENV, LOG_FORMAT_ENV, LOG_LEVEL_ENV
from ai.providers.config import default_config
from ai.providers.keyring_store import GLOBAL_API_KEY_ENV
from harness.chat.session import ARMORY_PLUGINS_TRUST_ENV
from harness.memory.extract import EXTRACTION_MODEL_ENV
from harness.parameters import cli as parameters_cli
from harness.privacy.consent import (
    ANALYTICS_ENABLED_ENV,
    CRASH_REPORTS_ENABLED_ENV,
    POSTHOG_HOST_ENV,
    POSTHOG_TOKEN_ENV,
    SENTRY_DSN_ENV,
)
from harness.rag.config import EMBED_MODEL_ENV, RERANK_MODEL_ENV
from heph.cli.main import build_parser
from heph.commands import get_registry
from interfaces.tui.keybinds import keybind_keys_text, tui_keybinds
from interfaces.tui.slash_command import TUI_ONLY_COMMAND_SUGGESTIONS

ROOT: Final[Path] = Path(__file__).resolve().parent.parent
PYPROJECT_PATH: Final[Path] = ROOT / "pyproject.toml"
HEPH_PYPROJECT_PATH: Final[Path] = ROOT / "packages" / "heph" / "pyproject.toml"
README_PATH: Final[Path] = ROOT / "README.md"
DOCS_INDEX_PATH: Final[Path] = ROOT / "docs" / "index.md"
README_LOGO_PATH: Final[Path] = ROOT / "assets" / "logo-auto.svg"
README_LOGO_RAW_URL: Final[str] = (
    "https://raw.githubusercontent.com/gildrb/heph/main/assets/logo-auto.svg"
)
README_LOGO_WIDTH: Final[int] = 320
README_SCREENSHOT_PATH: Final[Path] = ROOT / "assets" / "app-screenshot.png"
CLI_REFERENCE_PATH: Final[Path] = ROOT / "docs" / "cli-reference.md"
ARCHITECTURE_PATH: Final[Path] = ROOT / "docs" / "architecture.md"

GENERATED_NOTICE: Final[str] = "<!-- Managed by scripts/sync_docs.py. Do not edit directly. -->"
ARCHITECTURE_BLOCK_NAME: Final[str] = "privacy-diagnostics-architecture"

PLACEHOLDER_RE: Final[re.Pattern[str]] = re.compile(r"\[\[([A-Z0-9_]+)\]\]")
BLOCK_START_TEMPLATE: Final[str] = "<!-- sync-docs:{name}:start -->"
BLOCK_END_TEMPLATE: Final[str] = "<!-- sync-docs:{name}:end -->"

GENERATED_DOCS: Final[frozenset[Path]] = frozenset(
    {
        README_PATH,
        DOCS_INDEX_PATH,
        CLI_REFERENCE_PATH,
    }
)
HOME_TEMPLATE: Final[str] = """\
[[GENERATED_NOTICE]]

[[README_LOGO_BLOCK]][[BADGES_BLOCK]]

Local document workspace for accurate, cited answers from files you keep in
normal folders. Heph indexes armory materials, cites retrieved evidence, and
keeps learning memory scoped to that armory.

[[README_SCREENSHOT_BLOCK]]

## Quick Start

[[QUICK_START_BLOCK]]

## The armory is the interface

A typical Heph armory has this structure:

[[ARMORY_LAYOUT_BLOCK]]

Heph reads `materials/`, writes local state under `.harness/`, and leaves the
armory portable. Read [[ARMORY_DOC_LINK]] for storage, indexing, and memory
details.

Copy or sync `.armories` to move work between machines; set provider credentials
again on each machine.

## Installation

> [!NOTE]
> Heph is currently in beta, so unexpected issues may occur. Please report them if
> they have not already been reported.

### Using UV (recommended)

Install UV:

[[UV_INSTALL_BLOCK]]

Then Heph:

[[INSTALL_BLOCK]]

### Using Pip

[[PIP_INSTALL_BLOCK]]

[[DOCS_SECTION]]

## Contributing

See [CONTRIBUTING.md]([[CONTRIBUTING_LINK]]) for local development, tests, and pull request
guidelines.

## Safety

Analytics and crash reporting are opt-in from `/settings`. Source and Git installs do
not enable hosted diagnostics by default.

Model-generated terminal commands are not exposed as a default agent tool. Explicit
`!` terminal escapes and armory plugins should only be used in armories you trust.

[[FOOTER_SECTION]]
"""
CLI_REFERENCE_TEMPLATE: Final[str] = """\
[[GENERATED_NOTICE]]

# CLI Reference

## CLI commands

[[CLI_COMMANDS_TABLE]]

`[[SHORT_COMMAND]]` is the canonical public command that starts the Heph agent.
Use `[[SHORT_COMMAND]] tui [path]` only when a script needs the explicit TUI subcommand.

## Slash commands

[[SLASH_COMMANDS_TABLE]]

## TUI keyboard shortcuts

The `/keymap` slash command opens the editable shortcut map inside Heph. Choose
an action, then select RECORD or press Enter before typing the new shortcut.
Use the visible RESET action on a shortcut, or RESET ALL KEYBINDS from the keymap
list, to restore defaults.
Some terminal and desktop shortcuts are reserved, so Heph rejects keys such as
`ctrl+c`, `ctrl+d`, `ctrl+m`, `ctrl+t`, `alt+m`, and function keys.
Default app-wide shortcuts avoid function keys and use two-key chords:
Commands `ctrl+p`, Armory `ctrl+a`, Materials `ctrl+o`, Search `ctrl+r`,
and Evidence `ctrl+g`.

[[KEYBOARD_SHORTCUTS_TABLE]]

## Environment variables

[[ENV_VARS_TABLE]]
"""
PRIVACY_DIAGNOSTICS_CONTRACT: Final[str] = (
    "PostHog is used only for anonymous, opt-in usage/error visibility for the\n"
    "maintainer. Sentry is used only for redacted, opt-in crash reporting. The\n"
    "public repository ships `packages/harness/src/harness/privacy/release.py` as a safe "
    "stub;\n"
    "official release builds inject privacy and diagnostics backend values during CI, and "
    "forks or custom\n"
    "builds can provide `HARNESS_POSTHOG_PROJECT_TOKEN`,\n"
    "`HARNESS_POSTHOG_HOST`, and `HARNESS_SENTRY_DSN`."
)
ARCHITECTURE_PRIVACY_DIAGNOSTICS: Final[str] = """\
## Privacy & Diagnostics

Heph keeps privacy-impacting diagnostics optional and maintainer-facing.
User-facing data, cache, prompt, and compute ownership terms live in
`docs/trust.md` and `docs/privacy.md`.

- `diagnostics.events` sends anonymous PostHog events only when a backend is
  configured and the user explicitly opts in.
- `diagnostics.crashes` sends redacted Sentry crash reports only when a
  backend is configured and the user explicitly opts in.
- `packages/harness/src/harness/privacy/release.py` is committed as a safe stub in the public
  repository. Official release and edge workflows overwrite it in CI before
  building artifacts.
- Source, editable, and Git installs stay bare by default. Forks and custom
  builds can wire their own endpoints with `HARNESS_POSTHOG_PROJECT_TOKEN`,
  `HARNESS_POSTHOG_HOST`, and `HARNESS_SENTRY_DSN`.
- Agents and contributors should preserve this split: diagnostics exist only for
  opt-in maintainer visibility into usage/errors and is never a required product
  dependency.
"""


@dataclass(frozen=True)
class CommandLine:
    command: str
    description: str


@dataclass(frozen=True)
class EnvVarDoc:
    name: str
    description: str


@dataclass(frozen=True)
class KeyboardShortcutDoc:
    keys: str
    action: str
    description: str


@dataclass(frozen=True)
class DocsModel:
    short_command: str
    scripts_entrypoint: str
    common_commands: tuple[CommandLine, ...]
    cli_reference_commands: tuple[CommandLine, ...]
    slash_commands: tuple[CommandLine, ...]
    keyboard_shortcuts: tuple[KeyboardShortcutDoc, ...]
    env_vars: tuple[EnvVarDoc, ...]
    privacy_diagnostics_contract: str
    architecture_privacy_diagnostics: str


@dataclass(frozen=True)
class SyncTarget:
    path: Path
    content: str


ENV_VAR_DESCRIPTIONS: Final[dict[str, str]] = {
    "HARNESS_BASE_URL": "Override the active API base URL.",
    "HARNESS_MODEL": "Override the active model.",
    "HARNESS_MAX_TOKENS": "Set the max output tokens per response.",
    "HARNESS_RAG_CONTEXT_BUDGET": "Set the token budget for retrieved context.",
    "HARNESS_FEATURE_FLAGS": "Comma-separated feature flags.",
    "HARNESS_PRIORITY_WEB_PREREQS": (
        "Enable optional web-backed prerequisite hints in priority reports."
    ),
    "HARNESS_ANALYTICS_ENABLED": "Override the saved analytics opt-in (`true`/`false`).",
    "HARNESS_API_KEY": "Global API key override that applies to any provider.",
    "HARNESS_ARMORY_HOME": (
        "Default parent folder for named armories (`~/.armories` by default)."
    ),
    "HARNESS_TRUST_ARMORY_PLUGINS": (
        "Allow trusted armories to load `.harness/tools/*.py` plugins."
    ),
    "HARNESS_CRASH_REPORTS_ENABLED": "Override the saved crash-report opt-in (`true`/`false`).",
    "HARNESS_EMBED_MODEL": "Override the embedding model used by retrieval.",
    "HARNESS_EXTRACTION_MODEL": "Override the model used for background memory extraction.",
    "HARNESS_LOG_FILE": "Append structured logs to a file when set.",
    "HARNESS_LOG_FORMAT": "Choose `json` or `text` logging output.",
    "HARNESS_LOG_LEVEL": (
        "Configure structured log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`)."
    ),
    "HARNESS_POSTHOG_HOST": "Supply a PostHog host for a custom or forked build.",
    "HARNESS_POSTHOG_PROJECT_TOKEN": (
        "Supply a PostHog project token for a custom or forked build."
    ),
    "HARNESS_RERANK_MODEL": "Override the reranker model when available.",
    "HARNESS_RTK_FALLBACK_ALLOWED": (
        "Set to `0` to fail closed when the optional RTK wrapper is unavailable."
    ),
    "HARNESS_SENTRY_DSN": "Supply a Sentry DSN for a custom or forked build.",
    "HARNESS_TEMPERATURE": "Override the generation temperature for chat responses.",
    "OPENAI_API_KEY": "API key for the OpenAI API provider.",
    "DEEPSEEK_API_KEY": "API key for the DeepSeek API provider.",
    "OPENROUTER_API_KEY": "API key for OpenRouter.",
    "ZAI_API_KEY": "API key for Z.AI / GLM.",
    "CUSTOM_API_KEY": "API key for the custom provider entry.",
}

CLI_COMMAND_DESCRIPTIONS: Final[dict[str, str]] = {
    "heph": "Open your current armory or plain chat.",
    "heph <name-or-path>": (
        "Open an armory by name from `~/.armories`, e.g. `heph gdp`, or by explicit path; "
        "empty armories open with a no-materials state."
    ),
    "heph armory init <name>": "Create a named armory in `~/.armories`.",
    "heph tui [path]": "Explicit alias for the default Textual TUI.",
    "heph update": "Update the active released Heph install.",
    "heph sdk serve": "Run the SDK JSONL stdio service for native clients.",
    "heph sdk capabilities": "Print the SDK capability contract as JSON.",
    "heph release status": ("Show installed package, official stable, and release channel state."),
    "heph chat ask --jsonl <path> [prompt]": (
        "Emit structured turn events as JSON Lines for audits."
    ),
    "heph health [path]": (
        "Check indexed materials for generic extraction problems; defaults to the current armory."
    ),
    "heph index [path]": "Build or refresh the materials index; defaults to the current armory.",
    "heph local search [query]": "Browse curated GGUF models.",
    "heph local install <repo-or-path>": (
        "Install a curated GGUF model or local `.gguf` path after confirmation, "
        "then activate it only if it passes Heph's tool-call probe."
    ),
    "heph local status": "Show managed llama.cpp cache, server, and installed-model status.",
    "heph local revalidate <model-id>": "Rerun the tool-call probe for an installed local model.",
    "heph local stop": "Stop the managed localhost llama.cpp server.",
    "heph trust [path]": "Show data, cache, prompt, and compute ownership.",
}

LEGACY_PATTERNS: Final[tuple[tuple[re.Pattern[str], str], ...]] = (
    (
        re.compile(r"\bheph\s+start\b"),
        "Use `heph` or `heph <path>` as the primary command.",
    ),
    (
        re.compile(r"\bharness\s+start\b"),
        "Use `heph` or `heph <path>` as the primary command.",
    ),
    (
        re.compile(r"\bsource\s+reindex\b"),
        "Use `materials index` because `materials` is the preferred CLI namespace "
        "and the subcommand is `index`.",
    ),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync repo docs from code-backed sources.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if generated docs or managed blocks are stale.",
    )
    return parser.parse_args(argv)


def load_pyproject(path: Path) -> dict[str, object]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_project_scripts(pyproject_path: Path) -> dict[str, str]:
    project_raw = load_pyproject(pyproject_path).get("project", {})
    if not isinstance(project_raw, dict):
        raise TypeError("pyproject.toml is missing [project].")
    project = cast("dict[str, object]", project_raw)
    scripts = project.get("scripts", {})
    if not isinstance(scripts, dict):
        raise TypeError("pyproject.toml is missing [project.scripts].")
    return {str(key): str(value) for key, value in scripts.items()}


def build_help_map(
    subparsers: _argparse._SubParsersAction[argparse.ArgumentParser],
) -> dict[str, str]:
    help_map: dict[str, str] = {}
    for action in subparsers._choices_actions:
        if not isinstance(action.dest, str):
            continue
        help_text = getattr(action, "help", "")
        if help_text == _argparse.SUPPRESS:
            continue
        help_map[action.dest] = str(help_text).strip()
    return help_map


def get_subparsers_action(
    parser: argparse.ArgumentParser,
) -> _argparse._SubParsersAction[argparse.ArgumentParser]:
    for action in parser._actions:
        if isinstance(action, _argparse._SubParsersAction):
            return cast("_argparse._SubParsersAction[argparse.ArgumentParser]", action)
    raise RuntimeError(f"Parser {parser.prog!r} does not define subcommands.")


def collect_cli_commands(short_command: str) -> tuple[CommandLine, ...]:
    parser = build_parser()
    subparsers = get_subparsers_action(parser)
    top_level = list(subparsers.choices.keys())

    required_visible = {
        "armory",
        "materials",
        "index",
        "health",
        "local",
        "update",
        "sdk",
        "release",
        "trust",
        "config",
    }
    if not required_visible.issubset(top_level):
        raise RuntimeError("The top-level CLI surface changed; update sync_docs.py.")
    if "chat" not in top_level:
        raise RuntimeError("Expected hidden `chat` automation command to exist.")

    armory_parser = subparsers.choices["armory"]
    materials_parser = subparsers.choices["materials"]
    config_parser = subparsers.choices["config"]
    local_parser = subparsers.choices["local"]
    sdk_parser = subparsers.choices["sdk"]
    release_parser = subparsers.choices["release"]
    chat_parser = subparsers.choices["chat"]

    armory_sub = get_subparsers_action(armory_parser)
    materials_sub = get_subparsers_action(materials_parser)
    config_sub = get_subparsers_action(config_parser)
    sdk_sub = get_subparsers_action(sdk_parser)
    release_sub = get_subparsers_action(release_parser)
    chat_sub = get_subparsers_action(chat_parser)

    armory_help = build_help_map(armory_sub)
    materials_help = build_help_map(materials_sub)
    config_help = build_help_map(config_sub)
    local_sub = get_subparsers_action(local_parser)
    local_help = build_help_map(local_sub)
    sdk_help = build_help_map(sdk_sub)
    release_help = build_help_map(release_sub)
    chat_help = build_help_map(chat_sub)

    return (
        CommandLine(short_command, CLI_COMMAND_DESCRIPTIONS[short_command]),
        CommandLine(
            f"{short_command} <name-or-path>",
            CLI_COMMAND_DESCRIPTIONS[f"{short_command} <name-or-path>"],
        ),
        CommandLine(f"{short_command} armory init <name>", armory_help["init"]),
        CommandLine(f"{short_command} armory open <path>", armory_help["open"]),
        CommandLine(f"{short_command} materials list <path>", materials_help["list"]),
        CommandLine(f"{short_command} materials count <path>", materials_help["count"]),
        CommandLine(f"{short_command} materials index <path>", materials_help["index"]),
        CommandLine(
            f"{short_command} index [path]", CLI_COMMAND_DESCRIPTIONS["heph index [path]"]
        ),
        CommandLine(
            f"{short_command} health [path]",
            CLI_COMMAND_DESCRIPTIONS["heph health [path]"],
        ),
        CommandLine(
            f"{short_command} local search [query]",
            CLI_COMMAND_DESCRIPTIONS["heph local search [query]"],
        ),
        CommandLine(
            f"{short_command} local install <repo-or-path>",
            CLI_COMMAND_DESCRIPTIONS["heph local install <repo-or-path>"],
        ),
        CommandLine(f"{short_command} local status", local_help["status"]),
        CommandLine(
            f"{short_command} local revalidate <model-id>",
            CLI_COMMAND_DESCRIPTIONS["heph local revalidate <model-id>"],
        ),
        CommandLine(f"{short_command} local stop", local_help["stop"]),
        CommandLine(f"{short_command} update", CLI_COMMAND_DESCRIPTIONS["heph update"]),
        CommandLine(f"{short_command} sdk serve", sdk_help["serve"]),
        CommandLine(f"{short_command} sdk capabilities", sdk_help["capabilities"]),
        CommandLine(f"{short_command} release status", release_help["status"]),
        CommandLine(
            f"{short_command} trust [path]",
            CLI_COMMAND_DESCRIPTIONS["heph trust [path]"],
        ),
        CommandLine(f"{short_command} config show", config_help["show"]),
        CommandLine(f"{short_command} config set <key> <value>", config_help["set"]),
        CommandLine(f"{short_command} chat ask <path> [prompt]", chat_help["ask"]),
        CommandLine(
            f"{short_command} chat ask --jsonl <path> [prompt]",
            CLI_COMMAND_DESCRIPTIONS["heph chat ask --jsonl <path> [prompt]"],
        ),
        CommandLine(
            f"{short_command} tui [path]",
            CLI_COMMAND_DESCRIPTIONS[f"{short_command} tui [path]"],
        ),
    )


def collect_common_commands(short_command: str) -> tuple[CommandLine, ...]:
    cli_commands = {item.command: item.description for item in collect_cli_commands(short_command)}
    selected = (
        short_command,
        f"{short_command} <name-or-path>",
        f"{short_command} armory init <name>",
        f"{short_command} armory open <path>",
        f"{short_command} materials list <path>",
        f"{short_command} materials count <path>",
        f"{short_command} materials index <path>",
        f"{short_command} index [path]",
        f"{short_command} health [path]",
        f"{short_command} local search [query]",
        f"{short_command} local install <repo-or-path>",
        f"{short_command} local status",
        f"{short_command} update",
        f"{short_command} release status",
        f"{short_command} trust [path]",
        f"{short_command} chat ask <path> [prompt]",
        f"{short_command} chat ask --jsonl <path> [prompt]",
        f"{short_command} tui [path]",
    )
    return tuple(CommandLine(command, cli_commands[command]) for command in selected)


def collect_slash_commands() -> tuple[CommandLine, ...]:
    registry = get_registry()
    registry_commands = tuple(
        CommandLine(
            f"/{suggestion.name}",
            suggestion.description,
        )
        for suggestion in registry.suggestions()
    )
    tui_only_commands = tuple(
        CommandLine(
            f"/{suggestion.name}",
            suggestion.description,
        )
        for suggestion in TUI_ONLY_COMMAND_SUGGESTIONS
    )
    return (*registry_commands, *tui_only_commands)


def collect_keyboard_shortcuts() -> tuple[KeyboardShortcutDoc, ...]:
    return tuple(
        KeyboardShortcutDoc(
            keys=keybind_keys_text(shortcut),
            action=shortcut.label,
            description=shortcut.description,
        )
        for shortcut in tui_keybinds()
    )


def collect_env_vars() -> tuple[EnvVarDoc, ...]:
    config_envs = [env for env in parameters_cli._CONFIG_KEY_TO_ENV.values() if env]
    provider_envs = [
        provider.api_key_env
        for provider in default_config().providers.values()
        if provider.api_key_env
    ]
    names = sorted(
        {
            GLOBAL_API_KEY_ENV,
            *config_envs,
            ANALYTICS_ENABLED_ENV,
            CRASH_REPORTS_ENABLED_ENV,
            POSTHOG_TOKEN_ENV,
            POSTHOG_HOST_ENV,
            SENTRY_DSN_ENV,
            LOG_LEVEL_ENV,
            LOG_FILE_ENV,
            LOG_FORMAT_ENV,
            EMBED_MODEL_ENV,
            EXTRACTION_MODEL_ENV,
            "HARNESS_PRIORITY_WEB_PREREQS",
            RERANK_MODEL_ENV,
            "HARNESS_RTK_FALLBACK_ALLOWED",
            ARMORY_PLUGINS_TRUST_ENV,
            *provider_envs,
        }
    )
    missing = [name for name in names if name not in ENV_VAR_DESCRIPTIONS]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing environment variable descriptions for: {joined}")
    return tuple(EnvVarDoc(name, ENV_VAR_DESCRIPTIONS[name]) for name in names)


def collect_docs_model(root: Path) -> DocsModel:
    scripts = load_project_scripts(root / "pyproject.toml")
    if not scripts:
        scripts = load_project_scripts(HEPH_PYPROJECT_PATH)
    short_command = "heph"
    if short_command not in scripts:
        raise RuntimeError("Expected `heph` entrypoint in pyproject.toml.")

    return DocsModel(
        short_command=short_command,
        scripts_entrypoint=scripts[short_command],
        common_commands=collect_common_commands(short_command),
        cli_reference_commands=collect_cli_commands(short_command),
        slash_commands=collect_slash_commands(),
        keyboard_shortcuts=collect_keyboard_shortcuts(),
        env_vars=collect_env_vars(),
        privacy_diagnostics_contract=PRIVACY_DIAGNOSTICS_CONTRACT,
        architecture_privacy_diagnostics=ARCHITECTURE_PRIVACY_DIAGNOSTICS.strip(),
    )


def render_template(template_name: str, template: str, replacements: dict[str, str]) -> str:
    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in replacements:
            raise RuntimeError(f"Missing template replacement for {key!r} in {template_name}.")
        return replacements[key]

    rendered = PLACEHOLDER_RE.sub(_replace, template)
    unresolved = PLACEHOLDER_RE.findall(rendered)
    if unresolved:
        unresolved_text = ", ".join(sorted(set(unresolved)))
        raise RuntimeError(f"Unresolved placeholders in {template_name}: {unresolved_text}")
    return rendered.strip() + "\n"


def render_command_block(commands: tuple[CommandLine, ...]) -> str:
    width = max(len(command.command) for command in commands)
    lines = [f"{command.command:<{width}}  {command.description}" for command in commands]
    return "```text\n" + "\n".join(lines) + "\n```"


def render_markdown_table(headers: tuple[str, str], rows: tuple[tuple[str, str], ...]) -> str:
    lines = [
        f"| {headers[0]} | {headers[1]} |",
        "|---|---|",
    ]
    lines.extend(f"| {left} | {right} |" for left, right in rows)
    return "\n".join(lines)


def render_install_block() -> str:
    return "```bash\nuv tool install heph@latest\n```"


def render_uv_install_block() -> str:
    return "```bash\ncurl -LsSf https://astral.sh/uv/install.sh | sh\n```"


def render_pip_install_block() -> str:
    return "```bash\npip install heph\n```"


def render_create_armory_block(model: DocsModel) -> str:
    return (
        "```bash\n"
        f"{model.short_command} armory init [name]\n"
        "# Add files to ~/.armories/[name]/materials\n"
        f"{model.short_command} [name]\n"
        "```"
    )


def render_quick_start_block(model: DocsModel) -> str:
    return (
        "```bash\n"
        "# Install UV (if not already installed)\n"
        "curl -LsSf https://astral.sh/uv/install.sh | sh\n\n"
        "# Install Heph\n"
        "uv tool install heph@latest\n\n"
        "# Create a workspace for your files\n"
        f"{model.short_command} armory init [name]\n"
        "\n"
        "# Add documents, notes, or code that Heph can answer from\n"
        "cp ~/Downloads/[file] ~/.armories/[name]/materials/\n\n"
        "# Start Heph in that armory\n"
        f"{model.short_command} [name]\n"
        "```"
    )


def render_readme_badges_block(*, docs_index: bool) -> str:
    license_link = "../LICENSE" if docs_index else "LICENSE"
    badges = (
        (
            "PyPI",
            "https://img.shields.io/pypi/v/heph"
            "?style=for-the-badge&label=PyPI&labelColor=000000&color=3775A9",
            "https://pypi.org/project/heph/",
        ),
        (
            "uv",
            "https://img.shields.io/badge/uv-tool%20install"
            "-654FF0?style=for-the-badge&labelColor=000000",
            "#installation",
        ),
        (
            "License: MIT",
            "https://img.shields.io/badge/license-MIT"
            "-3FB950?style=for-the-badge&labelColor=000000",
            license_link,
        ),
    )
    links = "\n  ".join(
        f'<a href="{target}"><img alt="{alt}" src="{image}"></a>' for alt, image, target in badges
    )
    return f'<p align="center">\n  {links}\n</p>'


def render_armory_layout_block(*, docs_index: bool) -> str:
    return (
        "```text\n"
        "~/.armories/[name]/\n"
        "├── materials/            # PDFs, Office docs, notes, code to cite\n"
        "│   ├── [file].pdf\n"
        "│   └── [file].md\n"
        "├── .harness/             # Local Heph state\n"
        "│   ├── armory.toml       # Armory marker\n"
        "│   ├── rag_index.json    # Retrieval index\n"
        "│   ├── memory.json       # Learning memory\n"
        "│   ├── chats/            # Saved sessions\n"
        "│   ├── traces/           # JSONL traces when enabled\n"
        "│   ├── usage/            # Token and cost snapshots\n"
        "│   └── ignore            # Indexing ignore rules\n"
        "└── README.md             # Armory notes\n"
        "```"
    )


def render_slash_commands_table(commands: tuple[CommandLine, ...]) -> str:
    rows = tuple((command.command, command.description) for command in commands)
    return render_markdown_table(("Command", "Description"), rows)


def render_keyboard_shortcuts_table(shortcuts: tuple[KeyboardShortcutDoc, ...]) -> str:
    rows = tuple(
        (f"`{shortcut.keys}`", f"{shortcut.action}: {shortcut.description}")
        for shortcut in shortcuts
    )
    return render_markdown_table(("Shortcut", "Action"), rows)


def render_env_vars_table(env_vars: tuple[EnvVarDoc, ...]) -> str:
    rows = tuple((f"`{env.name}`", env.description) for env in env_vars)
    return render_markdown_table(("Variable", "Description"), rows)


def render_home_docs_section(*, docs_index: bool) -> str:
    prefix = "" if docs_index else "docs/"
    rows = [
        ("Getting started", f"{prefix}getting-started.md", "first armory, first answer"),
        ("Armories", f"{prefix}armories.md", "layout, portability, memory"),
        ("CLI reference", f"{prefix}cli-reference.md", "commands, shortcuts, env vars"),
        ("Configuration", f"{prefix}configuration.md", "providers, models, settings"),
        ("Models", f"{prefix}models.md", "provider choices and API keys"),
        ("Trust and ownership", f"{prefix}trust.md", "data, cache, prompts, compute"),
        ("Privacy", f"{prefix}privacy.md", "local state, diagnostics, network behavior"),
        ("Architecture", f"{prefix}architecture.md", "harness, package boundaries, flow"),
        ("SDK", f"{prefix}sdk.md", "native apps, GUI shells, automation"),
        ("Troubleshooting", f"{prefix}troubleshooting.md", "setup, indexing, providers"),
        ("Developers", f"{prefix}developers.md", "internal docs"),
        ("Runbooks", f"{prefix}runbooks.md", "operational debugging"),
    ]
    if docs_index:
        rows.append(
            (
                "Contributing",
                "../CONTRIBUTING.md",
                "repo layout and local workflow",
            )
        )
    bullets = "\n".join(f"- [{label}]({path}): {description}" for label, path, description in rows)
    return f"## Docs\n\n{bullets}"


def render_readme_logo_block(*, docs_index: bool) -> str:
    logo_path = Path("../assets/logo-auto.svg") if docs_index else Path("assets/logo-auto.svg")
    return (
        '<p align="center">\n'
        f'  <img alt="Heph" src="{logo_path.as_posix()}" width="{README_LOGO_WIDTH}">\n'
        "</p>\n\n"
    )


def render_readme_screenshot_block(*, docs_index: bool) -> str:
    screenshot_path = (
        Path("../assets/app-screenshot.png") if docs_index else Path("assets/app-screenshot.png")
    )
    return (
        '<p align="center">\n'
        f'  <img alt="Heph TUI" src="{screenshot_path.as_posix()}" width="100%">\n'
        "</p>"
    )


def render_home_footer(*, docs_index: bool) -> str:
    return ""


def render_home_doc(model: DocsModel, *, docs_index: bool) -> str:
    replacements = {
        "GENERATED_NOTICE": GENERATED_NOTICE,
        "UV_INSTALL_BLOCK": render_uv_install_block(),
        "INSTALL_BLOCK": render_install_block(),
        "PIP_INSTALL_BLOCK": render_pip_install_block(),
        "UPGRADE_BLOCK": "```bash\nheph update\n```",
        "GIT_INSTALL_BLOCK": "```bash\nuv tool install git+https://github.com/gildrb/heph\n```",
        "CREATE_ARMORY_BLOCK": render_create_armory_block(model),
        "QUICK_START_BLOCK": render_quick_start_block(model),
        "BADGES_BLOCK": render_readme_badges_block(docs_index=docs_index),
        "ARMORY_LAYOUT_BLOCK": render_armory_layout_block(docs_index=docs_index),
        "ARMORY_DOC_LINK": "[Armories](docs/armories.md)"
        if not docs_index
        else "[Armories](armories.md)",
        "TRUST_DOC_LINK": "[Trust and ownership](docs/trust.md)"
        if not docs_index
        else "[Trust and ownership](trust.md)",
        "TELEMETRY_CONTRACT": model.privacy_diagnostics_contract,
        "COMMON_COMMANDS_BLOCK": render_command_block(model.common_commands),
        "SLASH_COMMANDS_TABLE": render_slash_commands_table(model.slash_commands),
        "README_LOGO_BLOCK": render_readme_logo_block(docs_index=docs_index),
        "README_SCREENSHOT_BLOCK": render_readme_screenshot_block(docs_index=docs_index),
        "DOCS_SECTION": render_home_docs_section(docs_index=docs_index),
        "CONTRIBUTING_LINK": "../CONTRIBUTING.md" if docs_index else "CONTRIBUTING.md",
        "FOOTER_SECTION": render_home_footer(docs_index=docs_index).strip(),
    }
    return render_template("home", HOME_TEMPLATE, replacements)


def render_cli_reference(model: DocsModel) -> str:
    rows = tuple(
        (f"`{command.command}`", command.description) for command in model.cli_reference_commands
    )
    replacements = {
        "GENERATED_NOTICE": GENERATED_NOTICE,
        "CLI_COMMANDS_TABLE": render_markdown_table(("Command", "Description"), rows),
        "SLASH_COMMANDS_TABLE": render_slash_commands_table(model.slash_commands),
        "KEYBOARD_SHORTCUTS_TABLE": render_keyboard_shortcuts_table(model.keyboard_shortcuts),
        "ENV_VARS_TABLE": render_env_vars_table(model.env_vars),
        "SHORT_COMMAND": model.short_command,
    }
    return render_template("cli-reference", CLI_REFERENCE_TEMPLATE, replacements)


def block_markers(name: str) -> tuple[str, str]:
    return (
        BLOCK_START_TEMPLATE.format(name=name),
        BLOCK_END_TEMPLATE.format(name=name),
    )


def replace_managed_block(text: str, name: str, content: str) -> str:
    start_marker, end_marker = block_markers(name)
    replacement = f"{start_marker}\n{content.rstrip()}\n{end_marker}"
    pattern = re.compile(
        rf"{re.escape(start_marker)}\n.*?\n{re.escape(end_marker)}",
        re.DOTALL,
    )
    if not pattern.search(text):
        raise RuntimeError(f"Could not find managed block {name!r}.")
    return pattern.sub(replacement, text, count=1)


def render_targets(root: Path) -> tuple[SyncTarget, ...]:
    model = collect_docs_model(root)
    architecture_text = ARCHITECTURE_PATH.read_text(encoding="utf-8")
    architecture_updated = replace_managed_block(
        architecture_text,
        ARCHITECTURE_BLOCK_NAME,
        model.architecture_privacy_diagnostics,
    )
    return (
        SyncTarget(README_PATH, render_home_doc(model, docs_index=False)),
        SyncTarget(DOCS_INDEX_PATH, render_home_doc(model, docs_index=True)),
        SyncTarget(CLI_REFERENCE_PATH, render_cli_reference(model)),
        SyncTarget(ARCHITECTURE_PATH, architecture_updated),
    )


def write_targets(targets: tuple[SyncTarget, ...], *, check: bool) -> list[Path]:
    stale_paths: list[Path] = []
    for target in targets:
        current = target.path.read_text(encoding="utf-8")
        if current == target.content:
            continue
        stale_paths.append(target.path)
        if not check:
            target.path.write_text(target.content, encoding="utf-8")
    return stale_paths


def should_skip_lint(path: Path) -> bool:
    return path in GENERATED_DOCS


def lint_legacy_commands(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(root.rglob("*.md")):
        if should_skip_lint(path):
            continue
        text = path.read_text(encoding="utf-8")
        for pattern, message in LEGACY_PATTERNS:
            if pattern.search(text):
                rel = path.relative_to(root)
                errors.append(f"{rel}: {message}")
    return errors


def run_sync(*, check: bool) -> int:
    targets = render_targets(ROOT)
    stale_paths = write_targets(targets, check=check)
    lint_errors = lint_legacy_commands(ROOT)

    if stale_paths:
        prefix = "Stale docs detected:" if check else "Updated docs:"
        print(prefix)
        for path in stale_paths:
            print(f"  - {path.relative_to(ROOT)}")

    if lint_errors:
        print("Legacy command references detected:")
        for error in lint_errors:
            print(f"  - {error}")

    if check and (stale_paths or lint_errors):
        return 1
    if not check and not stale_paths:
        print("Docs already in sync.")
    return 0


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    raise SystemExit(run_sync(check=args.check))


if __name__ == "__main__":
    main()
