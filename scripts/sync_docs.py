"""Synchronize repo-native docs from code-backed sources."""

from __future__ import annotations

import argparse
import argparse as _argparse
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from hephaion.chat.session import ARMORY_PLUGINS_TRUST_ENV
from hephaion.cli.main import build_parser
from hephaion.commands import get_registry
from hephaion.logging import _LOG_FILE_ENV, _LOG_FORMAT_ENV, _LOG_LEVEL_ENV
from hephaion.memory.extract import _EXTRACTION_MODEL_ENV
from hephaion.parameters import cli as parameters_cli
from hephaion.privacy.consent import (
    ANALYTICS_ENABLED_ENV,
    CRASH_REPORTS_ENABLED_ENV,
    POSTHOG_HOST_ENV,
    POSTHOG_TOKEN_ENV,
    SENTRY_DSN_ENV,
)
from hephaion.providers.config import default_config
from hephaion.providers.keyring_store import GLOBAL_API_KEY_ENV
from hephaion.rag.retrieve import _EMBED_MODEL_ENV, _RERANK_MODEL_ENV

ROOT: Final[Path] = Path(__file__).resolve().parent.parent
PYPROJECT_PATH: Final[Path] = ROOT / "pyproject.toml"
README_PATH: Final[Path] = ROOT / "README.md"
DOCS_INDEX_PATH: Final[Path] = ROOT / "docs" / "index.md"
CLI_REFERENCE_PATH: Final[Path] = ROOT / "docs" / "cli-reference.md"
AGENTS_PATH: Final[Path] = ROOT / "AGENTS.md"
ARCHITECTURE_PATH: Final[Path] = ROOT / "docs" / "architecture.md"
TEMPLATES_DIR: Final[Path] = ROOT / "docs" / "_templates"
FRAGMENTS_DIR: Final[Path] = ROOT / "docs" / "_fragments"

GENERATED_NOTICE: Final[str] = "<!-- Managed by scripts/sync_docs.py. Do not edit directly. -->"
AGENTS_BLOCK_NAME: Final[str] = "privacy-diagnostics-docs-contract"
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
SKIP_LINT_DIRS: Final[frozenset[Path]] = frozenset(
    {
        ROOT / "docs" / "_templates",
        ROOT / "docs" / "_fragments",
    }
)


@dataclass(frozen=True)
class CommandLine:
    command: str
    description: str


@dataclass(frozen=True)
class EnvVarDoc:
    name: str
    description: str


@dataclass(frozen=True)
class DocsModel:
    short_command: str
    long_command: str
    project_name: str
    scripts_entrypoint: str
    common_commands: tuple[CommandLine, ...]
    cli_reference_commands: tuple[CommandLine, ...]
    slash_commands: tuple[CommandLine, ...]
    env_vars: tuple[EnvVarDoc, ...]
    privacy_diagnostics_contract: str
    agents_contract: str
    architecture_privacy_diagnostics: str


@dataclass(frozen=True)
class SyncTarget:
    path: Path
    content: str


ENV_VAR_DESCRIPTIONS: Final[dict[str, str]] = {
    "HEPHAION_BASE_URL": "Override the active API base URL.",
    "HEPHAION_MODEL": "Override the active model.",
    "HEPHAION_MAX_TOKENS": "Set the max output tokens per response.",
    "HEPHAION_RAG_CONTEXT_BUDGET": "Set the token budget for retrieved context.",
    "HEPHAION_FEATURE_FLAGS": "Comma-separated feature flags.",
    "HEPHAION_ANALYTICS_ENABLED": "Override the saved analytics opt-in (`true`/`false`).",
    "HEPHAION_API_KEY": "Global API key override that applies to any provider.",
    "HEPHAION_ARMORY_HOME": (
        "Default parent folder for named armories (`~/.armories` by default)."
    ),
    "HEPHAION_TRUST_ARMORY_PLUGINS": (
        "Allow trusted armories to load `.hephaion/tools/*.py` plugins."
    ),
    "HEPHAION_CRASH_REPORTS_ENABLED": "Override the saved crash-report opt-in (`true`/`false`).",
    "HEPHAION_EMBED_MODEL": "Override the embedding model used by retrieval.",
    "HEPHAION_EXTRACTION_MODEL": "Override the model used for background memory extraction.",
    "HEPHAION_LOG_FILE": "Append structured logs to a file when set.",
    "HEPHAION_LOG_FORMAT": "Choose `json` or `text` logging output.",
    "HEPHAION_LOG_LEVEL": (
        "Configure structured log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`)."
    ),
    "HEPHAION_POSTHOG_HOST": "Supply a PostHog host for a custom or forked build.",
    "HEPHAION_POSTHOG_PROJECT_TOKEN": (
        "Supply a PostHog project token for a custom or forked build."
    ),
    "HEPHAION_RERANK_MODEL": "Override the reranker model when available.",
    "HEPHAION_RTK_FALLBACK_ALLOWED": (
        "Set to `0` to fail closed when the optional RTK wrapper is unavailable."
    ),
    "HEPHAION_SENTRY_DSN": "Supply a Sentry DSN for a custom or forked build.",
    "HEPHAION_TEMPERATURE": "Override the generation temperature for chat responses.",
    "OPENAI_API_KEY": "API key for the OpenAI API provider.",
    "OPENROUTER_API_KEY": "API key for OpenRouter.",
    "ZAI_API_KEY": "API key for Z.AI / GLM.",
    "CUSTOM_API_KEY": "API key for the custom provider entry.",
}

