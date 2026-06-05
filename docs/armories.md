# Armories

An armory is the core organizational unit in Hephaion. It's a normal directory that contains your documents, chat history, retrieval index, and local memory.

## Armory Structure

```
~/.armories/my-armory/
├── materials/           # Your source documents
│   ├── document1.pdf
│   ├── notes.md
│   └── chapter1.txt
├── .hephaion/          # Hephaion configuration and state
│   ├── config.json     # Armory-specific settings
│   ├── index/          # Retrieval index
│   ├── memory/         # Learning memory
│   ├── chats/          # Chat history
│   ├── learning/       # Local harness attempt logs and policy artifacts
│   └── ignore          # File ignore patterns
└── README.md           # Optional description
```

## Key Concepts

### Portability

Armories are just directories. You can:
- Copy them between machines
- Share them via git (excluding `.hephaion/` via .gitignore)
- Back them up with any file backup tool
- Move them anywhere on your filesystem

### Isolation

Each armory is completely isolated:
- **Memory**: Learning memory is scoped to the armory
- **Index**: Retrieval index is armory-specific
- **Settings**: Model preferences and retrieval settings per armory
- **Chats**: Chat history stays with the armory

This separation prevents cross-contamination between different projects or domains.

### No Vendor Lock-in

Your documents are stored as regular files in `materials/`. You can:
- Access them directly with any PDF viewer, text editor, etc.
- Use them with other tools
- Export them without any proprietary format

## Creating Armories

### Default Location

```bash
heph armory init my-project
# Creates: ~/.armories/my-project/
```

### Custom Location

```bash
heph armory init ./docs/hephaion
# Creates: ./docs/hephaion/
```

### Anywhere

```bash
heph armory init ~/Documents/study/math
# Creates: ~/Documents/study/math/
```

## Managing Documents

### Adding Documents

Simply copy files into the `materials/` directory:

```bash
cp ~/Downloads/lecture.pdf ~/.armories/my-armory/materials/
cp ~/notes/summary.md ~/.armories/my-armory/materials/
```

### Supported Formats

- PDF
- Markdown (.md)
- Plain text (.txt)
- Code files (.py, .js, .ts, .java, etc.)
- Many other formats via Docling

### Organizing Materials

Use subdirectories to organize:

```
materials/
├── lectures/
│   ├── week1.pdf
│   └── week2.pdf
├── textbook/
│   ├── chapter1.pdf
│   └── chapter2.pdf
└── notes/
    └── summary.md
```

### Ignoring Files

Create `.hephaion/ignore` to exclude files:

```
# Ignore patterns
*.tmp
draft-*
old/
*.bak
```

## Indexing

Hephaion automatically indexes your materials. To manually refresh:

```bash
heph index ~/.armories/my-armory
```

Check index health:

```bash
heph health ~/.armories/my-armory
```

## Memory and Learning

Each armory maintains its own learning memory:

- **What you've asked**: Track questions you've explored
- **What you've learned**: Remember key concepts and explanations
- **Follow-up suggestions**: Proactively suggest related topics

Memory is stored in `.hephaion/memory/` and is completely local.

Harness attempt logs and policy artifacts are stored in `.hephaion/learning/`
and are also local to the armory.

## Sharing Armories

### Via Git

```bash
cd ~/.armories/my-armory
git init
git add materials/ .hephaion/ignore
git commit -m "Initial armory"
# Push to your preferred git host
```

Note: `.hephaion/index/`, `.hephaion/memory/`, `.hephaion/chats/`, and
`.hephaion/learning/` are gitignored by default.

### Manual Copy

```bash
# Copy entire armory
cp -r ~/.armories/my-armory ~/backup/armories/

# Copy just materials
cp -r ~/.armories/my-armory/materials ~/backup/documents/
```

## Best Practices

### One Armory per Project

Keep different projects in separate armories:
- `exams/` for exam preparation
- `research/` for research papers
- `documentation/` for product docs

### Descriptive Names

Use clear, descriptive names:
- `machine-learning-course` instead of `ml`
- `q3-financial-reports` instead of `reports`

### Regular Maintenance

- Remove outdated documents from `materials/`
- Re-index after major changes: `heph index`
- Check health periodically: `heph health`

### Backup Strategy

- Back up `materials/` regularly (these are your source documents)
- Optional: Back up `.hephaion/memory/` (learning memory)
- Index and chats can be regenerated if needed

## Advanced Usage

### Multiple Indexes

You can maintain multiple indexes for different purposes:

```bash
# Full index
heph index ~/.armories/my-armory

# Quick index (faster, less thorough)
heph index ~/.armories/my-armory --quick
```

### Custom Chunking

Configure chunking in `.hephaion/config.json`:

```json
{
  "retrieval": {
    "chunk_size": 1000,
    "chunk_overlap": 200
  }
}
```

Larger chunks = more context per retrieval
Smaller chunks = more precise retrieval

### Plugin System

Armories can have plugins for custom behavior (future feature):

```json
{
  "plugins": [
    "citation-enhancer",
    "summary-generator"
  ]
}
```

## Troubleshooting

### Index Out of Date

If Heph isn't finding recent documents:

```bash
heph index ~/.armories/my-armory
heph health ~/.armories/my-armory
```

### Poor Retrieval Quality

1. Increase `top_k` in settings
2. Adjust chunk size in config
3. Check document quality (OCR errors, formatting issues)
4. Use `/evidence` to see what's being retrieved

### Memory Not Working

1. Check memory is enabled in settings
2. Verify `.hephaion/memory/` directory exists
3. Try asking a few questions to build up memory
