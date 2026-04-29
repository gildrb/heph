# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Source-management and persistent config CLI commands.
- Persona switching, direct terminal I/O helpers, and an extensible armory tool registry.
- OAuth support plus optional document conversion via `docling`.
- Memory status indicator in the TUI status bar.

### Changed

- Revamped the TTY shell UI, streaming engine, and turn orchestrator flow.
- Refined plain-chat prompting, RAG index handling, and tool security boundaries.
- Removed classic prompt-toolkit shell (`shell.py`, `keybindings.py` deleted).
- Split `commands.py` into `app/commands/` package with per-concern modules.
- Split `harness/` into top-level `agent/` and `rag/` packages.
- Renamed `_build_client` to `build_client` (public API).
- Removed `prompt-toolkit` dependency.
- Moved `pathspec` and `rapidfuzz` to optional dependency groups.

### Fixed

- Provider/auth handling, config persistence, logging errors, and related test coverage.

## [0.1.0] - 2025-04-09

### Added

- Interactive TTY shell built on `prompt_toolkit` with a forge-inspired palette, borderless dynamic composer, and live status rows beneath the input.
- Slash commands for armory/session/model/provider management (`/help`, `/status`, `/save`, `/clear`, `/armory`, `/model`, `/provider`, `/models`, `/api`, `/compact`, `/history`, `/usage`, `/edit`, `/exit`).
- Shell mode via `!command`.
- Armory auto-discovery from the current directory or `./armory`.
- Agent loop with `bash`, `read_file`, `write_file`, `edit_file`, `list_files`, `search_files`, `web_fetch`, and `compact` tools.
- Steering — type while the agent is working to inject follow-up messages mid-loop.
- Three-layer context compaction: silent micro-compact, auto-compact at token thresholds, and manual `/compact`.
- Citation verification against retrieved sources.
- Per-armory memory extraction stored in `.hephaistos/memory.json`.
- Session usage and estimated cost tracking with model-specific pricing.
- Context window budget management with compaction urgency warnings.
- Structured logging plus per-session JSONL traces.
- Multi-provider model switching with built-in model registry.
- TF-IDF retrieval by default; optional embedding/hybrid retrieval, cross-encoder re-ranking, and query transformation when extra dependencies are installed.
- Mutation queue serialising concurrent file writes per-path.
- Keychain-based API key storage with lazy resolution.
