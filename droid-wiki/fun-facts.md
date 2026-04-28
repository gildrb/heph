# Fun facts

## The longest file

At 1,765 lines, `hephaistos/app/commands.py` is the largest file in the codebase. It handles every slash command the CLI supports: `/help`, `/model`, `/provider`, `/save`, `/compact`, `/armory`, `/vocab`, `/study`, and more. The file is essentially a router plus all the handler logic, and it has grown organically as new commands were added. It's a candidate for a future refactor, but for now it's remarkably self-contained — every slash command in one place.

## Solo project with bot colleagues

Gil wrote ~182 of the ~203 commits. But the git log tells a story of collaboration with machines:

- **devin-ai-integration[bot]** contributed 4 commits — likely automated PRs for dependency updates or code generation tasks.
- **dependabot[bot]** contributed 1 commit — a routine dependency bump.
- **T3 Code** contributed 7 commits as an external contributor.

The bot commits are visible in the log, but the real AI assistance footprint is much larger. Many of Gil's commits were co-authored with AI tools that don't leave a git signature. The codebase is a solo project in the traditional sense — one human with final say on every line — but it was built alongside AI pair programming from the start.

## Naming origin

Hephaistos is the Greek god of blacksmiths, craftsmen, and artisans. The name was chosen deliberately: this is a tool that helps you craft knowledge from raw material. The metaphor extends into the codebase itself:

- **Armories** are study workspaces — places where you store and sharpen your knowledge.
- The **"forge"** theme preset continues the blacksmith metaphor.
- Even the RAG pipeline fits: raw ore (source files) goes in, gets refined (chunked, indexed), and comes out as something useful (cited study material).

## The zero-config journey

Getting to "just run it with no setup" was a multi-step process, and it happened fast:

1. **Initially**: You needed an OpenAI API key to do anything. Every new user hit a signup wall before their first chat.
2. **Apr 26, 2026 (morning)**: OpenRouter was added as a free routing layer — still needed a key, but the barrier was lower.
3. **Apr 26, 2026 (later that day)**: Pollinations AI was wired in as the default provider. No API key, no signup, no configuration. Just `uv run heph` and you're chatting.

The entire zero-config journey happened in a single day. Commit `68af2b8` is the one that flipped the default.

## Startup speed hack

In late April 2026, startup time was cut by roughly 3× by converting top-level imports to deferred imports. Heavy modules like Textual and prompt-toolkit are now loaded only when needed, meaning the CLI can parse arguments and print help without ever importing the full TUI framework. It's a simple trick — `import` inside functions instead of at module level — but it makes the difference between "feels instant" and "feels like a Python app."
