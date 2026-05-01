<!-- Managed by scripts/sync_docs.py. Do not edit directly. -->

# Hephaistos

**A local-first study agent that works with your files and any LLM.**

Hephaistos helps you study from your own material. Create an armory, put your
study materials inside it, and chat with an agent that retrieves the relevant
parts of those files before answering. After each answer, Hephaistos checks that the
citations point to evidence it actually retrieved, then stores study memory for
that armory so you can continue where you left off.

Your workspace is just a folder on disk. Your materials, notes, saved chats,
retrieval index, and study memory stay with the armory instead of being locked
inside one model vendor's project format. Use Pollinations AI (free, zero-config),
OpenRouter, OpenAI, Z.AI, or any OpenAI-compatible endpoint you configure.

## Quickstart

### Requirements

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/)

### Install

Install the public CLI globally with `uv`:

```bash
uv tool install hephaistos
heph
heph --version
```

> **Zero-config**: Hephaistos uses Pollinations AI by default -- no API key
> or account needed. Just run `heph` and start studying.

Upgrade later with:

```bash
uv tool upgrade hephaistos
```

Or install the latest main branch directly from GitHub:

```bash
uv tool install git+https://github.com/gildrb/hephaistos
```

Official release installs can optionally enable anonymous usage analytics and
crash reports from `/settings`. They are off by default. Source, editable, and
Git installs stay bare by default and do not show the telemetry opt-in hint.

### From Source

For development or contributor workflows:

```bash
git clone https://github.com/gildrb/hephaistos
cd hephaistos
uv sync --group dev
```

Optional: enable BM25, embedding retrieval, and cross-encoder re-ranking from a source
checkout.

```bash
uv sync --group rag
```

Optional: enable document conversion for files such as PDF, DOCX, PPTX, and
XLSX.

```bash
uv sync --group docling
```

### Create An Armory

```bash
heph armory init ~/armories/exams
# Add study files to ~/armories/exams/source or ~/armories/exams/library
heph ~/armories/exams
```

If you `cd` into a valid armory first, `heph` attaches it automatically and
opens the interactive shell. From a source checkout, use `uv run heph`.
`hephaistos` is an equivalent long entrypoint. `heph start [path]` remains a hidden compatibility alias.

### Configure A Model

Inside the shell:

```text
/provider
/models
/api key <your-key>
```

You can also use environment variables such as `OPENROUTER_API_KEY`,
`OPENAI_API_KEY`, `ZAI_API_KEY`, `CUSTOM_API_KEY`, `HEPHAISTOS_BASE_URL`, and
`HEPHAISTOS_MODEL`. The default provider (Pollinations AI) works without any
API key.

### Settings And Telemetry

Use `/settings` for cross-session preferences such as:

- telemetry opt-in for anonymous analytics and crash reports
- theme preset selection
- default startup armory fallback
- default model selection

Credential flows stay on their existing commands: `/provider`, `/api`,
`/login`, and `/logout`.

PostHog is used only for anonymous, opt-in usage/error visibility for the
maintainer. Sentry is used only for redacted, opt-in crash reporting. The
public repository ships `hephaistos/_telemetry_release.py` as a safe stub;
official release builds inject telemetry values during CI, and forks or custom
builds can provide `HEPHAISTOS_POSTHOG_PROJECT_TOKEN`,
`HEPHAISTOS_POSTHOG_HOST`, and `HEPHAISTOS_SENTRY_DSN`.

## Why Hephaistos

- **Armories are portable study workspaces.** An armory is a normal directory
  with primary materials, reference material, notes, saved chats, retrieval state,
  and memory for that subject.
- **Answers are grounded in your files.** Hephaistos indexes `source/` and
  `library/`, retrieves relevant chunks for each question, and gives the model
  evidence IDs to cite.
- **Citations are checked after every answer.** The model must cite retrieved
  evidence like `[E1]`. Hephaistos verifies those IDs against the evidence from
  that exact turn and warns when citations are missing or invented.
- **Each armory remembers what you studied.** After substantive exchanges,
  Hephaistos extracts learned concepts into `.hephaistos/memory.json` and uses
  that memory in future sessions for the same armory.
- **The study loop is recall-first.** Hephaistos can present a material-backed
  solution, ask you to recall it, assess your attempt against the retrieved
  material, and give small hints instead of dumping the answer again.
- **The model is swappable.** Your armory is not tied to one LLM. Switch
  providers or models while keeping the same materials, chats, notes, and
  memory.

## How It Works

1. Put primary material in `source/` and reference material in `library/`.
2. Start a chat in the armory.
3. For each material-backed question, Hephaistos builds or loads the local RAG
   index, retrieves relevant chunks, and passes them to the model as citable
   evidence.
4. The answer is checked for valid evidence citations.
5. Useful concepts from the exchange are saved as armory memory for later
   sessions.

If an armory has no study materials, `heph <path>` asks you to add material before
starting a study session.

## Armory Layout

