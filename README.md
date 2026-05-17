<!-- Managed by scripts/sync_docs.py. Do not edit directly. -->

# Hephaistos

**A local-first document workspace for grounded answers, citations, memory, and recall practice with any LLM.**

Hephaistos helps you work with document-heavy projects. Create an armory, put your
materials inside it, and chat with an agent that retrieves the relevant
parts of those files before answering. After each answer, Hephaistos checks that the
citations point to evidence it actually retrieved, then stores armory memory for
that armory so you can continue where you left off.

Your workspace is just a folder on disk. Your materials, notes, saved chats,
retrieval index, and armory memory stay with the armory instead of being locked
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

Optional (needed for `/priority` PDF generation):

```bash
# macOS
brew install --cask mactex-no-gui

# Debian / Ubuntu
sudo apt install texlive-latex-extra latexmk

# Windows
winget install MiKTeX.MiKTeX
```

Without LaTeX, `/priority` saves a `.tex` draft and prints install guidance.

> **Zero-config**: Hephaistos uses Pollinations AI by default -- no API key
> or account needed. Just run `heph` and start working with your documents.

Upgrade later with:

```bash
uv tool upgrade hephaistos
```

You can also run `heph update` to see the correct update command for the
active executable.

Or install the latest main branch directly from GitHub:

```bash
uv tool install git+https://github.com/gildrb/hephaistos
```

Official release installs can optionally enable anonymous usage analytics and
crash reports from `/settings`. They are off by default. Source, editable, and
Git installs stay bare by default and do not show the privacy and diagnostics opt-in hint.

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

Optional benchmark extras are available for source checkouts:

```bash
uv sync --group beir           # BEIR external benchmark adapters
uv sync --group visualization  # matplotlib-backed benchmark summary visuals
```

Document conversion for files such as PDF, DOCX, PPTX, and XLSX is included in
the default install.

### Create An Armory

```bash
heph armory init ~/armories/exams
# Add source files to ~/armories/exams/materials
heph ~/armories/exams
```

If you `cd` into a valid armory first, `heph` attaches it automatically and
opens the interactive shell. From a source checkout, use `uv run heph`.
`hephaistos` is an equivalent long entrypoint. `heph start [path]` remains a hidden compatibility alias.

### Configure A Model

Inside the shell:

```text
/login
/models
```

You can also use environment variables such as `OPENROUTER_API_KEY`,
`OPENAI_API_KEY`, `ZAI_API_KEY`, `CUSTOM_API_KEY`, `HEPHAISTOS_BASE_URL`, and
`HEPHAISTOS_MODEL`. The default provider (Pollinations AI) works without any
API key.

### Privacy & Diagnostics

Use `/settings` for cross-session preferences such as:

- privacy and diagnostics opt-in for anonymous analytics and crash reports
- theme preset selection
- default startup armory fallback
- default model selection

Credential flows live in `/login` and `/logout`; model selection lives in `/models`.

PostHog is used only for anonymous, opt-in usage/error visibility for the
maintainer. Sentry is used only for redacted, opt-in crash reporting. The
public repository ships `hephaistos/privacy/release.py` as a safe stub;
official release builds inject privacy and diagnostics backend values during CI, and forks or custom
builds can provide `HEPHAISTOS_POSTHOG_PROJECT_TOKEN`,
`HEPHAISTOS_POSTHOG_HOST`, and `HEPHAISTOS_SENTRY_DSN`.

## Why Hephaistos

- **Armories are portable document workspaces.** An armory is a normal directory
  with materials, saved chats, retrieval state, and memory for that
  subject.
- **Answers are grounded in your files.** Hephaistos indexes `materials/`,
  retrieves relevant chunks for each question, and gives the model
  evidence IDs to cite.
- **Citations are checked after every answer.** The model must cite retrieved
  evidence like `[E1]`. Hephaistos verifies those IDs against the evidence from
  that exact turn and warns when citations are missing or invented.
- **Each armory remembers useful context.** After substantive exchanges,
  Hephaistos extracts learned concepts into `.hephaistos/memory.json` and uses
  that memory in future sessions for the same armory.
- **Guided learning is recall-first.** Hephaistos can present a material-backed
  solution, ask you to recall it, assess your attempt against the retrieved
  material, and give small hints instead of dumping the answer again. Material-
  backed reviews are scheduled with an FSRS-style stability/difficulty model
  that adjusts from your recall timing and effort.
- **The model is swappable.** Your armory is not tied to one LLM. Switch
  providers or models while keeping the same materials, chats, notes, and
  memory.

## How It Works

1. Put source files in `materials/`.
2. Start a chat in the armory.
3. For each material-backed question, Hephaistos builds or loads the local RAG
   index, retrieves relevant chunks, and passes them to the model as citable
   evidence.
4. The answer is checked for valid evidence citations.
5. Useful concepts from the exchange are saved as armory memory for later
   sessions.

If an armory has no materials, `heph <name-or-path>` asks you to add material before
starting a session.

## Armory Layout

```text
my-armory/
  materials/            # user source files, indexed for retrieval
  .hephaistos/
    armory.toml         # armory marker
    system_prompt.md    # optional custom armory prompt
    chats/              # saved chat sessions
    memory.json         # remembered concepts for this armory
    rag_index.json      # local retrieval index
```

Only `materials/` is retrieved for answers. Hidden files inside that folder are
skipped.

## Retrieval

Hephaistos works with plain text, Markdown, code, config files, CSV/TSV, HTML,
and other readable text formats out of the box. Markdown is chunked with heading
context, and other text files use semantic chunking when the optional RAG
dependencies are installed.

