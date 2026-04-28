# Hephaistos

Hephaistos is a local-first study agent that runs in your terminal. You create an armory (a folder on disk), drop your source files into it, and chat with an LLM that retrieves relevant chunks from those files before answering. Every answer is checked against the retrieved evidence, and what you study is remembered for future sessions.

The project is a single Python package (`hephaistos/`) with a Textual TUI as its primary interface and a fallback prompt-toolkit shell. It supports any OpenAI-compatible LLM endpoint and ships with zero-config defaults via Pollinations AI.

## Quick links

- [Architecture](architecture.md) — package layout, import boundaries, data flow diagrams
- [Getting started](getting-started.md) — install, build, test, run
- [Glossary](glossary.md) — terms used throughout the codebase

## What it does

1. **Armories** are portable study workspaces. Each armory is a directory containing source files, a RAG index, saved chats, and study memory.
2. **Retrieval** indexes `source/` and `library/` folders, retrieves relevant chunks per question, and passes them to the model as citable evidence.
3. **Citation verification** checks every answer against the evidence retrieved in that turn and warns when citations are missing or fabricated.
4. **Study memory** extracts learned concepts after substantive exchanges and injects them in future sessions for the same armory.
5. **Vocabulary drills** with spaced repetition help reinforce terms found in source material.

## Tech stack

- Python 3.13+, `from __future__ import annotations` everywhere
- [Textual](https://textual.textualize.io/) for the TUI, [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/) as fallback
- [OpenAI Python SDK](https://github.com/openai/openai-python) for LLM communication (works with any compatible endpoint)
- [Rich](https://rich.readthedocs.io/) for terminal formatting
- [keyring](https://github.com/jaraco/keyring/) for OS-level credential storage
- Optional: `sentence-transformers` and `scikit-learn` for embedding-based retrieval, `docling` for document conversion
