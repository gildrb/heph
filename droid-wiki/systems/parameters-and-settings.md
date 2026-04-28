# Parameters and settings

The parameters system provides typed access to user-facing configuration persisted in `~/.config/hephaistos/config.json`. It manages theme, interface mode, telemetry opt-in, default armory path, feature flags, and other cross-session preferences. The CLI interface (`/config show`, `/config set`, `/config reset`) is defined here.

## Purpose

- Provide typed, validated read/write access to persistent user settings.
- Define allowed setting types (boolean, string, integer) via `BOOL_KEYS`, `STRING_KEYS`, `INT_KEYS`.
- Layer defaults from `default.toml`, persisted settings from `config.json`, and environment variables.
- Normalize and validate user input before persisting.

## Directory layout

```
hephaistos/parameters/
├── settings.py        # AppSettings, load_app_settings(), save_setting(), type coercion
├── cli.py             # load_config(), /config show, /config set subcommands
├── default.toml       # Factory defaults (max_tokens, logging hints)
└── __init__.py
```

## Key abstractions

| Abstraction | File | Purpose |
|---|---|---|
| `AppSettings` | `hephaistos/parameters/settings.py` | Frozen dataclass with all typed settings fields |
| `load_app_settings()` | `hephaistos/parameters/settings.py` | Loads and returns typed `AppSettings` from `config.json` with defaults |
| `load_raw_settings()` | `hephaistos/parameters/settings.py` | Returns the raw `dict[str, object]` from `config.json` |
| `save_raw_settings()` | `hephaistos/parameters/settings.py` | Persists filtered settings to disk, updates in-process cache |
| `save_setting()` | `hephaistos/parameters/settings.py` | Normalize and persist a single key/value pair |
| `load_config()` | `hephaistos/parameters/cli.py` | Builds `ChatConfig` from defaults + provider config + user overrides + env vars |
| `BOOL_KEYS` | `hephaistos/parameters/settings.py` | Frozenset of boolean setting keys |
| `STRING_KEYS` | `hephaistos/parameters/settings.py` | Frozenset of string setting keys |
| `INT_KEYS` | `hephaistos/parameters/settings.py` | Frozenset of integer setting keys |

## How it works

### Settings schema

Settings are divided into three categories:

**Boolean keys** (`BOOL_KEYS`):
- `analytics_enabled` — PostHog analytics opt-in (default: `false`)
- `crash_reports_enabled` — Sentry crash reporting opt-in (default: `false`)
- `supermemory_enabled` — SuperMemory integration (default: `false`)
- `supermemory_onboarding_seen` — Internal: onboarding dismissed (default: `false`)
- `telemetry_notice_seen` — Internal: telemetry notice shown (default: `false`)

**String keys** (`STRING_KEYS`):
- `base_url` — LLM API endpoint override
- `model` — Default model name
- `feature_flags` — Comma-separated feature flag slugs
- `supermemory_profile` — SuperMemory profile name (default: `heph-study`)
- `theme` — UI theme: `forge`, `light`, or `high_contrast` (default: `forge`)
- `default_armory_path` — Default armory directory
- `interface_mode` — `tui` or `classic` (default: `tui`)

**Integer keys** (`INT_KEYS`):
- `max_tokens` — Completion token limit (default: `4096`)
- `rag_context_budget` — RAG evidence token budget (default: `2000`)
- `session_count` — Internal: sessions started (default: `0`)

Settings are further classified as `PUBLIC_CONFIG_KEYS` (user-visible) and `INTERNAL_CONFIG_KEYS` (tracked but not shown in `/config set`).

### Loading chain

`load_app_settings()` reads settings through this chain:

1. **`default.toml`**: Factory defaults for `max_tokens` only. Provider/model/key configuration is done via shell commands, not TOML.
2. **`config.json`**: User-persisted overrides. Loaded by `load_raw_settings()` with in-process caching (invalidated on file change).
3. **Coercion**: Each value is coerced to its expected type via `_coerce_bool()`, `int()`, or validated against `THEME_PRESETS`/`INTERFACE_MODES`.

### Value normalization

`normalize_setting_value(key, value)` validates and normalizes before persisting:

- Boolean keys: Accepts `"1"/"true"/"yes"/"on"` → `True`, `"0"/"false"/"no"/"off"` → `False`.
- Integer keys: Converted via `int()`.
- `theme`: Validated against `THEME_PRESETS` (`forge`, `light`, `high_contrast`).
- `interface_mode`: Validated against `INTERFACE_MODES` (`tui`, `classic`).
- `default_armory_path`: Resolved via `Path.expanduser().resolve()`.
- `feature_flags`: Parsed from comma-separated string to `frozenset[str]`.
- Unknown keys raise `KeyError`.

### ChatConfig construction

`load_config()` in `hephaistos/parameters/cli.py` builds a `ChatConfig` by layering:

1. **TOML defaults** from `default.toml` (base_url, model_id, max_tokens).
2. **Provider config** from `ProviderConfig.load().apply_to_config()`. Falls back to Pollinations if the active provider has no API key.
3. **User overrides** from `load_raw_settings()` (base_url, model, max_tokens, rag_context_budget, feature_flags).
4. **Environment variables**: `HEPHAISTOS_BASE_URL`, `HEPHAISTOS_MODEL`, `HEPHAISTOS_MAX_TOKENS`, `HEPHAISTOS_RAG_CONTEXT_BUDGET`, `HEPHAISTOS_FEATURE_FLAGS`.

Each layer overrides the previous one, so environment variables take final precedence.

### CLI commands

| Command | Description |
|---|---|
| `/config show` | Display all current configuration values |
| `/config set <key> <value>` | Persist a normalized setting value |

### Default values (default.toml)

```toml
max_tokens = 4096
```

The TOML file intentionally provides only `max_tokens`. All other defaults come from the `AppSettings` dataclass. Theme defaults to `"forge"`, interface mode to `"tui"`, and all telemetry to off.

### Caching

Both `load_raw_settings()` and `ProviderConfig.load()` use in-process file-stamp caching:
- Cache key: `(mtime_ns, file_size)`.
- Invalidated automatically when the backing file changes.
- Manual invalidation via `invalidate_settings_cache()` and `invalidate_provider_cache()`.

## Integration points

- **Chat engine** ([chat-engine.md](chat-engine.md)): `ChatConfig` is populated by `load_config()`.
- **Provider config** ([provider-config.md](provider-config.md)): `load_config()` calls `ProviderConfig.load().apply_to_config()`.
- **Session management** ([session-management.md](session-management.md)): `ChatConfig` is passed to `create_session()`.
- **Shell** (`hephaistos/app/shell.py`): Reads `AppSettings` for theme, interface mode, and telemetry preferences.

## Key source files

| File | Lines | Role |
|---|---|---|
| `hephaistos/parameters/settings.py` | ~280 | Typed settings, persistence, normalization, caching |
| `hephaistos/parameters/cli.py` | ~250 | ChatConfig loading, /config show and /config set commands |
| `hephaistos/parameters/default.toml` | ~15 | Factory defaults |

## Entry points for modification

- **Add a new setting**: Add the key to the appropriate frozenset (`BOOL_KEYS`, `STRING_KEYS`, or `INT_KEYS`), add a field to `AppSettings`, and update `load_app_settings()` in `hephaistos/parameters/settings.py`.
- **Add a new theme**: Add to `THEME_PRESETS` in `hephaistos/parameters/settings.py`.
- **Change default values**: Edit `AppSettings` defaults or `default.toml`.
- **Add a new CLI config command**: Add a subparser and handler in `hephaistos/parameters/cli.py`.
