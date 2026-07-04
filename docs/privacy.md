# Privacy and Data Handling

Heph keeps armory data on your machine unless you explicitly choose otherwise.
The short ownership contract is in [Trust and ownership](trust.md).

## Three Ownership Questions

### Who owns the data?

You own the data. Heph stores source materials and generated state as normal
local files in directories you control. There is no Heph-hosted document sync,
remote account store, or cloud workspace service.

The main data owner boundary is the armory:

- `materials/` contains the source files you add
- `.harness/` contains Heph's local state for that armory
- API keys stay machine-local in the OS keyring, environment variables, or the
  session-only fallback
- Model/provider choices are swappable and are not baked into the armory

### Where is the cache?

Heph uses explicit local cache and state paths:

- Armory state: `<armory>/.harness/`
- Named armories: `~/.armories/` by default, or `HARNESS_ARMORY_HOME`
- User settings: `~/.config/harness/`
- Managed llama.cpp binaries and logs: `~/.cache/harness/llama.cpp/`
- Managed GGUF model cache: `~/.cache/harness/llama.cpp/models/`
- CPU profiles: `~/.cache/harness/profiles/`

Run `heph trust` to print the current ownership contract and these paths. Run
`heph local status` to print the active local llama.cpp cache, model cache,
server, and installed-model state.

### Are the prompts secure?

Prompt security depends on the compute mode you choose:

- **Local llama.cpp**: prompts, retrieved chunks, and tool calls stay on your
  machine after the model and server binary have been downloaded.
- **Custom endpoint**: prompts go only to the endpoint you configured.
- **Hosted provider**: Heph sends the active question, system instructions, and
  selected retrieved chunks needed for the answer to that provider. It does not
  upload whole armories by default.

Diagnostics are separate from model prompts. Anonymous analytics and redacted
crash reports are opt-in and must not include document content or chat history.
Session traces are local armory files.

## Ownership Model

Heph is designed so users can own all three layers:

- **Mode**: local armory workflow by default, explicit provider and diagnostics
  choices, and optional local model execution.
- **Application layer**: open-source CLI, TUI, and SDK process that can be run,
  inspected, forked, or embedded without a Heph-hosted workspace.
- **Compute**: swappable provider layer. Use local llama.cpp, your own
  OpenAI-compatible endpoint, or a hosted provider you trust.

## Data Location

### Local Storage

All your data is stored locally in your armory:

```
~/.armories/my-armory/
├── materials/           # Your source documents (you control these)
├── .harness/
│   ├── armory.toml     # Armory marker and metadata
│   ├── rag_index.json  # Retrieval index (local only)
│   ├── memory.json     # Armory memory (local only)
│   ├── chats/          # Chat history (local only)
│   ├── traces/         # Session traces (local only)
│   └── usage/          # Token/cost snapshots (local only)
```

### No Cloud Sync by Default

- Documents are never uploaded to Heph servers
- Chat history stays on your machine
- Armory memory is local to each armory
- Retrieval indexes are built and stored locally
- Session traces and usage snapshots stay local to the armory
- Local llama.cpp model validation state stays in your user config, and managed
  llama.cpp binaries/models stay under `~/.cache/harness/llama.cpp/`

### Local Traces

Armory sessions can append JSONL trace files under `.harness/traces/`. These
files are local only and recognized secrets are redacted before writing, but
they can still include private user content such as:

- User message text
- Retrieval queries and retrieved chunk excerpts
- Session, material-operation, and tool metadata
- Timing and usage details

Treat trace files as private armory data when backing up, syncing, or sharing an
armory.

## What Goes to Model Providers

When you ask a question, the following is sent to your configured model provider:

1. **Your question**: The text you type
2. **Retrieved chunks**: Relevant passages from your documents
3. **System prompt**: Instructions for the agent

This is necessary for the model to process your request. Choose providers you trust.

### Provider Data Policies

Different providers have different data policies:

- **OpenAI API and business products**: OpenAI says API Platform data is not used
  to train models by default unless the account explicitly opts in
- **Pollinations AI**: Check their specific policy
- **Local llama.cpp**: Prompts, retrieved chunks, and tool calls stay on your
  machine after the model and server binary have been downloaded
- **Custom endpoints**: Depends on your endpoint

Check your provider's privacy policy for details.

## Opt-In Diagnostics

### Analytics

Anonymous usage analytics can be enabled in `/settings`:

- Feature usage patterns
- Performance metrics
- Error rates

**No document content or chat history is ever sent.**

### Crash Reporting

Anonymous crash reports can be enabled in `/settings`:

- Stack traces
- Error messages
- System information

**No personal data or document content is included.**

### Source and Git Installs

If you install Heph from source or via git:

- Diagnostics are **disabled by default**
- You must explicitly enable them in `/settings`
- Official release builds may have different defaults

## API Key Storage

### OS Keyring

API keys are stored in your OS keyring:

- **macOS**: Keychain Access
- **Linux**: Secret Service API (gnome-keyring, etc.)
- **Windows**: Credential Manager

