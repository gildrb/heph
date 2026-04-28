# Provider configuration

The provider configuration system manages multi-provider LLM endpoint definitions, model catalogs, and API key resolution. It reads provider definitions from `~/.config/hephaistos/providers.toml` and resolves API keys at runtime through a secure chain that never persists raw keys to config files.

## Purpose

- Define multiple LLM providers (Pollinations, OpenRouter, OpenAI Codex, Z.AI, custom) with endpoints, models, and key env vars.
- Persist provider selection and model choice across sessions.
- Provide a centralized model catalog with context windows, pricing, and capabilities.
- Resolve API keys securely via OS keychain → OAuth → environment variable → volatile store.

## Directory layout

```
hephaistos/providers/
├── config.py          # ProviderConfig, Provider, TOML persistence, in-process cache
├── registry.py        # ModelInfo, ModelRegistry, built-in model catalog
├── model_support.py   # Model/endpoint compatibility checks, prefix-based filtering
├── keyring_store.py   # API key resolution chain (keychain → OAuth → env → volatile)
├── oauth.py           # OAuth flow for subscription-based providers (see authentication.md)
└── __init__.py        # Package exports
```

## Key abstractions

| Abstraction | File | Purpose |
|---|---|---|
| `ProviderConfig` | `hephaistos/providers/config.py` | Top-level container: dict of `Provider` objects, active selection, TOML save/load |
| `Provider` | `hephaistos/providers/config.py` | Single provider definition: slug, endpoint, API key env var, model list, active state |
| `ModelInfo` | `hephaistos/providers/registry.py` | Model metadata: name, provider, context window, pricing, tags |
| `ModelRegistry` | `hephaistos/providers/registry.py` | Lookup table for model metadata with prefix matching |
| `resolve_key()` | `hephaistos/providers/keyring_store.py` | Full key resolution chain |

## How it works

### Provider config management

`ProviderConfig` is stored as TOML at `~/.config/hephaistos/providers.toml`. Each section defines a provider:

```toml
[pollinations]
display_name = "Pollinations AI (free)"
endpoint = "https://text.pollinations.ai/openai"
active = true
current_model = "openai"
models = ["openai", "openai-large", "mistral", "gemini"]

[openrouter]
display_name = "OpenRouter"
endpoint = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"
models = ["openai/gpt-5.4", "google/gemini-3-pro-preview", ...]
```

**Loading**:
1. `ProviderConfig.load()` reads the TOML file (or returns `default_config()` if absent).
2. Each section is parsed by `_sanitize_provider()` which validates models against `model_support.filter_supported_models()`.
3. Results are cached in-process via `_provider_cache()`. The cache is invalidated when the file's mtime/size changes or when `invalidate_provider_cache()` is called.

**Applying to ChatConfig**:
`apply_to_config(config)` sets the base URL, model, and a provider reference (slug + env var) on the `ChatConfig`. The API key is not stored directly — the engine resolves it lazily via `config.resolved_api_key`.

### Model registry

`ModelRegistry` in `hephaistos/providers/registry.py` provides a centralized model catalog:

- **`_BUILTIN_MODELS`**: Hardcoded list of `ModelInfo` entries covering all supported models across Pollinations, OpenAI, Google, Qwen, Z.AI, and others.
- **Lookup**: `get(model_name)` tries exact match, then strips provider prefix (`openai/gpt-5.4` → `gpt-5.4`), then tries adding prefixes.
- **Metadata per model**: Context window size, max output tokens, prompt/completion pricing per 1K tokens, and tags (free, study, reasoning, etc.).

### Model compatibility

`hephaistos/providers/model_support.py` enforces model/endpoint compatibility:

- Each provider has a set of model name prefixes (e.g., `openai-codex` → `gpt-`, `zai` → `glm-`).
- `is_supported_model_for_endpoint()`: Checks if a model name matches the known families for a given base URL.
- `is_supported_model_for_provider()`: Same check but using provider slug instead of URL.
- `filter_supported_models()`: Filters a model list to only those valid for a given provider.

### API key resolution chain

`resolve_key(slug, env_var)` in `hephaistos/providers/keyring_store.py` follows this priority:

1. **`HEPHAISTOS_API_KEY` environment variable** — global override, takes precedence over everything.
2. **OS keychain** — stored via `keyring` library (macOS Keychain, Linux Secret Service, Windows Credential Manager). Service name: `hephaistos:<slug>`, username: `api_key`. Results cached in-process.
3. **OAuth credentials** — auto-refreshed access token (see [authentication.md](authentication.md)).
4. **Provider-specific environment variable** — the `api_key_env` field (e.g., `OPENROUTER_API_KEY`).
5. **Volatile in-memory store** — set via `/api key` CLI command, session-scoped only.

Keys are never written to config files. `mask_key()` provides a safe display format (`abcd...efgh`).

### Key management commands

| Command | Action |
|---|---|
| `/api key <value>` | Store key in OS keychain (or volatile if keychain unavailable) |
| `/api key --show` | Display masked key for active provider |
| `/api key --clear` | Remove key from keychain |

### Default providers

The built-in `default_config()` includes:

| Provider | Slug | Endpoint | Key required |
|---|---|---|---|
| Pollinations AI | `pollinations` | `https://text.pollinations.ai/openai` | No |
| OpenRouter | `openrouter` | `https://openrouter.ai/api/v1` | Yes (`OPENROUTER_API_KEY`) |
| OpenAI Codex | `openai-codex` | `https://api.openai.com/v1` | Yes (OAuth or `OPENAI_API_KEY`) |
| Z.AI / GLM | `zai` | `https://api.z.ai/api/paas/v4/` | Yes (`ZAI_API_KEY`) |
| Custom | `custom` | `https://api.z.ai/api/coding/paas/v4` | Yes (`CUSTOM_API_KEY`) |

Pollinations is the default active provider because it requires no API key.

## Integration points

- **Chat engine** ([chat-engine.md](chat-engine.md)): `ChatConfig.resolved_api_key` delegates to `resolve_key()`.
- **Parameters CLI** (`hephaistos/parameters/cli.py`): `load_config()` calls `ProviderConfig.load().apply_to_config()`.
- **Session management** ([session-management.md](session-management.md)): `ChatConfig` is populated before session creation.
- **OAuth** ([authentication.md](authentication.md)): OAuth tokens are checked during key resolution (step 3).

## Key source files

| File | Lines | Role |
|---|---|---|
| `hephaistos/providers/config.py` | ~300 | Provider definitions, TOML persistence, caching |
| `hephaistos/providers/registry.py` | ~470 | Model catalog with metadata, pricing, context windows |
| `hephaistos/providers/keyring_store.py` | ~120 | API key resolution chain, keychain storage |
| `hephaistos/providers/model_support.py` | ~80 | Model/endpoint compatibility filtering |

## Entry points for modification

- **Add a new provider**: Add a `Provider` entry in `default_config()` in `hephaistos/providers/config.py` and a `ModelInfo` entry in `hephaistos/providers/registry.py`.
- **Add a new model**: Add a `ModelInfo` to `_BUILTIN_MODELS` and update the provider's model list in `default_config()`.
- **Change key resolution order**: Edit `resolve_key()` in `hephaistos/providers/keyring_store.py`.
- **Change model compatibility rules**: Edit `_PROVIDER_PREFIXES` and `_ENDPOINT_PREFIXES` in `hephaistos/providers/model_support.py`.
