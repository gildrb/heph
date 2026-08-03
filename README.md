<!-- Managed by scripts/sync_docs.py. Do not edit directly. -->

<p align="center">
  <img alt="Heph" src="assets/logo-auto.svg" width="280">
</p>

<p align="center">
  Local agent for accurate, cited answers from your files
</p>

<p align="center">
  <a href="https://raw.githubusercontent.com/gildrb/heph/main/assets/app-screenshot.png?v=c83c45bf619c">
    <img alt="Heph TUI" src="assets/app-screenshot.png?v=c83c45bf619c" width="100%">
  </a>
</p>

## Quick Start

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Heph
uv tool install heph@latest

# Create an armory for your files
heph armory init [name]

# Add materials that Heph can answer from
cp ~/Downloads/[file] ~/.armories/[name]/materials/

# Start Heph in that armory
heph [name]
```

## Armory layout

An armory is a normal folder:

```text
~/.armories/[name]/
├── materials/            # PDFs, Office docs, notes, code to cite
│   ├── [file].pdf
│   └── [file].md
├── .harness/             # Local Heph state
│   ├── armory.toml       # Armory marker
│   ├── rag_index.json    # Retrieval index
│   ├── memory.json       # Armory memory
│   ├── chats/            # Saved sessions
│   ├── traces/           # JSONL traces when enabled
│   ├── usage/            # Token and cost snapshots
│   └── ignore            # Indexing ignore rules
└── README.md             # Armory notes
```

`materials/` holds files Heph can index and cite. `.harness/` holds local state:
the retrieval index, memory, chats, traces, usage snapshots, and ignore rules.
Copy or sync the armory folder to move work between machines; configure provider
credentials again on each machine.

Read [Armories](docs/armories.md) for storage, indexing, and memory details.

## Installation

> [!NOTE]
> Heph is currently in beta, so unexpected issues may occur. Please report them if
> they have not already been reported.

### Using UV (recommended)

Install UV:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then Heph:

```bash
uv tool install heph@latest
```

### Using Pip

```bash
pip install heph
```

The default install is intentionally lean. The following measurements are total
Linux virtualenv sizes (including workspace packages), not deltas. OCR model
downloads are not included.

| Profile | Adds | Total installed Linux profile | Without it |
| --- | --- | --- | --- |
| default | Lean fallbacks | 41 distributions / 38.7 MiB | — |
| `search` | Accelerated BM25 | 43 distributions / 93.8 MiB | stdlib BM25 |
| `embeddings` | Embeddings, chunking, reranking | 87 distributions / 4.7 GiB | stdlib TF-IDF |
| `documents` | Docling extraction | 142 distributions / 5.0 GiB | text and `pdftotext` PDFs |
| `all` | All optional backends | 147 distributions / 5.1 GiB | lean fallbacks |

Install an extra with, for example, `pip install 'heph[documents]'`. The
`documents` profile also supports OCR and downloads OCR models on first use;
those model files are not included in the size measurements.

### Updating

```bash
heph update
```

Check the installed version:

```bash
heph --version
```

## Docs

[Getting started](docs/getting-started.md)<br>
[Armories](docs/armories.md)<br>
[CLI reference](docs/cli-reference.md)<br>
[Configuration](docs/configuration.md)<br>
[Models](docs/models.md)<br>
[Trust and ownership](docs/trust.md)<br>
[Privacy](docs/privacy.md)<br>
[Architecture](docs/architecture.md)<br>
[SDK](docs/sdk.md)<br>
[Troubleshooting](docs/troubleshooting.md)<br>
[Developers](docs/developers.md)<br>
[Runbooks](docs/runbooks.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local development, tests, and pull request
guidelines.

## Safety

Analytics and crash reporting are opt-in from `/settings`. Source and Git installs do
not enable hosted diagnostics by default.

Model-generated terminal commands are not exposed as a default agent tool. Explicit
`!` terminal escapes and armory plugins should only be used in armories you trust.
