<!-- Managed by scripts/sync_docs.py. Do not edit directly. -->

# CLI Reference

## CLI commands

| Command | Description |
|---|---|
| `heph` | Open your current armory or plain chat. |
| `heph <name-or-path>` | Open an armory by name from `~/.armories`, e.g. `heph gdp`, or by explicit path; empty armories open with a no-materials state. |
| `heph armory init <name>` | Create a new named armory folder. |
| `heph armory open <path>` | Open and validate an armory. |
| `heph materials list <path>` | List material files. |
| `heph materials count <path>` | Count material files. |
| `heph materials index <path>` | Build or refresh the RAG index. |
| `heph index [path]` | Build or refresh the materials index; defaults to the current armory. |
| `heph health [path]` | Check indexed materials for generic extraction problems; defaults to the current armory. |
| `heph local search [query]` | Browse curated GGUF models. |
| `heph local install <repo-or-path>` | Install a curated GGUF model or local `.gguf` path after confirmation, then activate it only if it passes Heph's tool-call probe. |
| `heph local status` | Show local llama.cpp status. |
| `heph local revalidate <model-id>` | Rerun the tool-call probe for an installed local model. |
| `heph local stop` | Stop the managed llama.cpp server. |
| `heph update` | Show how to update the active Heph install. |
| `heph sdk serve` | Run the SDK JSONL stdio service. |
| `heph sdk capabilities` | Print the SDK capability contract as JSON. |
| `heph release status` | Show installed package, official stable, and release channel state. |
| `heph config show` | Display current configuration. |
| `heph config set <key> <value>` | Set a configuration parameter. |
| `heph chat ask <path> [prompt]` | Ask one question without opening the TUI. |
| `heph chat ask --jsonl <path> [prompt]` | Emit structured turn events as JSON Lines for audits. |
| `heph tui [path]` | Explicit alias for the default Textual TUI. |

`heph` is the canonical public command that starts the Heph agent.
Use `heph tui [path]` only when a script needs the explicit TUI subcommand.

## Slash commands

| Command | Description |
|---|---|
| /help | Show available commands |
| /exit | Leave Heph |
| /login | Authenticate with a subscription or API key |
| /local | Install and manage curated local llama.cpp models |
| /logout | Clear stored subscription or API-key credentials |
| /status | Show session, usage, armory, and review info |
| /new | Start a new chat |
| /detach | Detach the current armory |
| /armory | Browse, open, or create armories |
| /compact | Summarize conversation to reduce context size |
| /evidence | Show retrieved evidence for the last turn |
| /cost | Show or hide live cost estimates |
| /priority | Generate a printable priority PDF cheat sheet |
| /exam | Start an active-recall exam question |
| /export | Export the current session to a markdown file |
| /import | Import files into the armory materials directory |
| /memory | Show saved armory memory |
| /models | Pick the active model |
| /settings | Manage cross-session preferences |
| /sessions | Switch between saved sessions |
| /stats | Alias for /status with session and armory statistics |
| /turn | Branch from an earlier completed turn |
| /index | Refresh the current armory materials index |
| /vocabulary | Practice vocabulary translations from your materials |
| /materials | Choose which materials are used for retrieval |
| /keymap | Edit keyboard shortcuts |

## TUI keyboard shortcuts

The `/keymap` slash command opens the editable shortcut map inside Heph. Choose
an action, then select RECORD or press Enter before typing the new shortcut.
Use the visible RESET action on a shortcut, or RESET ALL KEYBINDS from the keymap
list, to restore defaults.
Some terminal and desktop shortcuts are reserved, so Heph rejects keys such as
`ctrl+c`, `ctrl+d`, `ctrl+m`, `ctrl+t`, `alt+m`, and `f4`.
macOS keeps the familiar function-key defaults below. On Linux and other
platforms, app-wide defaults avoid function keys: Commands `ctrl+alt+p`,
Armory `ctrl+alt+a`, Materials `ctrl+alt+m`, Search `ctrl+alt+f`, and
Evidence `ctrl+alt+e`.

| Shortcut | Action |
|---|---|
| `f2` | Commands: Open the command palette. |
| `f3` | Armory: Open the armory home. |
| `f5` | Materials: Choose which materials are used for retrieval. |
| `f6` | Search: Search across armories. |
| `f8` | Evidence: Show evidence details. |
| `ctrl+l` | Screen: Clear the screen. |
| `tab` | Complete: Complete the current input. |
| `shift+tab` | Reasoning: Cycle the reasoning level. |
| `shift+enter/ctrl+enter/alt+enter/ctrl+j` | Newline: Insert a composer newline. |
| `escape` | Stop: Interrupt the active request. |
| `ctrl+c` | Quit: Quit Heph. |
| `ctrl+d` | Quit: Quit from an empty composer. |

## Environment variables

| Variable | Description |
|---|---|
| `CUSTOM_API_KEY` | API key for the custom provider entry. |
| `DEEPSEEK_API_KEY` | API key for the DeepSeek API provider. |
| `HARNESS_ANALYTICS_ENABLED` | Override the saved analytics opt-in (`true`/`false`). |
| `HARNESS_API_KEY` | Global API key override that applies to any provider. |
| `HARNESS_BASE_URL` | Override the active API base URL. |
| `HARNESS_CRASH_REPORTS_ENABLED` | Override the saved crash-report opt-in (`true`/`false`). |
| `HARNESS_EMBED_MODEL` | Override the embedding model used by retrieval. |
| `HARNESS_EXTRACTION_MODEL` | Override the model used for background memory extraction. |
| `HARNESS_FEATURE_FLAGS` | Comma-separated feature flags. |
| `HARNESS_LOG_FILE` | Append structured logs to a file when set. |
| `HARNESS_LOG_FORMAT` | Choose `json` or `text` logging output. |
| `HARNESS_LOG_LEVEL` | Configure structured log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `HARNESS_MAX_TOKENS` | Set the max output tokens per response. |
| `HARNESS_MODEL` | Override the active model. |
| `HARNESS_POSTHOG_HOST` | Supply a PostHog host for a custom or forked build. |
| `HARNESS_POSTHOG_PROJECT_TOKEN` | Supply a PostHog project token for a custom or forked build. |
| `HARNESS_PRIORITY_WEB_PREREQS` | Enable optional web-backed prerequisite hints in priority reports. |
| `HARNESS_RAG_CONTEXT_BUDGET` | Set the token budget for retrieved context. |
| `HARNESS_RERANK_MODEL` | Override the reranker model when available. |
| `HARNESS_RTK_FALLBACK_ALLOWED` | Set to `0` to fail closed when the optional RTK wrapper is unavailable. |
| `HARNESS_SENTRY_DSN` | Supply a Sentry DSN for a custom or forked build. |
| `HARNESS_TEMPERATURE` | Override the generation temperature for chat responses. |
| `HARNESS_TRUST_ARMORY_PLUGINS` | Allow trusted armories to load `.harness/tools/*.py` plugins. |
| `OPENAI_API_KEY` | API key for the OpenAI API provider. |
| `OPENROUTER_API_KEY` | API key for OpenRouter. |
| `ZAI_API_KEY` | API key for Z.AI / GLM. |
