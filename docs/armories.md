# Armories

An armory is the core workspace in Heph. It is a normal directory with source
files, chat history, retrieval index, traces, usage snapshots, and local memory.

## Armory Structure

```
~/.armories/my-armory/
├── materials/           # Your source documents
│   ├── document1.pdf
│   ├── notes.md
│   └── chapter1.txt
├── .harness/          # Heph state
│   ├── armory.toml     # Armory marker and metadata
│   ├── rag_index.json  # Retrieval index
│   ├── memory.json     # Learning memory
│   ├── chats/          # Chat history
│   ├── traces/         # JSONL traces when enabled
│   ├── usage/          # Token and cost snapshots
│   └── ignore          # File ignore patterns
└── README.md           # Optional description
```

## Key Concepts

### Portability

Armories are just directories under `~/.armories`. To move Heph to another PC,
install Heph, copy or sync the `.armories` folder, set up provider credentials,
and run `heph`.

You can:
- Copy the whole `.armories` folder between machines
- Back it up with any file backup tool
- Put source documents in normal `materials/` folders you can open with other apps

### Isolation

Each armory is completely isolated:
- **Memory**: Learning memory is scoped to the armory
- **Index**: Retrieval index is armory-specific
- **Chats**: Chat history stays with the armory
- **Traces and usage**: diagnostics traces and usage snapshots are armory-local

This separation prevents cross-contamination between different projects or domains.

### Normal Files

Your documents are stored as regular files in `materials/`. You can:
- Access them directly with any PDF viewer, text editor, etc.
- Use them with other tools
- Copy them without any proprietary export format

## Creating Armories

Named armories live in `~/.armories`:

```bash
heph armory init my-project
# Creates: ~/.armories/my-project/
```

New armories can be opened immediately, even before `materials/` contains files.
Heph will keep the armory attached and show a no-materials state until you add
documents.

Heph discovers valid armory folders in `.armories` when it starts. Copied or
synced armories are available as long as their `.harness/armory.toml` marker and
`materials/` folder travel with them.

Armories created by older Heph releases with `.hephaion/` state are migrated to
`.harness/` on first open. If both state directories exist and `.harness/` is not
a valid armory state directory, Heph stops instead of guessing which state to use.

When Heph is open without an attached armory, entering the exact name of a
discovered armory opens it directly. Names and relative paths resolve inside
`~/.armories`; Heph will not open armories outside that directory from this flow.
When Heph is already attached to an armory, entering exactly `detach` leaves the
current armory and continues in plain chat.

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
- DOCX, PPTX, and XLSX
- Common code files

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

Create `.harness/ignore` to exclude files:

```
# Ignore patterns
*.tmp
draft-*
old/
*.bak
```

## Indexing

Heph indexes materials when needed. To refresh manually:

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

Memory is stored in `.harness/memory.json` and is completely local.

## Moving Armories

The normal portability path is the folder itself:

```bash
cp -r ~/.armories ~/backup/armories
```

On the other machine, place the folder at `~/.armories`, set up `/login` or your
provider environment variables, and run `heph`. Indexes are rebuildable, so a
copied armory can still work when generated index files are missing or stale.

If you intentionally share only source files, copy just one armory's
`materials/` folder:

```bash
cp -r ~/.armories/my-armory/materials ~/backup/documents/
```

## Best Practices

### One Armory per Project

Keep different projects in separate armories:
- `course-notes/` for course materials
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

- Back up or sync `~/.armories` when you want every armory to travel
- Back up `materials/` when you only need the source documents
- Indexes can be regenerated if needed
- Provider credentials stay machine-local and are not stored in `.armories`

## Rebuilding Indexes

Index files are rebuildable. If an armory was copied from another machine or the
index looks stale, refresh it with the normal indexing path:

```bash
heph index ~/.armories/my-armory
```

## Troubleshooting

### Index Out of Date

If Heph isn't finding recent documents:

```bash
heph index ~/.armories/my-armory
heph health ~/.armories/my-armory
```

### Poor Retrieval Quality

1. Check document quality (OCR errors, formatting issues)
2. Run `heph health ~/.armories/my-armory`
3. Refresh the index with `heph index ~/.armories/my-armory`
4. Use `/evidence` to see what's being retrieved

### Memory Not Working

1. Verify you're opening the expected armory
2. Verify `.harness/memory.json` exists
3. Try asking a few questions to build up memory
