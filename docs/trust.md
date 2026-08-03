# Trust and Ownership

Heph is local-first beta software. The trust contract is explicit so users can
inspect it, move it, or replace the compute layer.

## Who Owns the Data?

You do. Source materials and Heph state are normal local files in directories
you control. Heph has no hosted document sync, remote account store, or hosted
armory service.

- `materials/` contains the materials you add
- `.harness/` contains local state for retrieval, memory, chats, traces, usage,
  generated artifacts, and trusted local tools
- API keys stay machine-local in the OS keyring, environment variables, or the
  session-only fallback
- Provider/model choices are swappable and are not baked into the armory

## Where Is the Cache?

- Armory state: `<armory>/.harness/`
- Named armories: `~/.armories/` by default, or `HARNESS_ARMORY_HOME`
- User settings: `~/.config/harness/`
- Managed llama.cpp binaries and logs: `~/.cache/harness/llama.cpp/`
- Managed GGUF model cache: `~/.cache/harness/llama.cpp/models/`
- CPU profiles: `~/.cache/harness/profiles/`

Run `heph trust` for the current contract and `heph local status` for the active
local model cache and server state.

## Are the Prompts Secure?

Prompt security depends on the compute mode:

- **Local llama.cpp**: prompts, retrieved chunks, and tool calls stay on your
  machine after the model and server binary have been downloaded.
- **Custom endpoint**: prompts go only to the endpoint you configured.
- **Hosted provider**: Heph sends the active question, system instructions, and
  selected retrieved chunks needed for the answer to that provider. It does not
  upload whole armories by default.

No hosted diagnostics, analytics, or crash reports are sent. Session traces are local
armory files and are never uploaded.

## What Can Users Own?

- **Mode**: local armory workflow by default, explicit provider choices, and optional local model execution.
- **Application layer**: open-source CLI, TUI, and SDK process that can be run,
  inspected, forked, or embedded without a Heph-hosted armory service.
- **Compute**: swappable provider layer. Use local llama.cpp, your own
  OpenAI-compatible endpoint, or a hosted provider you trust.
