# Models

Heph works with multiple model providers without binding an armory to one
vendor.

The compute choice is part of the privacy boundary. Local llama.cpp keeps
prompts, retrieved chunks, and tool calls on your machine. Hosted providers
receive the active question, system instructions, and selected retrieved chunks
needed for the answer. Custom endpoints receive the same request shape at the
endpoint you configure.

## Supported Providers

### Pollinations AI

- **Cost**: Free
- **Account**: No account required
- **Models**: Various open models

### OpenRouter

- **Cost**: Pay-per-use
- **Account**: API key required
- **Models**: Many hosted models from different labs

### OpenAI

- **Cost**: Pay-per-use or subscription
- **Account**: API key or Codex subscription
- **Models**: OpenAI API models available to your account

### DeepSeek

- **Cost**: Pay-per-use
- **Account**: API key required
- **Models**: DeepSeek chat and reasoning models available to your account

### Z.AI

- **Cost**: Pay-per-use
- **Account**: API key required
- **Models**: Various models

### Local llama.cpp

- **Cost**: Free after you download the model and have the hardware to run it
- **Account**: No API key required
- **Models**: Curated GGUF releases capped at 16 GB recommended RAM,
  plus local `.gguf` files for advanced installs

Heph manages an official `llama-server` binary, downloads verified release
assets into `~/.cache/harness/llama.cpp/bin/`, stores model cache under
`~/.cache/harness/llama.cpp/models`, and binds the server to `127.0.0.1`.
The guided catalog favors publisher-owned releases with specific GGUF quant
files, including small LiquidAI LFM, Hugging Face SmolLM, Qwen, AllenAI OLMo,
IBM Granite, Mistral, Microsoft Phi, and Google Gemma options. `/local` shows
the download size and recommended RAM for each model and asks for confirmation
before any model is downloaded or started.

Local models are not automatically considered usable. After install, Heph runs a
deterministic tool-call probe using the OpenAI-compatible `tool_calls` protocol.
Only models that return a valid tool call with valid JSON arguments appear in
`/models`, where they are labeled `local, tool-capable`. Failed models can remain
downloaded and can be revalidated later.

### Custom Endpoints

- **Cost**: Varies
- **Account**: Depends on endpoint
- **Models**: Any OpenAI-compatible API

## Choosing a Model

Use `/models` to inspect models Heph can actually reach from your configured
providers. The list refreshes live provider catalogs where supported, so new
models can appear without a code release.

General tradeoffs:

- Higher-quality reasoning models are better for sensitive document answers,
  synthesis, and citation-heavy work.
- Faster or cheaper models are useful for exploration, setup checks, and
  low-risk questions.
- Local llama.cpp models keep prompts, retrieved chunks, and tool calls on your
  machine after the model has passed the tool-call probe.
- Custom endpoints let you own the compute boundary while keeping Heph's armory,
  retrieval, citation, and memory behavior unchanged.

## Model Configuration

### Set Default Model

Via environment variable:

```bash
export HARNESS_MODEL="provider-model-name"
```

Or via `/settings` in the TUI.

### Switch Models Mid-Session

Use `/models` to see available models and switch during a session. It refreshes
live provider catalogs where supported, so new models can appear without a code
release.

## Model-Specific Considerations

### Provider Adapters

The harness stays provider-swappable, but it does not send
every model the same generic payload. Provider request profiles translate Heph's
reasoning level into each API's native controls:

- **OpenAI API** uses `reasoning_effort`.
- **DeepSeek API** enables `thinking`, maps reasoning to DeepSeek's `high`/`max`
  effort values, and omits temperature while thinking is active.
- **OpenRouter** uses its nested `reasoning` payload for models that support it.
- **Local llama.cpp** receives provider-neutral OpenAI-compatible fields and no
  hosted fallback.
- **Custom endpoints** receive only provider-neutral fields unless they match a
  known official API profile.

Native Gemini APIs require their own runtime transports, so they are not exposed
as direct providers until those adapters exist.

The `thinking_visibility` setting controls only thinking text or summaries that a
provider explicitly sends. It does not reveal hidden model chain-of-thought when
the provider keeps that reasoning private.

### Context Window

Different models have different context windows, output limits, reasoning
controls, and pricing. Heph uses retrieval so the full armory does not need to
fit into one prompt, but larger context windows can still help when an answer
needs more evidence at once.

### Cost

1. **Use retrieval**: Heph retrieves only relevant chunks, reducing token usage
2. **Choose appropriate model**: use faster or cheaper models for simple queries
3. **Limit response length**: Set max tokens in settings
4. **Cache results**: Memory feature avoids re-processing

### Performance Tips

1. **Start with a faster model** for initial exploration
2. **Switch to higher-quality models** for important analyses
3. **Use `/evidence`** to check what was retrieved before expensive queries
4. **Batch similar questions** to make better use of context

## Rate Limits

Different providers have different rate limits:

- **OpenAI**: Varies by account, model, and tier
- **DeepSeek**: Depends on account tier and model
- **OpenRouter**: Depends on underlying model
- **Pollinations**: Generally lenient
- **Custom**: Depends on your endpoint

If you hit rate limits, Heph will automatically retry with exponential backoff.

## Troubleshooting

### Model Not Available

If a model isn't showing up in `/models`:

1. Check your API key is valid
2. Verify the model name is correct
3. Check if the model is available in your region
4. Try `/login` to re-authenticate
5. For local llama.cpp models, run `heph local status` and revalidate failed
   models with `heph local revalidate <model-id>`

### Slow Responses

1. Check your internet connection
2. Try a different model or provider
3. For local models, check CPU/GPU memory pressure and consider a smaller GGUF
   quantization
4. Consider using a model with larger context window

### Poor Quality Answers

1. Switch to a higher-quality model
2. Check that your documents are properly indexed (`heph health`)
3. Refresh the index with `heph index`
4. Use `/evidence` to see what context was retrieved

Provider catalogs and configuration can change without changing your armories or
source files.
