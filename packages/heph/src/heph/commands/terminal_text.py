from __future__ import annotations


def terminal_safe_text(text: str) -> str:
    safe: list[str] = []
    for char in text:
        codepoint = ord(char)
        if char in {"\n", "\t"}:
            safe.append(char)
        elif codepoint < 32 or codepoint == 127 or 128 <= codepoint <= 159:
            safe.append(f"\\x{codepoint:02x}")
        else:
            safe.append(char)
    return "".join(safe)
