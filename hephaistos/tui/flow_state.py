from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InlineFlow:
    name: str = ""
    step: str = ""
    slug: str = ""
    endpoint: str = ""
    model: str = ""
    options: list[tuple[str, str]] = field(default_factory=list)
    all_options: list[tuple[str, str]] = field(default_factory=list)

    @property
    def active(self) -> bool:
        return bool(self.name)
