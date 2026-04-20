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

```bash
uv sync
```

Optional: enable embedding retrieval and cross-encoder re-ranking.

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
uv run hephaistos armory init ~/armories/exams
# Add study files to ~/armories/exams/source or ~/armories/exams/library
uv run hephaistos chat start ~/armories/exams
```

If you `cd` into a valid armory first, `uv run hephaistos` will attach it
automatically and open the interactive shell.

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

### Install The Shortcut

```bash
uv tool install --force --editable .
heph
```

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

## Retrieval

Hephaistos works with plain text, Markdown, code, config files, CSV/TSV, HTML,
and other readable text formats out of the box. Markdown is chunked with heading
context, and other text files use semantic chunking when the optional RAG
dependencies are installed.

With `uv sync --group rag`, retrieval can use hybrid TF-IDF plus embeddings,
cross-encoder re-ranking, and query transformation.

With `uv sync --group docling`, document files such as PDF, DOCX, PPTX, XLSX,
ODT, ODS, ODP, and RTF can be converted into Markdown before indexing.

You can prebuild or refresh the index:

```bash
uv run hephaistos source index ~/armories/exams
```

## Bring Your Own Model

Hephaistos is built around configurable providers, not a single required model.
The default provider config includes:

- OpenRouter
- OpenAI
- Z.AI
- Custom OpenAI-compatible endpoint

Switch inside the shell with `/provider` and `/model`, or set
`HEPHAISTOS_BASE_URL` and `HEPHAISTOS_MODEL` for your own endpoint. The armory
stays the same when the model changes.

## Common Commands

```text
hephaistos armory init <path>         Create a new armory
hephaistos armory open <path>         Validate an existing armory
hephaistos source list <path>         List source and library files
hephaistos source count <path>        Count source and library files
hephaistos source index <path>        Build or refresh the retrieval index
hephaistos chat start <path>          Start a new study session
hephaistos chat resume <path> <id>    Resume a saved session
hephaistos chat list <path>           List saved sessions
```

Useful shell commands:

| Command | Description |
|---------|-------------|
| `/armory` | Open, create, detach, or browse armories |
| `/chats` | List saved chats in the active armory |
| `/resume [id-prefix]` | Resume a saved chat |
| `/save` | Save the current chat |
| `/provider` | Switch provider |
| `/model` | Switch model |
| `/api key <key>` | Set an API key for the active provider |
| `/persona` | Switch study style |
| `/compact` | Summarize a long conversation to free context |
| `/exit` | Leave the shell |
| `/quit` | Leave the shell |

## Custom Study Prompts

Every armory can define its own study behavior with:

```text
my-armory/.hephaistos/system_prompt.md
```

Use it for modes like quiz practice, Socratic tutoring, exam drilling, debate,
or lecture-style explanations. Hephaistos still appends the source-grounding and
citation rules around the custom prompt.

## License

This project is licensed under the [MIT License](LICENSE).
