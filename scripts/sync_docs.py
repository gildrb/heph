"""Regenerate the small repository documentation contract."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTICE = "<!-- Managed by scripts/sync_docs.py. Do not edit directly. -->"

DOCS = {
    "index.md": f"""{NOTICE}

# Heph

Heph is a local document harness. It stores armories, indexes material, and answers with source citations.

## Quick start

```bash
heph init ./my-armory
heph tui ./my-armory
```

Put source files under `materials/`. Armory state stays under `.harness/`.

See [the CLI reference](cli-reference.md).
""",
    "cli-reference.md": f"""{NOTICE}

# CLI reference

- `heph tui [PATH]` - open the Textual interface.
- `heph init PATH` - create an armory.
- `heph index PATH` - index local material.
- `heph health PATH` - check armory state.
- `heph version` - print the installed version.

Slash commands and keyboard shortcuts are shown by `heph tui --help`.
""",
}

def main() -> None:
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    for name, content in DOCS.items():
        (docs / name).write_text(content, encoding="utf-8")

if __name__ == "__main__":
    main()
