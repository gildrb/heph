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

# Used only in string-annotated cast() — vulture cannot detect string references.
Stream  # unused import (hephaistos/chat/engine.py)
ChatCompletionChunk  # unused import (hephaistos/chat/engine.py)

# sentence-transformers / sklearn Protocol signatures — vulture sees the keyword-only
# parameters as unused because they are never referenced inside the Protocol body, but
# they define the shape of the external callables we pass these kwargs to.
convert_to_numpy  # Protocol param (hephaistos/harness/rag/chunker.py, retrieve.py)
show_progress_bar  # Protocol param (hephaistos/harness/rag/chunker.py, retrieve.py)
stop_words  # Protocol param (hephaistos/harness/rag/retrieve.py)
sublinear_tf  # Protocol param (hephaistos/harness/rag/retrieve.py)
max_features  # Protocol param (hephaistos/harness/rag/retrieve.py)
token_pattern  # Protocol param (hephaistos/harness/rag/retrieve.py)
