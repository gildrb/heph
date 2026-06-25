# Getting Started

## Install

Hephaion requires **Python 3.13+**.

### Quick Install

```bash
uv tool install heph@latest
heph
heph --version
```

### With pip

```bash
pip install heph
```

PDF, DOCX, PPTX, and XLSX conversion support is built in through
`docling-slim[standard]`.

### Upgrade

```bash
uv tool upgrade heph
```

### From Source

```bash
git clone https://github.com/gildrb/heph
cd heph
uv sync --frozen --group dev
uv run heph
```

## Create an Armory

An armory is a normal folder containing your documents, chat history, retrieval index, and local memory.

```bash
heph armory init exams
cd ~/.armories/exams
# Add your documents to the materials/ directory
```

Named armories are stored in `~/.armories`. To move Heph to another PC, install
Heph, copy or sync the `.armories` folder, set up provider credentials, and run
`heph`.

You can open a new armory before adding documents. Heph stays attached to the
armory and shows a no-materials state until files are present in `materials/`.

## Add Documents

Place your documents in the `materials/` directory of your armory:

```bash
~/.armories/exams/
├── materials/
│   ├── lecture-notes.pdf
│   ├── textbook-chapter1.pdf
│   └── reference-doc.md
└── .hephaion/
    ├── armory.toml
    ├── chats/
    ├── traces/
    └── usage/
```

Supported formats:
- PDF
- Markdown
- Plain text
- Code files
- Many other document formats (via Docling)

## Start Heph

```bash
heph exams
```

Or with an explicit armory path:

```bash
heph ~/.armories/exams
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

Once configured, start asking questions about your documents:

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
5. Keep track of what you've learned in memory

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
- `heph armory init NAME` - Create a new armory in `~/.armories`
- `heph index [path]` - Refresh the materials index
- `heph health [path]` - Check indexed materials
- `heph update` - Show the update command

## Next Steps

- [Configuration](configuration.md) - Configure models, privacy, and behavior
- [Armories](armories.md) - Understand how armories work
- [Privacy](privacy.md) - Learn about privacy and data handling
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
