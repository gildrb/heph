from __future__ import annotations

import os
from pathlib import Path

from harness.agent.shell_tools import ARMORY_SHELL_TRUST_ENV

def format_trust_report(armory_path: Path | None = None) -> str:
    location = str(armory_path / ".harness") if armory_path else "<armory>/.harness"
    trusted = bool(armory_path and _trusted(armory_path))
    shell = "enabled" if trusted else "disabled"
    return "\n".join((
        "Heph trust contract",
        "",
        "Data and chat state stay in the armory; no hosted telemetry is collected.",
        f"State: {location}",
        f"Shell: {shell}",
        f"Enable shell explicitly with {ARMORY_SHELL_TRUST_ENV}=<armory>",
    ))

def _trusted(path: Path) -> bool:
    raw = os.environ.get(ARMORY_SHELL_TRUST_ENV, "")
    return any(Path(item).expanduser().resolve() == path.expanduser().resolve() for item in raw.split(os.pathsep) if item.strip())
