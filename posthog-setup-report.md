<wizard-report>
# PostHog post-wizard report

The wizard has completed a deep integration of PostHog analytics into the Hephaistos CLI. A new `hephaistos/analytics.py` module was created to provide an optional, no-op-safe PostHog client that is initialised at startup via environment variables. A stable per-installation UUID (stored in `~/.cache/hephaistos/install_id`) is used as the `distinct_id` so that sessions are correlated over time without collecting any PII. The `posthog` package was added to the project dependencies, and `POSTHOG_PROJECT_TOKEN` / `POSTHOG_HOST` were written to `.env`.

| Event | Description | File |
|---|---|---|
| `session_started` | User starts the interactive chat shell — top of the conversion funnel | `hephaistos/app/shell.py` |
| `message_sent` | User sends a chat message to the LLM | `hephaistos/app/shell.py` |
| `llm_request_failed` | LLM request fails (engine error or stream recovery error) | `hephaistos/app/shell.py` |
| `session_saved` | User saves the current chat session to the armory | `hephaistos/app/commands.py` |
| `session_resumed` | User resumes a previously saved chat session | `hephaistos/app/workspace.py` |
| `provider_switched` | User switches the active LLM provider via `/provider use` | `hephaistos/app/commands.py` |
| `model_switched` | User switches to a different model via `/model` | `hephaistos/app/commands.py` |
| `login_completed` | User successfully authenticates via OAuth (`/login`) | `hephaistos/app/commands.py` |
| `logout_completed` | User clears stored OAuth credentials (`/logout`) | `hephaistos/app/commands.py` |
| `conversation_compacted` | User compacts the conversation to reduce context size (`/compact`) | `hephaistos/app/commands.py` |
| `conversation_cleared` | User starts a fresh chat session (`/clear`) | `hephaistos/app/commands.py` |
| `armory_initialized` | User creates a new armory workspace via CLI | `hephaistos/armory/cli.py` |
| `api_key_configured` | User sets or updates an API key via `/api key` | `hephaistos/app/commands.py` |

## Next steps

We've built some insights and a dashboard for you to keep an eye on user behavior, based on the events we just instrumented:

- **Dashboard — Analytics basics**: https://eu.posthog.com/project/163054/dashboard/632930
- **Session starts over time**: https://eu.posthog.com/project/163054/insights/5EzZ9SF1
- **Messages sent per day**: https://eu.posthog.com/project/163054/insights/RjiTc35p
- **Session → Message sent conversion funnel**: https://eu.posthog.com/project/163054/insights/zqu9wWej
- **LLM request failures over time**: https://eu.posthog.com/project/163054/insights/ASPtIp3Y
- **Provider switch events**: https://eu.posthog.com/project/163054/insights/HKwISBiA

### Agent skill

We've left an agent skill folder in your project. You can use this context for further agent development when using Claude Code. This will help ensure the model provides the most up-to-date approaches for integrating PostHog.

</wizard-report>
