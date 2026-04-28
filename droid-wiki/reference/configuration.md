# Configuration

Hephaistos uses a layered config system: shipped defaults → user config file → environment variables → CLI flags. API keys are never stored in config files — they're resolved at runtime from OS keyring → environment variable → in-memory store.

## User config files

All user config lives under `~/.config/hephaistos/` (managed by `hephaistos/parameters/settings.py`):

### `~/.config/hephaistos/config.json`

Cross-session settings. Managed via `hephaistos/parameters/settings.py` (`AppSettings` dataclass). Contains:

- **theme** — terminal color theme name
- **interface_mode** — `tui` or `shell`
- **telemetry** — opt-in flags for analytics and crash reporting
- **default_armory** — path to the default armory
- **default_model** — model ID to use when none specified
- **feature flags** — toggles for experimental features

### `~/.config/hephaistos/providers.toml`

LLM provider definitions. Managed via `hephaistos/providers/config.py` (`ProviderConfig`). Each provider entry has:

- `display_name` — human-readable name
- `endpoint` — OpenAI-compatible API base URL
- `api_key_env` — environment variable name for the API key
- `active` — whether the provider is enabled
- `current_model` — default model for this provider
- `models` — list of available model IDs

Example:

```toml
[zai]
display_name = "Z.AI"
endpoint = "https://api.z.ai/api/paas/v4/"
api_key_env = "ZAI_API_KEY"
active = true
current_model = "glm-5"
models = ["glm-5", "glm-5-plus"]
```

### `~/.config/hephaistos/auth.json`

OAuth tokens for providers that use browser-based auth. File permissions are set to `0600` (owner read/write only). Managed via `hephaistos/providers/oauth.py`.

## Shipped defaults

### `hephaistos/parameters/default.toml`

Default values shipped with the package. These are the base layer that user config overrides. Contains default theme, interface mode, telemetry defaults, and feature flag defaults.

## Armory-local config

Each armory directory can contain these files under `.hephaistos/`:

### `.hephaistos/armory.toml`

Marker file that identifies a directory as a Hephaistos armory. Created by `heph armory init`.

### `.hephaistos/system_prompt.md`

Optional custom study prompt. When present, its contents are prepended to the agent's system prompt for all sessions in this armory. Write it in plain markdown — it's injected as-is.

### `.hephaistos/memory.json`

Per-armory study memory. Contains concepts extracted from past sessions. Managed by `hephaistos/memory/__init__.py` (`MemoryStore`). Read automatically when a session starts; updated after substantive exchanges.

### `.hephaistos/rag_index.json`

Per-armory retrieval index. Built by the RAG indexer and read by the retrieval layer. Contains document chunks, embeddings metadata, and index statistics. Managed by `hephaistos/harness/rag/index.py` (`ArmoryIndex`).

## Environment variables

### API keys

Resolved at runtime in this order: OS keyring → environment variable → in-memory store (prompted).

| Variable | Purpose |
|----------|---------|
| `HEPHAISTOS_API_KEY` | Generic API key for any provider |
| `HEPHAISTOS_BASE_URL` | Override the API base URL |
| `HEPHAISTOS_MODEL` | Override the model ID |
| `OPENROUTER_API_KEY` | OpenRouter-specific API key |
| `OPENAI_API_KEY` | OpenAI-specific API key |
| `ZAI_API_KEY` | Z.AI-specific API key |
| `CUSTOM_API_KEY` | Custom provider API key |

### Logging

| Variable | Values | Default |
|----------|--------|---------|
| `HEPHAISTOS_LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `WARNING` |
| `HEPHAISTOS_LOG_FILE` | file path | stderr |
| `HEPHAISTOS_LOG_FORMAT` | `text`, `json` | `text` |

### Telemetry

| Variable | Values | Default |
|----------|--------|---------|
| `HEPHAISTOS_ANALYTICS_ENABLED` | `true`, `false` | `false` |
| `HEPHAISTOS_CRASH_REPORTS_ENABLED` | `true`, `false` | `false` |

Telemetry is opt-in and anonymous. The public repo ships safe stubs in `hephaistos/_telemetry_release.py` — official release builds inject actual PostHog/Sentry keys during CI.
