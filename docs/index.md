# Hephaistos

**A local-first study agent that works with your files and any LLM.**

Hephaistos helps you study from your own material. Create an armory, put your
source files inside it, and chat with an agent that retrieves the relevant parts
of those files before answering. After each answer, Hephaistos checks that the
citations point to evidence it actually retrieved, then stores study memory for
that armory so you can continue where you left off.

Your workspace is just a folder on disk. Your source files, notes, saved chats,
retrieval index, and study memory stay with the armory instead of being locked
inside one model vendor's project format. Use OpenRouter, OpenAI, Z.AI, or any
OpenAI-compatible endpoint you configure.

## Quickstart

### Requirements

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/)
- An API key or compatible local/hosted LLM endpoint

### Install

Install the public CLI globally with `uv`:

```bash
uv tool install hephaistos
heph --version
```

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

Optional: enable embedding retrieval and cross-encoder re-ranking from a source checkout.

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
heph chat start ~/armories/exams
```

If you `cd` into a valid armory first, `heph` will attach it automatically and
open the interactive shell. From a source checkout, use `uv run heph`.

### Configure A Model

Inside the shell:

```text
/provider
/model
/api key <your-key>
```

You can also use environment variables such as `OPENROUTER_API_KEY`,
`OPENAI_API_KEY`, `ZAI_API_KEY`, `CUSTOM_API_KEY`, `HEPHAISTOS_BASE_URL`, and
`HEPHAISTOS_MODEL`.

### Settings And Telemetry

Use `/settings` for cross-session preferences such as telemetry opt-in, theme
presets, a default startup armory, and the default model. Credential flows stay
on `/provider`, `/api`, `/login`, and `/logout`.

Forks and custom builds can supply their own telemetry env vars:
`HEPHAISTOS_POSTHOG_PROJECT_TOKEN`, `HEPHAISTOS_POSTHOG_HOST`, and
`HEPHAISTOS_SENTRY_DSN`. Official release builds inject those values during CI;
the public repository only ships a stub module.

## Why Hephaistos

- **Armories are portable study workspaces.** An armory is a normal directory
  with source files, reference material, notes, saved chats, retrieval state,
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
- **The study loop is recall-first.** Hephaistos can present a source-backed
  solution, ask you to recall it, assess your attempt against the retrieved
  source, and give small hints instead of dumping the answer again.
- **The model is swappable.** Your armory is not tied to one LLM. Switch
  providers or models while keeping the same source files, chats, notes, and
  memory.

## How It Works

1. Put primary material in `source/` and reference material in `library/`.
2. Start a chat in the armory.
3. For each source-backed question, Hephaistos builds or loads the local RAG
   index, retrieves relevant chunks, and passes them to the model as citable
   evidence.
4. The answer is checked for valid evidence citations.
5. Useful concepts from the exchange are saved as armory memory for later
   sessions.

If an armory has no source files, `chat start` asks you to add material before
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
those folders are skipped.

## Bring Your Own Model

Hephaistos is built around configurable providers, not a single required model.
The default provider config includes OpenRouter, OpenAI, Z.AI, and a custom
OpenAI-compatible endpoint.

Switch inside the shell with `/provider` and `/model`, or set
`HEPHAISTOS_BASE_URL` and `HEPHAISTOS_MODEL` for your own endpoint. The armory
stays the same when the model changes.

## Next Steps

- Read the [CLI reference](cli-reference.md) for commands and shell shortcuts.
- Read the [RAG API docs](api/harness.md) for retrieval and citation modules.
- Read the [memory API docs](api/memory.md) for per-armory study memory.
