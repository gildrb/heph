from __future__ import annotations

from hephaistos.terminal import current_palette


def _tui_css() -> str:
    """Generate TUI CSS from the current theme palette.

    All backgrounds are transparent to support terminal emulator transparency.
    Text colors remain theme-specific for readability.
    """
    p = current_palette()
    bg = "transparent"
    bt = "transparent"
    user_bg = p.composer_bar
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
Screen .screen--selection {{
    background: {bg};
    text-style: reverse;
}}
Horizontal,
Vertical,
Static,
RichLog {{
    background: {bg};
    background-tint: {bt};
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
    min-width: 0;
    background: {bg};
    color: {p.text};
}}
#transcript-spacer {{
    height: 1;
    background: {bg};
    color: transparent;
}}
#transcript-spacer.hidden-for-armory {{
    display: none;
}}
#status {{
    height: 1;
    max-height: 1;
    width: auto;
    max-width: 100%;
    padding: 0 0;
    background: {bg};
    color: {p.dim};
}}
#transcript {{
    height: 1fr;
    min-height: 0;
    width: 100%;
    max-width: 100%;
    padding: 0 0;
    content-align: left bottom;
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
    height: 1;
    color: {p.emphasis};
    background: {bg};
    text-style: bold;
}}
#armory-breadcrumbs {{
    height: auto;
    max-height: 0;
    color: {p.dim};
    background: {bg};
}}
#armory-mode-hint {{
    height: 1;
    color: {p.dim};
    background: {bg};
}}
#armory-pane-hint {{
    height: auto;
    max-height: 0;
    color: {p.dim};
    background: {bg};
}}
#armory-count-hint {{
    height: auto;
    max-height: 0;
    color: {p.dim};
    background: {bg};
}}
#armory-columns-inline-labels {{
    layout: horizontal;
    height: 1;
    width: 100%;
}}
#armory-current-label {{
    width: 100%;
    padding: 0 1;
    color: {p.dim};
    background: {bg};
}}
#armory-preview-label {{
    display: none;
}}
#armory-columns-inline {{
    layout: horizontal;
    height: 1fr;
    width: 100%;
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
    background: {bg};
    color: {p.text};
}}
#armory-preview-inline {{
    display: none;
}}
#armory-error-inline {{
    height: 1;
    color: {p.error};
    background: {bg};
}}
#materials-inline {{
    height: 1fr;
    min-height: 0;
    width: 100%;
    background: {bg};
    background-tint: {bt};
    color: {p.text};
    display: none;
}}
#materials-inline.active {{
    display: block;
}}
#materials-top-gap,
#materials-bottom-gap {{
    height: 1;
    background: {bg};
    color: transparent;
}}
#materials-header {{
    height: 1;
    color: {p.dim};
    background: {bg};
}}
#materials-columns {{
    layout: horizontal;
    height: 1fr;
    min-height: 0;
    width: 100%;
    background: {bg};
    color: {p.text};
}}
#materials-list,
#materials-list-right {{
    height: 1fr;
    min-height: 0;
    width: 1fr;
    padding: 0 1;
    background: {bg};
    color: {p.text};
    scrollbar-size: 0 0;
}}
#materials-list-right {{
    display: none;
}}
#materials-columns.two-column > #materials-list-right {{
    display: block;
}}
#materials-list.material-enabled > .option-list--option-highlighted,
#materials-list.material-enabled:focus > .option-list--option-highlighted,
#materials-list-right.material-enabled > .option-list--option-highlighted,
#materials-list-right.material-enabled:focus > .option-list--option-highlighted {{
    background: {bg};
    color: {p.material_enabled};
    text-style: not bold;
}}
#materials-list.material-disabled > .option-list--option-highlighted,
#materials-list.material-disabled:focus > .option-list--option-highlighted,
#materials-list-right.material-disabled > .option-list--option-highlighted,
#materials-list-right.material-disabled:focus > .option-list--option-highlighted {{
    background: {bg};
    color: {p.material_disabled};
    text-style: not bold;
}}
#materials-footer {{
    height: 1;
    color: {p.dim};
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
    layout: horizontal;
    height: 3;
    min-height: 3;
    max-height: 3;
    width: 100%;
    max-width: 100%;
    margin-top: 1;
    padding: 1 0;
    background: {user_bg};
    color: {p.text};
}}
#composer-frame.compact {{
    height: 1;
    min-height: 1;
    max-height: 1;
    margin-top: 0;
    padding: 0 0;
}}
#composer-prompt {{
    height: 1;
    min-height: 1;
    max-height: 1;
    width: 2;
    min-width: 2;
    max-width: 2;
    padding: 0 0;
    background: {user_bg};
    color: {p.text};
}}
#completion-stack {{
    height: 9;
    min-height: 1;
    max-height: 9;
    width: 100%;
    max-width: 100%;
    background: {bg};
    color: {p.text};
}}
#completion-stack.compact {{
    height: 1;
    max-height: 1;
}}
#suggestions {{
    height: auto;
    max-height: 7;
    min-width: 30;
    width: 100%;
    max-width: 100%;
    padding-right: 0;
    background: {bg};
    color: {p.text};
    scrollbar-size: 0 0;
    display: none;
}}
#suggestions.visible {{
    display: block;
}}
#suggestions.model-picker {{
    max-height: 20;
}}
#suggestions > .option-list--option-highlighted,
#suggestions:focus > .option-list--option-highlighted {{
    background: {bg};
    color: {p.text};
    text-style: not bold;
}}
#suggestions.mouse-hovering > .option-list--option-highlighted,
#suggestions.mouse-hovering:focus > .option-list--option-highlighted,
#suggestions > .option-list--option-hover,
#suggestions:focus > .option-list--option-hover {{
    background: {user_bg};
    color: {p.text};
    text-style: not bold;
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
    padding: 0 2;
}}
OptionList > .option-list--option-highlighted {{
    background: {p.selection_background};
    color: {p.selection_text};
    text-style: not bold;
    padding: 0 2;
}}
OptionList:focus > .option-list--option-highlighted {{
    background: {p.selection_background};
    color: {p.selection_text};
    text-style: not bold;
    padding: 0 2;
}}
#composer {{
    height: 1;
    min-height: 1;
    max-height: 1;
    width: 100%;
    max-width: 100%;
    padding: 0 0;
    background: {user_bg};
    color: {p.text};
}}
#footer-hints {{
    height: 1;
    width: auto;
    max-width: 100%;
    background: {bg};
    color: {p.dim};
}}
#completion-position {{
    height: 1;
    width: auto;
    max-width: 100%;
    padding: 0 2;
    background: {bg};
    color: {p.dim};
    display: none;
}}
#completion-position.visible {{
    display: block;
}}
#info-panel {{
    width: 46;
    min-width: 46;
    max-width: 46;
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
    background: {user_bg};
    background-tint: {bt};
    color: {p.text};
}}
Input > .input--placeholder,
Input > .input--suggestion {{
    color: {p.chrome_label};
}}
Input:focus {{
    border: none;
    background: {user_bg};
    background-tint: {bt};
}}
Input > .input--cursor {{
    background: {p.text};
    color: {p.composer_bar};
}}
Input > .input--selection {{
    background: {bg};
    text-style: reverse;
}}
"""
