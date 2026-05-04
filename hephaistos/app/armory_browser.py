"""Compatibility alias for :mod:`hephaistos.tui.armory_browser`."""

from __future__ import annotations

import sys

from hephaistos.tui import armory_browser as _armory_browser

sys.modules[__name__] = _armory_browser
