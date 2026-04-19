# CLI Reference

## CLI commands

```text
hephaistos armory init <path>         Create a new armory workspace
hephaistos armory open <path>         Validate an existing armory
hephaistos chat start <path>          Start a new chat session in an armory
hephaistos chat resume <path> <id>    Resume a saved chat session
hephaistos chat list <path>           List saved chat sessions
```

The top-level CLI is shell-first, so `chat` is implemented but hidden from `hephaistos --help`.

## Slash commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/status` | Show armory, session, model, memory, and usage state |
| `/save` | Save the current chat to the active armory |
| `/clear` | Start a fresh chat session |
| `/armory` | Open the armory management menu |
| `/chats` | List saved chats in the active armory |
| `/resume [id-prefix]` | Resume a saved chat by menu or session ID prefix |
| `/model` | Show or switch the active model |
| `/provider` | Show or switch the active provider and model |
| `/models` | List the built-in model catalog across providers |
| `/api` | Inspect or set the API key / base URL |
| `/compact` | Summarize the conversation to free context |
| `/history` | Show turn counts and a token estimate |
| `/persona` | Show or switch the agent persona |
| `/usage` | Show tracked token usage and estimated cost |
| `/edit` | Edit and resend the last user message |
| `/exit` | Leave the shell |

## Shell shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Alt+Enter` / `Esc+Enter` | Insert newline |
| `\` at end of line | Continue on the next line |
| `Up` / `Down` | Browse prompt history |
| `Tab` | Autocomplete slash commands |
| `Ctrl+C` | Cancel the current response |
| `Ctrl+D` | Exit the shell |
| `Ctrl+A` / `Ctrl+E` | Move to start / end of line |
| `Ctrl+U` / `Ctrl+K` | Clear to start / kill to end |

## Environment variables

| Variable | Description |
|----------|-------------|
| `HEPHAISTOS_API_KEY` | Generic API key override |
| `HEPHAISTOS_BASE_URL` | Override the API base URL |
| `HEPHAISTOS_MODEL` | Override the active model |
| `HEPHAISTOS_MAX_TOKENS` | Max output tokens per response |
| `HEPHAISTOS_RAG_CONTEXT_BUDGET` | Token budget for injected retrieval context |
| `HEPHAISTOS_MAX_RETRIES` | Max streaming retry attempts |
| `HEPHAISTOS_RETRY_BASE_DELAY` | Initial retry backoff in seconds |
| `HEPHAISTOS_RETRY_MAX_DELAY` | Max retry backoff in seconds |
| `HEPHAISTOS_LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |
| `HEPHAISTOS_LOG_FILE` | Optional append-only log file path |
| `HEPHAISTOS_LOG_FORMAT` | `json` or `text` for stderr logs |
| `HEPHAISTOS_EMBED_MODEL` | Override the embedding model used by retrieval |
| `HEPHAISTOS_RERANK_MODEL` | Override the reranker model when available |
| `OPENAI_API_KEY` | API key for the OpenAI-compatible provider path |
| `OPENROUTER_API_KEY` | API key for OpenRouter |
| `ZAI_API_KEY` | API key for Z.AI / GLM |
| `CUSTOM_API_KEY` | API key for the custom provider entry |
