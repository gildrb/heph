# pyright: reportUnusedFunction=false
from __future__ import annotations

from hephaistos.terminal import current_palette


def _tui_css() -> str:
    """Generate TUI CSS from the current theme palette.

    Transparent themes (forge) use ``background: transparent`` so the
    terminal shows through.  Opaque themes set an explicit background
    colour on every surface so no transparency leaks.
    """
    p = current_palette()
    bg = "transparent" if p.is_transparent else p.background
    bt = "transparent"
    return f"""
App {{
    background: {bg};
    color: {p.text};
}}
Screen {{
    layout: vertical;
    background: {bg};
    color: {p.text};
    layers: base suggestions;
}}
#main-layout {{
    layer: base;
    layout: horizontal;
    height: 100%;
    width: 100%;
    background: {bg};
    color: {p.text};
}}
#shell {{
    layout: vertical;
    height: 100%;
    width: 1fr;
    background: {bg};
    color: {p.text};
}}
#status {{
    height: 1;
    width: auto;
    max-width: 100%;
    padding: 0 0;
    background: {bg};
    color: {p.dim};
}}
#transcript {{
    height: 1fr;
    padding: 0 0;
    background: {bg};
    color: {p.text};
    scrollbar-size: 0 0;
    background-tint: {bt};
}}
#transcript.hidden-for-armory {{
    display: none;
}}
#transcript:focus {{
    background: {bg};
    background-tint: {bt};
}}
#armory-inline {{
    height: 1fr;
    width: 100%;
    background: {bg};
    background-tint: {bt};
    color: {p.text};
    display: none;
}}
#armory-inline.active {{
    display: block;
}}
#armory-header {{
    height: 2;
    color: {p.dim};
    background: {bg};
    text-style: bold;
}}
#armory-columns-inline {{
    layout: horizontal;
    height: 1fr;
    width: 100%;
}}
#armory-parent-inline {{
    width: 26;
    height: 100%;
    border-right: solid {p.stone};
    padding: 0 1 0 0;
    background: {bg};
    color: {p.dim};
    scrollbar-size: 0 0;
}}
#armory-current-inline {{
    width: 1fr;
    height: 100%;
    padding: 0 1;
    background: {bg};
    color: {p.text};
    scrollbar-size: 0 0;
}}
#armory-current-inline > .option-list--option-highlighted {{
    background: {p.highlight};
    color: {p.text};
}}
#armory-preview-inline {{
    width: 40;
    height: 100%;
    padding: 0 1;
    border-left: solid {p.stone};
    background: {bg};
    color: {p.dim};
}}
#armory-error-inline {{
    height: 1;
    color: {p.error};
    background: {bg};
}}
#transcript RichLog {{
    color: {p.text};
}}
#transcript RichLog .md-code-inline {{
    color: {p.text};
    text-style: bold;
}}
#thinking-indicator {{
    height: 1;
    width: auto;
    max-width: 100%;
    padding: 0 0;
    background: {bg};
    color: {p.dim};
    display: none;
}}
#thinking-indicator.active {{
    display: block;
}}
#composer-frame {{
    height: auto;
    width: auto;
    max-width: 100%;
    margin-top: 1;
    padding: 0 0;
    background: {bg};
    color: {p.text};
}}
#suggestions {{
    dock: bottom;
    margin-bottom: 3;
    height: auto;
    max-height: 7;
    min-width: 30;
    width: 85%;
    max-width: 85%;
    padding-right: 1;
    background: {bg};
    color: {p.text};
    scrollbar-color: {p.highlight};
    scrollbar-color-hover: {p.stone};
    scrollbar-color-active: {p.stone};
    scrollbar-background: {p.panel};
    scrollbar-background-hover: {p.panel};
    scrollbar-background-active: {p.panel};
    scrollbar-corner-color: {bg};
    scrollbar-size-vertical: 1;
    layer: suggestions;
    display: none;
}}
#suggestions.visible {{
    display: block;
}}
#suggestions.model-picker {{
    max-height: 20;
}}
.hidden {{
    visibility: hidden;
}}
OptionList {{
    width: 100%;
    background: {bg};
    color: {p.text};
    border: none;
    padding: 0;
}}
OptionList > .option-list--option {{
    background: {bg};
    color: {p.text};
    padding: 0 0;
}}
OptionList > .option-list--option-highlighted {{
    background: {p.highlight};
    color: {p.text};
    padding: 0 0;
}}
OptionList:focus > .option-list--option-highlighted {{
    background: {p.highlight};
    color: {p.text};
    padding: 0 0;
}}
#composer {{
    height: 1;
    min-height: 1;
    max-height: 1;
    width: auto;
    max-width: 100%;
    padding: 0 0;
    background: {bg};
    color: {p.text};
}}
#footer-hints {{
    height: 1;
    width: auto;
    max-width: 100%;
    margin-top: 1;
    background: {bg};
    color: {p.dim};
}}
#info-separator {{
    width: 1;
    height: 100%;
    background: {bg};
    color: {p.stone};
}}
#info-panel {{
    width: 30;
    min-width: 30;
    max-width: 30;
    height: 100%;
    padding: 0 1;
    background: {bg};
    color: {p.dim};
}}
Input {{
    height: 1;
    min-height: 1;
    max-height: 1;
    border: none;
    padding: 0 0;
    background: {bg};
    background-tint: {bt};
    color: {p.text};
}}
Input > .input--placeholder,
Input > .input--suggestion {{
    color: {p.dim};
}}
Input:focus {{
    border: none;
    background: {bg};
    background-tint: {bt};
}}
Input > .input--cursor {{
    background: {p.text};
    color: {p.panel};
}}
Input > .input--selection {{
    background: {p.stone};
}}
"""