With `uv sync --group rag`, retrieval can use BM25, hybrid sparse plus
embedding retrieval, cross-encoder re-ranking, and query transformation.

Document files such as PDF, DOCX, PPTX, XLSX, ODT, ODS, ODP, and RTF are
converted into Markdown before indexing.

You can prebuild or refresh the index:

```bash
heph index ~/armories/exams
```

## Benchmarks

Hephaistos includes deterministic benchmark harnesses for retrieval, answer
grounding, document understanding, learning state, index integrity, academic item
extraction, model replay, and external corpus adapters. The committed academic
suite lives under `benchmarks/academic/`; public-corpus scaffolding and the
model evaluation prompt live under `benchmarks/public-academic/` and
`benchmarks/model-evaluation-prompt.md`.

Run the local deterministic suite from a source checkout:

```bash
uv run python -m scripts.run_benchmark_suite \
  --json-report .artifacts/benchmark-suite.json \
  --min-evidence-coverage 1.0
```

Run the comprehensive external workflow, including optional BEIR, standard RAG,
native, public-academic, and summary phases:

```bash
scripts/comprehensive_benchmark_run.sh \
  --output-dir .artifacts/comprehensive-benchmark \
  --fixture-mode
```

Use `--offline` to forbid network materialization, local `--beir-source-dir` or
`--beir-source-zip` inputs for BEIR runs, and `--require-beir-extra` or
`--require-visualization-extra` to fail early when optional extras are missing.
External runners write JSON reports with fixed retrieval parameters and redact
secret-like environment values before logs or Markdown summaries are written.

To run already materialized external inputs directly:

```bash
uv run python -m scripts.run_external_benchmarks \
  public-academic \
  public-academic \
  --suite path/to/materialized-suite \
  --json-report .artifacts/public-academic.report.json
```

Generate a human-readable summary from runner reports:

```bash
uv run python -m scripts.generate_benchmark_summary \
  .artifacts/public-academic.report.json \
  --output .artifacts/benchmark-summary.md
```

See `benchmarks/README.md` for dataset schemas, public/permissioned corpus
materialization, model-matrix evaluation, and strict completion-audit gates.

## Bring Your Own Model

Hephaistos is built around configurable providers, not a single required model.
The default provider config includes:

- Pollinations AI (free, zero-config default)
- OpenRouter
- OpenAI API key
- OpenAI Codex subscription
- Z.AI
- Custom OpenAI-compatible endpoint

Connect access inside the shell with `/login`, then switch models with `/models`.
You can also set `HEPHAISTOS_BASE_URL` and `HEPHAISTOS_MODEL` for your own endpoint.
The armory stays the same when the model changes.

## Common Commands

```text
heph                                   Open your current armory or plain chat.
heph <name-or-path>                    Open a known armory by name, e.g. `heph gdp`, or by path.
heph armory <name> [parent]            Create a named armory in ~/Armories or in <parent>/Armories.
heph armory init <name-or-path>        Create a new named armory folder.
heph armory open <path>                Open and validate an armory.
heph materials list <path>             List material files.
heph materials count <path>            Count material files.
heph materials index <path>            Build or refresh the RAG index.
heph index [path]                      Build or refresh the materials index; defaults to the current armory.
heph health [path]                     Check indexed materials for generic extraction problems; defaults to the current armory.
heph update                            Show how to update the active Hephaistos install.
heph chat resume <path> <id>           Resume an existing chat session.
heph chat ask <path> [prompt]          Ask one question without opening the TUI.
heph chat ask --jsonl <path> [prompt]  Emit structured turn events as JSON Lines for harness audits.
heph chat list <path>                  List chat sessions in an armory.
heph start [path]                      Hidden backwards-compatible alias for `heph [path]`.
heph tui [path]                        Explicit alias for the default Textual TUI.
```

Useful shell commands:

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
| /stats | Show session, armory, and learning progress stats |
| /priority | Generate a printable priority PDF cheat sheet |
| /mode | Set manual, guided, or autopilot learning mode |
| /autopilot | Let Heph drive a bounded autonomous learning session |
| /exam | Start an active-recall exam question |
| /export | Export the current session to a markdown file |
| /import | Import files into the armory materials directory |
| /remind | Show upcoming review reminders and due cards |
| /edit | Edit and resend the last user message |
| /models | Pick the active model |
| /recommend | Recommend models for sessions |
| /memory | Manage armory memory and Supermemory setup |
| /persona | Show or switch the agent persona |
| /settings | Manage cross-session preferences |
| /sessions | Switch between saved sessions |
| /index | Manage cross-armory search index |
| /usage | Show token usage and cost for this session |
| /vocab | Vocabulary drill with spaced repetition |

## Shell And Plugin Safety

Model-generated shell commands are not exposed as a default agent tool. The TUI
still supports explicit user-entered `!` shell escapes for local convenience.

Armory plugins in `.hephaistos/tools/*.py` are disabled by default because they
execute Python code. Set `HEPHAISTOS_TRUST_ARMORY_PLUGINS=1` only for armories
you control and trust.

## Custom Armory Prompts

Every armory can define its own assistant behavior with:

```text
my-armory/.hephaistos/system_prompt.md
```

Use it for modes like quiz practice, Socratic tutoring, exam drilling, debate,
or lecture-style explanations. Hephaistos still appends the source-grounding and
citation rules around the custom prompt.

## License

This project is licensed under the [MIT License](LICENSE).
