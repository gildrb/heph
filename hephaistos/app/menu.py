"""Compatibility alias for :mod:`hephaistos.terminal`."""

from __future__ import annotations

import sys

from hephaistos import terminal as _terminal

sys.modules[__name__] = _terminal
