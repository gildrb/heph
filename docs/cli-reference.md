<!-- Managed by scripts/sync_docs.py. Do not edit directly. -->

# CLI Reference

## CLI commands

| Command | Description |
|---|---|
| `heph` | Open your current armory or plain chat. |
| `heph <name-or-path>` | Open a known armory by name, e.g. `heph gdp`, or by path. |
| `hephaistos [path]` | Equivalent long entrypoint for `heph`. |
| `heph armory <name> [parent]` | Create a named armory in ~/Armories or in <parent>/Armories. |
| `heph armory init <name-or-path>` | Create a new named armory folder. |
| `heph armory open <path>` | Open and validate an armory. |
| `heph materials list <path>` | List study material files. |
| `heph materials count <path>` | Count study material files. |
| `heph materials index <path>` | Build or refresh the RAG index. |
| `heph index [path]` | Build or refresh the materials index; defaults to the current armory. |
| `heph health [path]` | Check indexed materials for generic extraction problems; defaults to the current armory. |
| `heph update` | Show how to update the active Hephaistos install. |
| `heph config show` | Display current configuration. |
| `heph config set <key> <value>` | Set a configuration parameter. |
| `heph chat start <path>` | Start a new chat session in an armory. |
| `heph chat resume <path> <id>` | Resume an existing chat session. |
| `heph chat ask <path> [prompt]` | Ask one question without opening the TUI. |
| `heph chat ask --jsonl <path> [prompt]` | Emit structured turn events as JSON Lines for harness audits. |
| `heph chat list <path>` | List chat sessions in an armory. |
| `heph start [path]` | Hidden backwards-compatible alias for `heph [path]`. |
| `heph tui [path]` | Explicit alias for the default Textual TUI. |
| `heph source list <path>` | Deprecated alias for `heph materials list <path>`. |
| `heph source count <path>` | Deprecated alias for `heph materials count <path>`. |
| `heph source index <path>` | Deprecated alias for `heph materials index <path>`. |

`heph` is the canonical public command. `hephaistos` is an
equivalent long entrypoint. `heph start [path]` stays available as
a hidden backwards-compatible alias and should not be the primary instruction in
new docs.

## Slash commands

| Command | Description |
|---|---|
| /help | Show available commands |
| /exit | Leave the shell |
| /login | Authenticate with a subscription or API key |
| /logout | Clear stored subscription or API-key credentials |
| /status | Show armory, session, and model info |
| /new | Start a new chat |
| /armory | Browse, open, or create armories |
| /compact | Summarize conversation to reduce context size |
| /evidence | Show retrieved evidence for the last turn |
| /tokens | Show or hide live token estimates |
| /cost | Show or hide live cost estimates |
| /stats | Show session, armory, and study progress stats |
| /priority | Generate a printable priority PDF cheat sheet |
| /mode | Set manual, guided, or autopilot study mode |
| /autopilot | Let Heph drive a bounded autonomous study session |
| /exam | Start an active-recall exam question |
| /export | Export the current session to a markdown file |
| /import | Import files into the armory materials directory |
| /remind | Show upcoming study reminders and due cards |
| /edit | Edit and resend the last user message |
| /models | Pick the active model |
| /recommend | Recommend models for study sessions |
| /memory | Manage study memory and Supermemory setup |
| /persona | Show or switch the agent persona |
| /settings | Manage cross-session preferences |
| /sessions | Switch between saved sessions |
| /index | Manage cross-armory search index |
| /usage | Show token usage and cost for this session |
| /vocab | Vocabulary drill with spaced repetition |

## Environment variables

| Variable | Description |
|---|---|
| `CUSTOM_API_KEY` | API key for the custom provider entry. |
| `HEPHAISTOS_ANALYTICS_ENABLED` | Override the saved analytics opt-in (`true`/`false`). |
| `HEPHAISTOS_API_KEY` | Global API key override that applies to any provider. |
| `HEPHAISTOS_BASE_URL` | Override the active API base URL. |
| `HEPHAISTOS_CRASH_REPORTS_ENABLED` | Override the saved crash-report opt-in (`true`/`false`). |
| `HEPHAISTOS_EMBED_MODEL` | Override the embedding model used by retrieval. |
| `HEPHAISTOS_EXTRACTION_MODEL` | Override the model used for background memory extraction. |
| `HEPHAISTOS_FEATURE_FLAGS` | Comma-separated feature flags. |
| `HEPHAISTOS_LOG_FILE` | Append structured logs to a file when set. |
| `HEPHAISTOS_LOG_FORMAT` | Choose `json` or `text` logging output. |
| `HEPHAISTOS_LOG_LEVEL` | Configure structured log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `HEPHAISTOS_MAX_TOKENS` | Set the max output tokens per response. |
| `HEPHAISTOS_MODEL` | Override the active model. |
| `HEPHAISTOS_POSTHOG_HOST` | Supply a PostHog host for a custom or forked build. |
| `HEPHAISTOS_POSTHOG_PROJECT_TOKEN` | Supply a PostHog project token for a custom or forked build. |
| `HEPHAISTOS_RAG_CONTEXT_BUDGET` | Set the token budget for retrieved context. |
| `HEPHAISTOS_RERANK_MODEL` | Override the reranker model when available. |
| `HEPHAISTOS_SENTRY_DSN` | Supply a Sentry DSN for a custom or forked build. |
| `OPENAI_API_KEY` | API key for the OpenAI API provider. |
| `OPENROUTER_API_KEY` | API key for OpenRouter. |
| `SUPERMEMORY_API_KEY` | API key for Supermemory study memory. |
| `SUPERMEMORY_URL` | Override the Supermemory API base URL. |
| `ZAI_API_KEY` | API key for Z.AI / GLM. |
