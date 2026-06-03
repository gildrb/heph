# Troubleshooting

Common issues and solutions when using Hephaion.

## Installation Issues

### Python Version Error

**Problem**: `Python 3.13 or higher required`

**Solution**:
```bash
# Check your Python version
python --version

# Install Python 3.13+ using pyenv
pyenv install 3.13
pyenv global 3.13

# Or use conda
conda install python=3.13
```

### UV Not Found

**Problem**: `uv: command not found`

**Solution**:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

### Permission Denied

**Problem**: Permission errors during install

**Solution**:
```bash
# Use user-level install
uv tool install heph@latest --user

# Or use a virtual environment
python -m venv .venv
source .venv/bin/activate
uv pip install heph
```

## Model Configuration Issues

### API Key Not Working

**Problem**: "Invalid API key" or authentication errors

**Solutions**:
1. Verify your API key is correct
2. Check the key hasn't expired or been revoked
3. Try re-authenticating with `/login`
4. Check environment variables are set correctly

```bash
# Check if environment variable is set
echo $OPENAI_API_KEY

# Test the key manually
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Model Not Available

**Problem**: Model doesn't show up in `/models`

**Solutions**:
1. Check your plan includes access to that model
2. Verify the model name is correct
3. Try `/login` to refresh available models
4. Check if the model is available in your region

### Rate Limit Errors

**Problem**: "Rate limit exceeded" or "Too many requests"

**Solutions**:
1. Wait a few minutes and try again
2. Upgrade your API plan if needed
3. Use a different provider
4. Reduce request frequency

## Document and Indexing Issues

### Documents Not Found

**Problem**: Heph says it can't find information in your documents

**Solutions**:
1. Check documents are in `materials/` directory
2. Re-index the armory: `heph index`
3. Check file formats are supported
4. Use `/evidence` to see what was retrieved
5. Try increasing `top_k` in settings

```bash
# Check index health
heph health ~/.armories/my-armory

# Rebuild index from scratch
rm ~/.armories/my-armory/.hephaion/index/*
heph index ~/.armories/my-armory
```

### Poor OCR Quality

**Problem**: PDFs with poor text extraction

**Solutions**:
1. Try higher quality PDFs if available
2. Use OCR software to improve text layer
3. Convert to text/Markdown manually
4. Reinstall or update Heph if built-in Docling extraction is unavailable

### Index Out of Date

**Problem**: New documents aren't being found

**Solution**:
```bash
heph index ~/.armories/my-armory
```

## Performance Issues

### Slow Responses

**Problem**: Heph takes a long time to respond

**Solutions**:
1. Check your internet connection
2. Try a faster model (GPT-3.5 instead of GPT-4)
3. Reduce `top_k` in retrieval settings
4. Use a model with larger context window
5. Check provider status for outages

### High Memory Usage

**Problem**: Heph using too much RAM

**Solutions**:
1. Reduce `top_k` to retrieve fewer chunks
2. Use a smaller model
3. Clear old chat history
4. Close other armories if you have multiple open

### Slow Indexing

**Problem**: `heph index` takes a long time

**Solutions**:
1. Use `--quick` flag for faster indexing
2. Exclude large files with `.hephaion/ignore`
3. Index in batches by organizing materials into subdirectories
4. Check disk I/O performance

## Chat and Memory Issues

### Memory Not Working

**Problem**: Heph doesn't remember previous conversations

**Solutions**:
1. Check memory is enabled in `/settings`
2. Verify `.hephaion/memory/` directory exists
3. Ask a few questions to build up memory
4. Check memory retention settings

### Chat History Lost

**Problem**: Previous chat sessions are missing

**Solutions**:
1. Check `.hephaion/chats/` directory exists
2. Verify you're opening the correct armory
3. Check if chats were accidentally deleted
4. Restore from backup if available

### Context Window Full

**Problem**: "Context window exceeded" error

**Solutions**:
1. Use a model with larger context window
2. Reduce conversation history
3. Ask more focused questions
4. Clear chat history and start fresh

## TUI Issues

### Display Problems

**Problem**: TUI rendering incorrectly

**Solutions**:
1. Check your terminal supports Unicode
2. Try a different terminal (iTerm2, VS Code terminal)
3. Increase terminal window size
4. Check terminal color settings

### Keyboard Shortcuts Not Working

**Problem**: Keyboard shortcuts don't respond

**Solutions**:
1. Check if your terminal is intercepting keys
2. Try different key combinations
3. Check accessibility settings
4. Use mouse if available

### TUI Crashes

**Problem**: TUI crashes with error

**Solutions**:
1. Check logs: `HEPHAION_LOG_LEVEL=DEBUG heph`
2. Try running with `--no-tui` flag if available
3. Check terminal compatibility
4. Report the issue with logs

## DevContainer Issues

### Build Fails

**Problem**: Dev container fails to build

**Solutions**:
1. Check Docker is running
2. Verify dev container configuration
3. Try rebuilding the container
4. Check for network issues

### Extensions Not Installing

**Problem**: VS Code extensions not available in container

**Solutions**:
1. Check `devcontainer.json` extension list
2. Manually install extensions in container
3. Check marketplace access from container
4. Rebuild container

## Network Issues

### Connection Refused

**Problem**: Can't connect to model provider

**Solutions**:
1. Check internet connection
2. Verify API endpoint is correct
3. Check firewall settings
4. Try different network
5. Check provider status page

### Proxy Issues

**Problem**: Can't connect through corporate proxy

**Solutions**:
```bash
# Set proxy environment variables
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="http://proxy.example.com:8080"

# Or configure in ~/.hephaion/config.json
```

### SSL Certificate Errors

**Problem**: SSL certificate verification fails

**Solutions**:
1. Check system time is correct
2. Update CA certificates
3. Check if corporate firewall is intercepting SSL
4. For development only: disable SSL verification (not recommended)

## Getting Help

If none of these solutions work:

1. **Check logs**: Enable debug logging
   ```bash
   HEPHAION_LOG_LEVEL=DEBUG heph
   ```

2. **Health check**: Run diagnostics
   ```bash
   heph health ~/.armories/my-armory
   ```

3. **Search issues**: Check https://github.com/gildrb/heph/issues

4. **Report the issue**: Create a new issue with:
   - Hephaion version: `heph --version`
   - Python version: `python --version`
   - OS: macOS/Linux/Windows version
   - Steps to reproduce
   - Error messages and logs
   - Expected vs actual behavior

5. **Email**: hi@gildrb.com for security or sensitive issues

## Debug Mode

Enable comprehensive debugging:

```bash
# Enable debug logging
HEPHAION_LOG_LEVEL=DEBUG heph

# Log to file
HEPHAION_LOG_FILE=heph.log heph

# JSON format logs
HEPHAION_LOG_FORMAT=json heph

# Profile performance
heph --profile
heph --profile-memory
```

Check generated logs and profiles in `.hephaion/` for detailed information.