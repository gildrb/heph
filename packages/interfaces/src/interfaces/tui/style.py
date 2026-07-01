from __future__ import annotations

from interfaces.palette import TRANSPARENT
from interfaces.terminal import Theme, current_palette


def _tui_css(theme: Theme | None = None) -> str:
    p = theme or current_palette()
    app_bg = p.bg_app
    bg = p.bg_surface
    bt = TRANSPARENT
    user_bg = p.bg_raised
    return f"""
App {{
    background: {app_bg};
    color: {p.text_primary};
}}
Screen {{
    layout: vertical;
    background: {app_bg};
    color: {p.text_primary};
    layers: base suggestions;
}}
Screen .screen--selection {{
    background: {app_bg};
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
    background: {app_bg};
    color: {p.text_primary};
}}
#shell {{
    layout: vertical;
    height: 100%;
    width: 1fr;
    min-width: 0;
    background: {bg};
    color: {p.text_primary};
}}
#transcript-spacer {{
    height: 1;
    background: {bg};
    color: {p.bg_app};
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
    color: {p.text_muted};
}}
#transcript {{
    height: 1fr;
    min-height: 0;
    width: 100%;
    max-width: 100%;
    padding: 0 0;
    content-align: left bottom;
    background: {bg};
    color: {p.text_primary};
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
    padding: 1 0 0 0;
    background: {bg};
    background-tint: {bt};
    color: {p.text_primary};
    display: none;
}}
#armory-inline.active {{
    display: block;
}}
#armory-header {{
    height: 1;
    color: {p.text_muted};
    background: {bg};
}}
#armory-breadcrumbs {{
    height: auto;
    max-height: 0;
    color: {p.text_muted};
    background: {bg};
}}
#armory-flow-hint {{
    height: 0;
    color: {p.text_muted};
    background: {bg};
}}
#armory-pane-hint {{
    height: auto;
    max-height: 0;
    color: {p.text_muted};
    background: {bg};
}}
#armory-count-hint {{
    height: auto;
    max-height: 0;
    color: {p.text_muted};
    background: {bg};
}}
#armory-columns-inline-labels {{
    layout: horizontal;
    height: 0;
    width: 100%;
}}
#armory-current-label {{
    display: none;
    width: 0;
    max-width: 0;
    padding: 0;
    color: {p.text_muted};
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
    padding: 0 0;
    background: {bg};
    color: {p.text_primary};
    scrollbar-size: 0 0;
}}
#armory-current-inline > .option-list--option,
#materials-list > .option-list--option,
#materials-list-right > .option-list--option {{
    padding: 0 0;
}}
#armory-current-inline > .option-list--option-highlighted {{
    background: {bg};
    color: {p.brand_primary};
    text-style: not bold;
    padding: 0 0;
}}
#armory-preview-inline {{
    display: none;
}}
#armory-error-inline {{
    height: 1;
    color: {p.status_error_text};
    background: {bg};
}}
#materials-inline {{
    height: 1fr;
    min-height: 0;
    width: 100%;
    background: {bg};
    background-tint: {bt};
    color: {p.text_primary};
    display: none;
}}
#materials-inline.active {{
    display: block;
}}
#materials-top-gap,
#materials-bottom-gap {{
    height: 1;
    background: {bg};
    color: {p.bg_app};
}}
#materials-header {{
    height: 1;
    color: {p.text_muted};
    background: {bg};
}}
#materials-columns {{
    layout: horizontal;
    height: 1fr;
    min-height: 0;
    width: 100%;
    background: {bg};
    color: {p.text_primary};
}}
#materials-list,
#materials-list-right {{
    height: 1fr;
    min-height: 0;
    width: 1fr;
    padding: 0 0;
    background: {bg};
    color: {p.text_primary};
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
    color: {p.brand_primary};
    text-style: not bold;
    padding: 0 0;
}}
#materials-list.material-disabled > .option-list--option-highlighted,
#materials-list.material-disabled:focus > .option-list--option-highlighted,
#materials-list-right.material-disabled > .option-list--option-highlighted,
#materials-list-right.material-disabled:focus > .option-list--option-highlighted {{
    background: {bg};
    color: {p.brand_primary};
    text-style: not bold;
    padding: 0 0;
}}
#materials-footer {{
    height: 0;
    max-height: 0;
    color: {p.text_muted};
    background: {bg};
    display: none;
}}
#transcript RichLog {{
    color: {p.text_primary};
}}
#transcript RichLog .md-code-inline {{
    color: {p.text_primary};
    text-style: bold;
}}
#thinking-indicator {{
    height: 1;
    width: auto;
    max-width: 100%;
    padding: 0 0;
    background: {bg};
    color: {p.text_muted};
    display: none;
}}
#thinking-indicator.active {{
    display: block;
}}
#composer-frame {{
    layout: horizontal;
    height: auto;
    min-height: 3;
    max-height: 8;
    width: 100%;
    max-width: 100%;
    margin-top: 1;
    padding: 1 0;
    background: {user_bg};
    color: {p.text_primary};
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
    color: {p.text_primary};
}}
#completion-stack {{
    height: 9;
    min-height: 1;
    max-height: 9;
    width: 100%;
    max-width: 100%;
    background: {bg};
    color: {p.text_primary};
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
    color: {p.text_primary};
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
    color: {p.brand_primary};
    text-style: not bold;
}}
#suggestions.mouse-hovering > .option-list--option-highlighted,
#suggestions.mouse-hovering:focus > .option-list--option-highlighted,
#suggestions > .option-list--option-hover,
#suggestions:focus > .option-list--option-hover {{
    background: {bg};
    color: {p.brand_primary};
    text-style: not bold;
}}
.hidden {{
    visibility: hidden;
}}
OptionList {{
    width: 100%;
    background: {bg};
    color: {p.text_primary};
    border: none;
    padding: 0;
}}
OptionList > .option-list--option {{
    background: {bg};
    color: {p.text_primary};
    padding: 0 2;
}}
OptionList > .option-list--option-highlighted {{
    background: {p.action_primary_bg};
    color: {p.action_primary_text};
    text-style: not bold;
    padding: 0 2;
}}
OptionList:focus > .option-list--option-highlighted {{
    background: {p.action_primary_bg};
    color: {p.action_primary_text};
    text-style: not bold;
    padding: 0 2;
}}
#suggestions.completion-menu > .option-list--option,
#suggestions.completion-menu > .option-list--option-hover,
#suggestions.completion-menu > .option-list--option-highlighted,
#suggestions.completion-menu:focus > .option-list--option-highlighted,
#suggestions.completion-menu:focus > .option-list--option-hover,
#suggestions.inline-menu > .option-list--option,
#suggestions.inline-menu > .option-list--option-hover,
#suggestions.inline-menu > .option-list--option-highlighted,
#suggestions.inline-menu:focus > .option-list--option-highlighted,
#suggestions.inline-menu:focus > .option-list--option-hover {{
    padding: 0 0;
}}
#composer {{
    height: auto;
    min-height: 1;
    max-height: 6;
    width: 100%;
    max-width: 100%;
    padding: 0 0;
    background: {user_bg};
    color: {p.text_primary};
}}
#footer-hints {{
    height: 1;
    width: auto;
    max-width: 100%;
    background: {bg};
    color: {p.text_muted};
}}
#completion-position {{
    height: 1;
    width: auto;
    max-width: 100%;
    padding: 0 2;
    background: {bg};
    color: {p.text_muted};
    display: none;
}}
#completion-position.visible {{
    display: block;
}}
#info-panel-resizer {{
    width: 2;
    min-width: 2;
    max-width: 2;
    height: 100%;
    padding: 0 0;
    background: {bg};
    color: {p.text_muted};
}}
#info-panel {{
    width: 38;
    min-width: 24;
    max-width: 100%;
    height: 100%;
    padding: 0 0;
    content-align: left top;
    background: {bg};
    color: {p.text_muted};
}}
Input {{
    height: 1;
    min-height: 1;
    max-height: 1;
    border: none;
    padding: 0 0;
    background: {user_bg};
    background-tint: {bt};
    color: {p.text_primary};
}}
Input > .input--placeholder,
Input > .input--suggestion {{
    color: {p.text_secondary};
}}
Input:focus {{
    border: none;
    background: {user_bg};
    background-tint: {bt};
}}
Input > .input--cursor {{
    background: {p.text_primary};
    color: {p.bg_raised};
}}
Input > .input--selection {{
    background: {bg};
    text-style: reverse;
}}
"""
