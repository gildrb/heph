# Vulture whitelist — false positives that are required by framework interfaces.

# prompt_toolkit Completer protocol requires this parameter name exactly (reportIncompatibleMethodOverride).
complete_event  # unused variable (hephaistos/app/shell.py)

# prompt_toolkit Completer protocol — vulture sees the class but not the dynamic dispatch.
_.get_completions  # used by prompt_toolkit (hephaistos/app/shell.py)

# prompt_toolkit keybinding decorator — the decorated _ function is the callback.
_  # unused function (hephaistos/app/shell.py)

# BaseHTTPRequestHandler overrides — required by the HTTP server framework.
_.do_GET  # used by http.server (hephaistos/providers/oauth.py)
_.log_message  # used by http.server (hephaistos/providers/oauth.py)

# Test handler stubs — **kw accepts arbitrary keyword arguments per handler protocol.
kw  # unused variable (tests/test_oauth.py, tests/test_tool_registry.py)