CLI_COMMAND_DESCRIPTIONS: Final[dict[str, str]] = {
    "heph": "Open your current armory or plain chat.",
    "heph <name-or-path>": "Open a known armory by name, e.g. `heph gdp`, or by path.",
    "hephaion [path]": "Equivalent long Hephaion harness entrypoint for `heph`.",
    "heph armory <name>": "Create a named armory in `~/.armories`.",
    "heph tui [path]": "Explicit alias for the default Textual TUI.",
    "heph update": "Show how to update the active Heph install.",
    "heph chat ask --jsonl <path> [prompt]": (
        "Emit structured turn events as JSON Lines for harness audits."
    ),
    "heph health [path]": (
        "Check indexed materials for generic extraction problems; defaults to the current armory."
    ),
    "heph index [path]": "Build or refresh the materials index; defaults to the current armory.",
}

LEGACY_PATTERNS: Final[tuple[tuple[re.Pattern[str], str], ...]] = (
    (
        re.compile(r"\bheph\s+start\b"),
        "Use `heph` or `heph <path>` as the primary command.",
    ),
    (
        re.compile(r"\bhephaion\s+start\b"),
        "Use `hephaion` or `hephaion <name-or-path>` as the long-form harness command.",
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


def collect_cli_commands(short_command: str, long_command: str) -> tuple[CommandLine, ...]:
    parser = build_parser()
    subparsers = get_subparsers_action(parser)
    top_level = list(subparsers.choices.keys())

    required_visible = {
        "armory",
        "materials",
        "index",
        "health",
        "update",
        "config",
    }
    if not required_visible.issubset(top_level):
        raise RuntimeError("The top-level CLI surface changed; update sync_docs.py.")
    if "chat" not in top_level:
        raise RuntimeError("Expected hidden `chat` automation command to exist.")

    armory_parser = subparsers.choices["armory"]
    materials_parser = subparsers.choices["materials"]
    config_parser = subparsers.choices["config"]
    chat_parser = subparsers.choices["chat"]

    armory_sub = get_subparsers_action(armory_parser)
    materials_sub = get_subparsers_action(materials_parser)
    config_sub = get_subparsers_action(config_parser)
    chat_sub = get_subparsers_action(chat_parser)

    armory_help = build_help_map(armory_sub)
    materials_help = build_help_map(materials_sub)
    config_help = build_help_map(config_sub)
    chat_help = build_help_map(chat_sub)

    return (
        CommandLine(short_command, CLI_COMMAND_DESCRIPTIONS[short_command]),
        CommandLine(
            f"{short_command} <name-or-path>",
            CLI_COMMAND_DESCRIPTIONS[f"{short_command} <name-or-path>"],
        ),
        CommandLine(
            f"{long_command} [path]",
            CLI_COMMAND_DESCRIPTIONS[f"{long_command} [path]"],
        ),
        CommandLine(
            f"{short_command} armory <name>",
            CLI_COMMAND_DESCRIPTIONS[f"{short_command} armory <name>"],
        ),
        CommandLine(f"{short_command} armory init <name-or-path>", armory_help["init"]),
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
        CommandLine(f"{short_command} update", CLI_COMMAND_DESCRIPTIONS["heph update"]),
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


def collect_common_commands(short_command: str, long_command: str) -> tuple[CommandLine, ...]:
    cli_commands = {
        item.command: item.description
        for item in collect_cli_commands(short_command, long_command)
    }
    selected = (
        short_command,
        f"{short_command} <name-or-path>",
        f"{short_command} armory <name>",
        f"{short_command} armory init <name-or-path>",
        f"{short_command} armory open <path>",
        f"{short_command} materials list <path>",
        f"{short_command} materials count <path>",
        f"{short_command} materials index <path>",
        f"{short_command} index [path]",
        f"{short_command} health [path]",
        f"{short_command} update",
        f"{short_command} chat ask <path> [prompt]",
        f"{short_command} chat ask --jsonl <path> [prompt]",
        f"{short_command} tui [path]",
    )
    return tuple(CommandLine(command, cli_commands[command]) for command in selected)


def collect_slash_commands() -> tuple[CommandLine, ...]:
    registry = get_registry()
    return tuple(
        CommandLine(
            f"/{suggestion.name}",
            suggestion.description,
        )
        for suggestion in registry.suggestions()
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
            _LOG_LEVEL_ENV,
            _LOG_FILE_ENV,
            _LOG_FORMAT_ENV,
            _EMBED_MODEL_ENV,
            _EXTRACTION_MODEL_ENV,
            _RERANK_MODEL_ENV,
            "HEPHAION_RTK_FALLBACK_ALLOWED",
            ARMORY_PLUGINS_TRUST_ENV,
            *provider_envs,
        }
    )
    missing = [name for name in names if name not in ENV_VAR_DESCRIPTIONS]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing environment variable descriptions for: {joined}")
    return tuple(EnvVarDoc(name, ENV_VAR_DESCRIPTIONS[name]) for name in names)


def load_fragment(name: str) -> str:
    path = FRAGMENTS_DIR / name
    return path.read_text(encoding="utf-8").strip()


def collect_docs_model(root: Path) -> DocsModel:
    scripts = load_project_scripts(root / "pyproject.toml")
    short_command = "heph"
    long_command = "hephaion"
    if short_command not in scripts or long_command not in scripts:
        raise RuntimeError("Expected both `heph` and `hephaion` entrypoints in pyproject.toml.")
    if scripts[short_command] != scripts[long_command]:
        raise RuntimeError("Expected `heph` and `hephaion` to share one entrypoint.")

    return DocsModel(
        short_command=short_command,
        long_command=long_command,
        project_name="Hephaion",
        scripts_entrypoint=scripts[short_command],
        common_commands=collect_common_commands(short_command, long_command),
        cli_reference_commands=collect_cli_commands(short_command, long_command),
        slash_commands=collect_slash_commands(),
        env_vars=collect_env_vars(),
        privacy_diagnostics_contract=load_fragment("privacy-diagnostics-contract.md"),
        agents_contract=load_fragment("agents-privacy-diagnostics-contract.md"),
        architecture_privacy_diagnostics=load_fragment("privacy-diagnostics-architecture.md"),
    )


def render_template(template_name: str, replacements: dict[str, str]) -> str:
    template = (TEMPLATES_DIR / template_name).read_text(encoding="utf-8")

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


def render_install_block(model: DocsModel) -> str:
    return (
        "```bash\n"
        "uv tool install heph@latest\n"
        f"{model.short_command}\n"
        f"{model.short_command} --version\n"
        "```"
    )


def render_pip_install_block() -> str:
    return (
        "```bash\n"
        "pip install heph\n"
        "```\n\n"
        "For PDF, DOCX, PPTX, and XLSX conversion support, install the optional Docling extra:\n\n"
        "```bash\n"
        'pip install "heph[docling]"\n'
        "```"
    )


def render_create_armory_block(model: DocsModel) -> str:
    return (
        "```bash\n"
        f"{model.short_command} armory init exams\n"
        "# Add source files to ~/.armories/exams/materials\n"
        f"{model.short_command} exams\n"
        "```"
    )


def render_slash_commands_table(commands: tuple[CommandLine, ...]) -> str:
    rows = tuple((command.command, command.description) for command in commands)
    return render_markdown_table(("Command", "Description"), rows)


def render_env_vars_table(env_vars: tuple[EnvVarDoc, ...]) -> str:
    rows = tuple((f"`{env.name}`", env.description) for env in env_vars)
    return render_markdown_table(("Variable", "Description"), rows)


def render_home_docs_section(*, docs_index: bool) -> str:
    prefix = "" if docs_index else "docs/"
    contributing = "../CONTRIBUTING.md" if docs_index else "CONTRIBUTING.md"
    rows = (
        (f"{prefix}getting-started.md", "first armory and materials walkthrough"),
        (f"{prefix}armories.md", "portable armory layout and local storage"),
        (f"{prefix}cli-reference.md", "CLI commands, slash commands, and environment variables"),
        (f"{prefix}configuration.md", "provider and model configuration"),
        (f"{prefix}models.md", "provider choices, model selection, and API keys"),
        (f"{prefix}privacy.md", "local-first storage, diagnostics, and network behavior"),
        (f"{prefix}architecture.md", "package boundaries and data flow"),
        (f"{prefix}troubleshooting.md", "common setup, indexing, and provider issues"),
        (f"{prefix}developers/index.md", "developer docs and internal guides"),
        (f"{prefix}developers/runbooks/index.md", "operational debugging runbooks"),
        (contributing, "repo layout, development workflow, and contribution guidelines"),
    )
    bullets = "\n".join(f"- [{path}]({path}) — {description}" for path, description in rows)
    return f"## Docs\n\n{bullets}"


def render_home_footer(*, docs_index: bool) -> str:
    if docs_index:
        return (
            "## Next Steps\n\n"
            "- Read the [CLI reference](cli-reference.md) for commands and keyboard shortcuts.\n"
            "- Read the [architecture guide](architecture.md) for package boundaries"
            " and data flow.\n"
            "- Read [agentic development](developers/agentic-development.md) for"
            " agent-readiness conventions.\n"
            "- Read the [runbooks](developers/runbooks/index.md) for operational"
            " debugging.\n"
        )
    return (
        "## License\n\n"
        "This project is licensed under the "
        "[GNU General Public License v3.0 only](LICENSE).\n"
    )


def render_home_doc(model: DocsModel, *, docs_index: bool) -> str:
    long_entry = f"`{model.long_command}`"
    compatibility = (
        f"`{model.short_command} [path]` opens the TUI. "
        f"`{model.short_command} tui [path]` is the explicit form, "
        f"and {long_entry} is the long entrypoint."
    )
    replacements = {
        "GENERATED_NOTICE": GENERATED_NOTICE,
        "INSTALL_BLOCK": render_install_block(model),
        "PIP_INSTALL_BLOCK": render_pip_install_block(),
        "UPGRADE_BLOCK": "```bash\nuv tool upgrade heph\n```",
        "GIT_INSTALL_BLOCK": "```bash\nuv tool install git+https://github.com/gildrb/heph\n```",
        "CREATE_ARMORY_BLOCK": render_create_armory_block(model),
        "EQUIVALENT_ENTRYPOINT_NOTE": compatibility,
        "TELEMETRY_CONTRACT": model.privacy_diagnostics_contract,
        "COMMON_COMMANDS_BLOCK": render_command_block(model.common_commands),
        "SLASH_COMMANDS_TABLE": render_slash_commands_table(model.slash_commands),
        "DOCS_SECTION": render_home_docs_section(docs_index=docs_index),
        "CONTRIBUTING_LINK": "../CONTRIBUTING.md" if docs_index else "CONTRIBUTING.md",
        "FOOTER_SECTION": render_home_footer(docs_index=docs_index).strip(),
    }
    return render_template("home.md.template", replacements)


def render_cli_reference(model: DocsModel) -> str:
    rows = tuple(
        (f"`{command.command}`", command.description) for command in model.cli_reference_commands
    )
    replacements = {
        "GENERATED_NOTICE": GENERATED_NOTICE,
        "CLI_COMMANDS_TABLE": render_markdown_table(("Command", "Description"), rows),
        "SLASH_COMMANDS_TABLE": render_slash_commands_table(model.slash_commands),
        "ENV_VARS_TABLE": render_env_vars_table(model.env_vars),
        "SHORT_COMMAND": model.short_command,
        "LONG_COMMAND": model.long_command,
    }
    return render_template("cli-reference.md.template", replacements)


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
    agents_text = AGENTS_PATH.read_text(encoding="utf-8")
    architecture_text = ARCHITECTURE_PATH.read_text(encoding="utf-8")
    agents_updated = replace_managed_block(agents_text, AGENTS_BLOCK_NAME, model.agents_contract)
    architecture_updated = replace_managed_block(
        architecture_text,
        ARCHITECTURE_BLOCK_NAME,
        model.architecture_privacy_diagnostics,
    )
    return (
        SyncTarget(README_PATH, render_home_doc(model, docs_index=False)),
        SyncTarget(DOCS_INDEX_PATH, render_home_doc(model, docs_index=True)),
        SyncTarget(CLI_REFERENCE_PATH, render_cli_reference(model)),
        SyncTarget(AGENTS_PATH, agents_updated),
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
    if path in GENERATED_DOCS:
        return True
    return any(parent in SKIP_LINT_DIRS for parent in [path, *path.parents])


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
