# Systems

Active contributors: Gil

Hephaistos is built from several tightly-scoped systems that collaborate through well-defined interfaces. Each system lives in its own package and owns a single concern.

| System | Package | One-line summary |
|---|---|---|
| [Chat engine](chat-engine.md) | `hephaistos/chat` | Streaming LLM API calls with retry, circuit breaking, and token tracking |
| [Agent harness](agent-harness.md) | `hephaistos/harness` | The model/tool dispatch loop, tool registry, RAG, and persona system |
| [Session management](session-management.md) | `hephaistos/chat/session.py` | Chat session lifecycle — creation, persistence, and turn orchestration |
| [Provider configuration](provider-config.md) | `hephaistos/providers` | Multi-provider LLM endpoint management, model catalog, and key resolution |
| [Authentication](authentication.md) | `hephaistos/providers/oauth.py` | OAuth Authorization Code + PKCE flow for subscription-based providers |
| [Parameters and settings](parameters-and-settings.md) | `hephaistos/parameters` | Typed user-facing configuration persisted to `config.json` |

## How they connect

```
User input → Session management → Turn orchestrator
                                    │
                     ┌──────────────┤
                     │              │
              Chat engine      Agent harness
              (streaming)      (tool dispatch, RAG)
                     │              │
                 Provider config    │
                 (keys, models)     │
                     │              │
                 Authentication  Tool registry
                                   │
                              Parameters / settings
```

Import boundaries are enforced: only `app` may import other packages; all other packages are forbidden from importing `app` (checked by `lint-imports`).