This is more secure than storing keys in config files.

### Environment Variables

You can also use environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export OPENROUTER_API_KEY="sk-..."
```

Keys in environment variables are never written to disk by Heph.

### Session-Only Fallback

If the OS keyring is unavailable during `/login`, Heph keeps the API key in
process memory for the current run only. This fallback is not written to disk and
is cleared by `/logout` or process exit.

### Never in Config Files

Heph never writes API keys to:
- armory `.harness/` state
- Any other configuration files
- Git history

## Network Activity

### Outbound Connections

Heph makes network connections only to:

1. **Model providers** (OpenAI, OpenRouter, etc.) - for inference
2. **Hugging Face and llama.cpp release downloads** - only when you use
   `heph local` or `/local` to browse curated local models, install
   them, or update local GGUF model support
3. **Package managers** (uv, pip) - for updates/dependencies
4. **Web pages requested through the `web_fetch` tool** - only when a model tool
   call asks Heph to fetch a URL because armory material is insufficient
5. **DuckDuckGo HTML search** - only when priority-report prerequisite hints are
   explicitly enabled with `HARNESS_PRIORITY_WEB_PREREQS` or the
   `priority_web_prereqs` feature flag
6. **Optional diagnostics endpoints** - if you enable them

Optional local document extraction and priority-PDF generation can invoke local
system tools such as PDF/OCR utilities or LaTeX engines. These tools run on your
machine against local files; Heph does not add network calls for them.

### Localhost-Only Servers

Heph does not:
- Accept LAN or internet connections
- Bind managed local model servers beyond localhost

Heph may:

- Temporarily bind a localhost-only OAuth callback during `/login`
- Run managed `llama-server` on `127.0.0.1` while a local model is active

It does not act as a public server.

During `/login`, Heph may temporarily bind a localhost-only OAuth callback
on `127.0.0.1:1455`. The callback validates the OAuth state parameter and is
closed after login or timeout.

### Proxy Support

If you need to use a proxy:

```bash
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="http://proxy.example.com:8080"
```

## Security Best Practices

### For Your Documents

1. **Encrypt sensitive armories**: Use filesystem encryption (BitLocker, FileVault, LUKS)
2. **Backup regularly**: Your documents in `materials/` are the master copy
3. **Access control**: Use OS permissions to restrict armory access
4. **Audit sharing**: Be careful when sharing armories via git

### For Model Providers

1. **Choose reputable providers**: review each provider before sending private material.
2. **Review privacy policies**: Understand how your data is handled
3. **Use API keys responsibly**: Don't share keys, rotate them periodically
4. **Consider local models**: Use tool-capable local llama.cpp models for
   maximum prompt privacy when your hardware can run them well

### For Development

If you're developing with Heph:

1. **Never commit secrets**: Use `.env.example` as template
2. **Use .gitignore**: Exclude `.harness/`, `.env`, API keys
3. **Audit dependencies**: Keep dependencies updated
4. **Security linting**: Run `bandit` on your code

## Compliance

### GDPR Considerations

- Your data stays on your machine (data residency)
- You control your documents (data portability)
- You can delete armories at any time (right to erasure)
- No personal data is sent without your consent

### HIPAA Considerations

Heph is not HIPAA-compliant out of the box. For healthcare use:

1. **Encrypt armories** at rest
2. **Choose HIPAA-compliant** model providers
3. **Disable diagnostics** completely
4. **Consult legal counsel** for your specific use case

### Enterprise Considerations

For enterprise deployment:

1. **Review provider contracts** for data handling
2. **Consider air-gapped setups** with local models
3. **Implement armory encryption** policies
4. **Audit network connections** to approved providers only

## Transparency

### Open Source

Heph is open source. You can:

- Review the code at https://github.com/gildrb/heph
- Audit how data is handled
- Build from source yourself
- Modify for your needs

### Observable Behavior

You can monitor what Heph does:

1. **Check logs**: Set `HARNESS_LOG_LEVEL=DEBUG`
2. **Monitor network**: Use firewall tools to see connections
3. **Inspect files**: All data is in plain text/JSON formats
4. **Use `/evidence`**: See exactly what was retrieved for each answer

## Data Deletion

### Delete an Armory

```bash
rm -rf ~/.armories/my-armory
```

This permanently deletes:
- Your documents in `materials/`
- All chat history
- Armory memory
- Retrieval index
- Session traces and usage snapshots

### Clear Specific Data

```bash
# Clear chat history only
rm ~/.armories/my-armory/.harness/chats/*

# Clear memory only
rm ~/.armories/my-armory/.harness/memory.json

# Clear index (will be rebuilt on next use)
rm ~/.armories/my-armory/.harness/rag_index.json

# Clear local traces only
rm ~/.armories/my-armory/.harness/traces/*.jsonl
```

### Revoke API Access

To revoke Heph's access to your accounts:

1. **Revoke API keys** in your provider's dashboard
2. **Remove keys** from OS keyring
3. **Clear environment variables**

Have a privacy concern or suggestion? Please open an issue or email hi@gildrb.com
