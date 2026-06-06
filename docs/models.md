# Models

Hephaion works with multiple model providers, giving you flexibility in cost,
performance, privacy, and availability without binding an armory to one vendor.

## Supported Providers

### Pollinations AI

- **Cost**: Free
- **Account**: No account required
- **Models**: Various open models
- **Best for**: Testing, casual use, no-budget scenarios

### OpenRouter

- **Cost**: Pay-per-use
- **Account**: API key required
- **Models**: Many hosted models from different labs
- **Best for**: Access to multiple models through one API

### OpenAI

- **Cost**: Pay-per-use or subscription
- **Account**: API key or Codex subscription
- **Models**: OpenAI API models available to your account
- **Best for**: Production use, reliable performance

### DeepSeek

- **Cost**: Pay-per-use
- **Account**: API key required
- **Models**: DeepSeek chat and reasoning models available to your account
- **Best for**: Reasoning models through DeepSeek's official API semantics

### Z.AI

- **Cost**: Pay-per-use
- **Account**: API key required
- **Models**: Various models
- **Best for**: Alternative to OpenAI/OpenRouter

### Custom Endpoints

- **Cost**: Varies
- **Account**: Depends on endpoint
- **Models**: Any OpenAI-compatible API
- **Best for**: Self-hosted models, enterprise deployments

## Choosing a Model

Use `/models` to inspect models Heph can actually reach from your configured
providers. Use `/recommend` for current model picks from the local provider
catalog instead of relying on hardcoded docs.

General tradeoffs:

- Higher-quality reasoning models are better for sensitive document answers,
  synthesis, and citation-heavy work.
- Faster or cheaper models are useful for exploration, setup checks, and
  low-risk questions.
- Local or self-hosted OpenAI-compatible models can use the same armory harness
  when they are strong enough for your task.

## Model Configuration

### Set Default Model

Via environment variable:

```bash
export HEPHAION_MODEL="provider-model-name"
```

Or via `/settings` in the TUI.

### Switch Models Mid-Session

Use `/models` to see available models and switch during a session. It refreshes
live provider catalogs where supported, so new models can appear without a code
release.

## Model-Specific Considerations

### Provider Adapters

Hephaion keeps the document harness provider-swappable, but it does not send
every model the same generic payload. Provider request profiles translate Heph's
reasoning level into each API's native controls:

- **OpenAI API** uses `reasoning_effort`.
- **DeepSeek API** enables `thinking`, maps reasoning to DeepSeek's `high`/`max`
  effort values, and omits temperature while thinking is active.
- **OpenRouter** uses its nested `reasoning` payload for models that support it.
- **Custom endpoints** receive only provider-neutral fields unless they match a
  known official API profile.

Native Gemini APIs require their own runtime transports, so they are not exposed
as direct providers until those adapters exist.

### Context Window

Different models have different context windows, output limits, reasoning
controls, and pricing. Heph uses retrieval so the full armory does not need to
fit into one prompt, but larger context windows can still help when an answer
needs more evidence at once.

### Cost Optimization

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

### Slow Responses

1. Check your internet connection
2. Try a different model or provider
3. Consider using a model with larger context window

### Poor Quality Answers

1. Switch to a higher-quality model
2. Check that your documents are properly indexed (`heph health`)
3. Refresh the index with `heph index`
4. Use `/evidence` to see what context was retrieved

## Future Models

Hephaion is designed to be model-agnostic. As new models are released, provider
catalogs and configuration can change without changing your armories or
documents.

The architecture separates retrieval, citation checking, and model inference, so improvements in one area don't require changes in others.
