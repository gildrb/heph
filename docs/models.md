# Models

Hephaion works with multiple model providers, giving you flexibility in cost, performance, and features.

## Supported Providers

### Pollinations AI

- **Cost**: Free
- **Account**: No account required
- **Models**: Various open models
- **Best for**: Testing, casual use, no-budget scenarios

### OpenRouter

- **Cost**: Pay-per-use
- **Account**: API key required
- **Models**: GPT-4, Claude, Gemini, and many others
- **Best for**: Access to multiple models through one API

### OpenAI

- **Cost**: Pay-per-use or subscription
- **Account**: API key or Codex subscription
- **Models**: GPT-4, GPT-4 Turbo, GPT-3.5
- **Best for**: Production use, reliable performance

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

### For Best Accuracy

- **GPT-4** or **Claude Opus**: Highest quality, slower, more expensive
- Best for complex reasoning, academic work, important documents

### For Balanced Performance

- **GPT-4 Turbo** or **Claude Sonnet**: Good quality, faster, moderate cost
- Best for day-to-day use, most document analysis tasks

### For Speed and Cost

- **GPT-3.5** or smaller open models: Fast, inexpensive, lower quality
- Best for quick questions, large document sets, testing

## Model Configuration

### Set Default Model

Via environment variable:

```bash
export HEPHAION_MODEL="gpt-4-turbo"
```

Or via `/settings` in the TUI.

### Switch Models Mid-Session

Use `/models` to see available models and switch during a session. It refreshes
live provider catalogs where supported, so new models can appear without a code
release.

## Model-Specific Considerations

### Context Window

Different models have different context windows (maximum input size):

- GPT-4 Turbo: 128k tokens
- GPT-4: 8k-32k tokens (depending on variant)
- Claude Opus: 200k tokens
- GPT-3.5: 16k tokens

Larger context windows can handle more documents at once but may be slower.

### Cost Optimization

1. **Use retrieval**: Heph retrieves only relevant chunks, reducing token usage
2. **Choose appropriate model**: Don't use GPT-4 for simple queries
3. **Limit response length**: Set max tokens in settings
4. **Cache results**: Memory feature avoids re-processing

### Performance Tips

1. **Start with a faster model** for initial exploration
2. **Switch to higher-quality models** for important analyses
3. **Use `/evidence`** to check what was retrieved before expensive queries
4. **Batch similar questions** to make better use of context

## Rate Limits

Different providers have different rate limits:

- **OpenAI**: Varies by tier (3-5000 RPM)
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
2. Try a different model (some are faster than others)
3. Reduce `top_k` in retrieval settings
4. Consider using a model with larger context window

### Poor Quality Answers

1. Increase `top_k` to retrieve more context
2. Switch to a higher-quality model
3. Check that your documents are properly indexed (`heph health`)
4. Use `/evidence` to see what context was retrieved

## Future Models

Hephaion is designed to be model-agnostic. As new models are released:

1. Add them to provider registries
2. Update model configuration
3. No changes to your armories or documents needed

The architecture separates retrieval, citation checking, and model inference, so improvements in one area don't require changes in others.