```text
my-armory/
  source/               # primary study material, indexed for retrieval
  library/              # extra reference material, indexed for retrieval
  notes/                # notes and summaries the agent can write
  chats/                # saved chat sessions
  parameters/           # armory-specific parameter files
  .hephaistos/
    armory.toml         # armory marker
    system_prompt.md    # optional custom study prompt
    memory.json         # remembered concepts for this armory
    rag_index.json      # local retrieval index
```

Only `source/` and `library/` are retrieved for answers. Hidden files inside
those folders are skipped. In docs and code, **materials** means this study-file
domain. `source/` remains the on-disk folder for primary materials, and
`source` in citations still means the provenance path for a retrieved chunk.

## Retrieval

Hephaistos works with plain text, Markdown, code, config files, CSV/TSV, HTML,
and other readable text formats out of the box. Markdown is chunked with heading
context, and other text files use semantic chunking when the optional RAG
dependencies are installed.

With `uv sync --group rag`, retrieval can use BM25, hybrid sparse plus
embedding retrieval, cross-encoder re-ranking, and query transformation.

With `uv sync --group docling`, document files such as PDF, DOCX, PPTX, XLSX,
ODT, ODS, ODP, and RTF can be converted into Markdown before indexing.

You can prebuild or refresh the index:

```bash
heph materials index ~/armories/exams
```

## Bring Your Own Model

Hephaistos is built around configurable providers, not a single required model.
The default provider config includes:

- Pollinations AI (free, zero-config default)
- OpenRouter
- OpenAI
- Z.AI
- Custom OpenAI-compatible endpoint

Switch inside the shell with `/provider` and `/models`, or set
`HEPHAISTOS_BASE_URL` and `HEPHAISTOS_MODEL` for your own endpoint. The armory
stays the same when the model changes.

## Common Commands

```text
heph                          Launch the TUI in plain-chat mode or attach the current armory.
heph <path>                   Launch the TUI attached to a specific armory path.
heph armory init <path>       Create a new armory folder.
heph armory open <path>       Open and validate an armory.
heph materials list <path>    List study material files.
heph materials count <path>   Count study material files.
heph materials index <path>   Build or refresh the RAG index.
heph chat resume <path> <id>  Resume an existing chat session.
heph chat list <path>         List chat sessions in an armory.
heph start [path]             Hidden backwards-compatible alias for `heph [path]`.
heph tui [path]               Explicit alias for the default Textual TUI.
```

Useful shell commands:

| Command | Description |
|---|---|
| /help | Show available commands |
| /exit | Leave the shell |
| /login | Authenticate via OAuth |
| /logout | Clear stored OAuth credentials |
| /status | Show armory, session, and model info |
| /save | Save current chat to armory |
| /clear | Start a fresh chat session |
| /new | Start a new chat (saves previous automatically) |
| /armory | Browse, open, or create armories |
| /chats | List saved chats in the active armory |
| /sessions | List or resume saved sessions |
| /resume [id-prefix] | Resume the latest saved chat, or pass an ID prefix |
| /api | Manage API key (keychain) or base URL |
| /compact | Summarize conversation to reduce context size |
| /history | Show conversation turn count and token estimate |
| /evidence | Show retrieved evidence for the last turn |
| /tokens | Show or hide live token estimates |
| /cost | Show or hide live cost estimates |
| /stats | Show session, armory, and study progress stats |
| /export | Export the current session to a markdown file |
| /import | Import files into the armory materials directory |
| /remind | Show upcoming study reminders and due cards |
| /edit | Edit and resend the last user message |
| /provider | Show or switch LLM provider and model |
| /models | Pick the active model |
| /recommend | Recommend models for study sessions |
| /memory | Manage study memory and Supermemory setup |
| /persona | Show or switch the agent persona |
| /settings | Manage cross-session preferences |
| /index | Manage cross-armory search index |
| /usage | Show token usage and cost for this session |
| /vocab | Vocabulary drill with spaced repetition |

## RTK Shell Output Compression

Hephaistos can optionally route simple model-generated `bash` tool calls through
[`rtk`](https://github.com/rtk-ai/rtk) before the output is returned to the
model. This is disabled by default and only affects agent tool calls, not
user-entered `!` shell escapes in the TUI.

```bash
export HEPHAISTOS_RTK=1
export HEPHAISTOS_RTK_ULTRA=1                  # optional
export HEPHAISTOS_RTK_MIN_COMMAND_CHARS=20     # optional
```

Commands that use shell metacharacters such as pipes, redirects, or control
operators run normally so shell behavior stays unchanged. If `rtk` is not
installed, Hephaistos falls back to the original command output.

## Custom Study Prompts

Every armory can define its own study behavior with:

```text
my-armory/.hephaistos/system_prompt.md
```

Use it for modes like quiz practice, Socratic tutoring, exam drilling, debate,
or lecture-style explanations. Hephaistos still appends the source-grounding and
citation rules around the custom prompt.

## Next Steps

- Read the [CLI reference](cli-reference.md) for commands and keyboard shortcuts.
- Read the [Agent API docs](api/agent.md) for dispatch, tools, and citation modules.
- Read the [RAG API docs](api/rag.md) for retrieval, indexing, and chunking modules.
- Read the [memory API docs](api/memory.md) for per-armory study memory.
