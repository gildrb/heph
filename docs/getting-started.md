# Getting Started

## Install

Heph requires **Python 3.13+**.

### Using UV (recommended)

Install UV:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then Heph:

```bash
uv tool install heph@latest
heph
heph --version
```

### Using Pip

```bash
pip install heph
```

The default install indexes Markdown, text, and code files. It can also extract
text-layer PDFs when `pdftotext` is installed. Install
`pip install 'heph[documents]'` for DOCX, PPTX, XLSX, and other Docling formats.

### Upgrade

```bash
heph update
```

### From Source

```bash
git clone https://github.com/gildrb/heph
cd heph
uv sync --frozen --group dev
uv run heph
```

## Create an Armory

An armory is a normal folder containing materials, chat history, retrieval
index, traces, usage snapshots, and local memory.

```bash
heph armory init [name]
cd ~/.armories/[name]
# Add materials to the materials/ directory
```

Named armories are stored in `~/.armories`. To move Heph to another PC, install
Heph, copy or sync the `.armories` folder, set up provider credentials, and run
`heph`.

You can open a new armory before adding documents. Heph stays attached to the
armory and shows a no-materials state until files are present in `materials/`.

## Add Documents

Place files in the armory's `materials/` directory:

```bash
~/.armories/[name]/
├── materials/
│   ├── [file].pdf
│   ├── [file].pdf
│   └── [file].md
└── .harness/
    ├── armory.toml
    ├── chats/
    ├── traces/
    └── usage/
```

Supported formats:
- PDF
- Markdown
- Plain text
- DOCX, PPTX, and XLSX
- Common code files

## Start Heph

```bash
heph [name]
```

Or with an explicit armory path:

```bash
heph ~/.armories/[name]
heph .
```

## Configure a Model

On first launch, Heph will prompt you to configure a model. Use `/login` to connect:

1. **Pollinations AI** - Free, no account required
2. **OpenRouter** - API key required
3. **OpenAI** - API key or subscription login
4. **Z.AI** - API key required
5. **Custom endpoint** - Any OpenAI-compatible API

You can also set environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export OPENROUTER_API_KEY="sk-..."
export ZAI_API_KEY="sk-..."
```

## Ask Questions

Once configured, ask questions about your materials:

```
What are the key concepts from chapter 1?
Explain the difference between X and Y based on the textbook.
Summarize the main arguments in the lecture notes.
```

Heph will:
1. Search your documents for relevant information
2. Retrieve the most relevant passages
3. Generate an answer based on your materials
4. Show you the sources it used
5. Save armory-scoped memory

## Key Commands

Inside Heph:
- `/login` - Configure model access
- `/local` - Manage local llama.cpp models
- `/models` - Choose an available model
- `/armory` - Open or create armories
- `/materials` - Choose which materials are used for retrieval
- `/keymap` - Edit active keyboard shortcuts
- `/detach` - Leave the current armory and continue without one
- `/evidence` - See retrieval evidence for the last answer
- `/turn` - Inspect the current or last request
- `/settings` - Configure privacy, diagnostics, and other options
- `/exit` - Quit Heph

CLI commands:
- `heph [name-or-path]` - Open Heph for an armory
- `heph armory init [name]` - Create a new armory in `~/.armories`
- `heph index [path]` - Refresh the materials index
- `heph health [path]` - Check indexed materials
- `heph update` - Update the released install

## Read Next

- [Configuration](configuration.md) - Configure models, privacy, and behavior
- [Armories](armories.md) - Understand how armories work
- [Privacy](privacy.md) - Learn about privacy and data handling
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
