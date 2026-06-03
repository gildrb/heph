# Privacy and Data Handling

Hephaion is designed with privacy as a core principle. Your documents and data stay on your machine unless you explicitly choose otherwise.

## Data Location

### Local Storage

All your data is stored locally in your armory:

```
~/.armories/my-armory/
├── materials/           # Your source documents (you control these)
├── .hephaion/
│   ├── armory.toml     # Armory marker and metadata
│   ├── rag_index.json  # Retrieval index (local only)
│   ├── memory.json     # Learning memory (local only)
│   ├── chats/          # Chat history (local only)
│   ├── traces/         # Session traces (local only)
│   └── usage/          # Token/cost snapshots (local only)
```

### No Cloud Sync by Default

- Documents are never uploaded to Hephaion servers
- Chat history stays on your machine
- Learning memory is local to each armory
- Retrieval indexes are built and stored locally
- Session traces and usage snapshots stay local to the armory

### Local Traces

Armory sessions can append JSONL trace files under `.hephaion/traces/`. These
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

When the configured provider is the official OpenAI API, Hephaion also runs OpenAI Guardrails
by default for quality and safety checks such as PII detection, jailbreak/off-topic detection,
and prompt-injection checks around tool use. Detected PII in user input is masked before the
normal model request when possible. Non-OpenAI providers, OpenAI-compatible proxies, and the
separate OpenAI Codex subscription backend continue to use Hephaion's local guardrails until
they have their own provider-native adapters.

### Provider Data Policies

Different providers have different data policies:

- **OpenAI**: May use data for improvement unless you opt out
- **Anthropic**: Generally does not use data for training
- **Pollinations AI**: Check their specific policy
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

If you install Hephaion from source or via git:

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

Keys in environment variables are never written to disk by Hephaion.

### Session-Only Fallback

If the OS keyring is unavailable during `/login`, Hephaion keeps the API key in
process memory for the current run only. This fallback is not written to disk and
is cleared by `/logout` or process exit.

### Never in Config Files

Hephaion never writes API keys to:
- `.hephaion/config.json`
- Any other configuration files
- Git history

## Network Activity

### Outbound Connections

Hephaion makes network connections only to:

1. **Model providers** (OpenAI, OpenRouter, etc.) - for inference
   and provider-native quality guardrails when available
2. **Package managers** (uv, pip) - for updates/dependencies
3. **Optional diagnostics endpoints** - if you enable them

Optional local document extraction and priority-PDF generation can invoke local
system tools such as PDF/OCR utilities or LaTeX engines. These tools run on your
machine against local files; Hephaion does not add network calls for them.

### No Persistent Inbound Server

Hephaion does not:
- Run a persistent listening service
- Accept LAN or internet connections
- Act as a server

During `/login`, Hephaion may temporarily bind a localhost-only OAuth callback
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

1. **Choose reputable providers**: OpenAI, Anthropic, etc.
2. **Review privacy policies**: Understand how your data is handled
3. **Use API keys responsibly**: Don't share keys, rotate them periodically
4. **Consider local models**: Use local LLMs for maximum privacy (future feature)

### For Development

If you're developing with Hephaion:

1. **Never commit secrets**: Use `.env.example` as template
2. **Use .gitignore**: Exclude `.hephaion/`, `.env`, API keys
3. **Audit dependencies**: Keep dependencies updated
4. **Security linting**: Run `bandit` on your code

## Compliance

### GDPR Considerations

- Your data stays on your machine (data residency)
- You control your documents (data portability)
- You can delete armories at any time (right to erasure)
- No personal data is sent without your consent

### HIPAA Considerations

Hephaion is not HIPAA-compliant out of the box. For healthcare use:

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

Hephaion is open source. You can:

- Review the code at https://github.com/gildrb/heph
- Audit how data is handled
- Build from source yourself
- Modify for your needs

### Observable Behavior

You can monitor what Hephaion does:

1. **Check logs**: Set `HEPHAION_LOG_LEVEL=DEBUG`
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
- Learning memory
- Retrieval index
- Session traces and usage snapshots

### Clear Specific Data

```bash
# Clear chat history only
rm ~/.armories/my-armory/.hephaion/chats/*

# Clear memory only
rm ~/.armories/my-armory/.hephaion/memory.json

# Clear index (will be rebuilt on next use)
rm ~/.armories/my-armory/.hephaion/rag_index.json

# Clear local traces only
rm ~/.armories/my-armory/.hephaion/traces/*.jsonl
```

### Revoke API Access

To revoke Hephaion's access to your accounts:

1. **Revoke API keys** in your provider's dashboard
2. **Remove keys** from OS keyring
3. **Clear environment variables**

## Future Privacy Features

Planned enhancements:

- **Local model support**: Use models running entirely on your machine
- **E2E encryption**: Encrypt data before sending to providers
- **Federated learning**: Improve models without sending raw data
- **Audit logs**: Detailed logs of all data access

Have a privacy concern or suggestion? Please open an issue or email hi@gildrb.com