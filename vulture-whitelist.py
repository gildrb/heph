# Vulture whitelist — false positives that are required by framework interfaces.

# BaseHTTPRequestHandler overrides — required by the HTTP server framework.
_.do_GET  # used by http.server (hephaistos/providers/oauth.py)
_.log_message  # used by http.server (hephaistos/providers/oauth.py)

# Test handler stubs — **kw accepts arbitrary keyword arguments per handler protocol.
kw  # unused variable (tests/test_oauth.py, tests/test_tool_registry.py)

# Used only in string-annotated cast() — vulture cannot detect string references.
Stream  # unused import (hephaistos/runtime/engine.py)
ChatCompletionChunk  # unused import (hephaistos/runtime/engine.py)
TextualApp  # unused import (tests/test_app_tui.py)
TextualOptionList  # unused import (tests/test_app_tui.py)

# sentence-transformers / sklearn Protocol signatures — vulture sees the keyword-only
# parameters as unused because they are never referenced inside the Protocol body, but
# they define the shape of the external callables we pass these kwargs to.
convert_to_numpy  # Protocol param (hephaistos/rag/optional_backends.py)
show_progress_bar  # Protocol param (hephaistos/rag/optional_backends.py)

# fake_iter callback params for iter_chat_events mock -- vulture sees them as unused
session  # unused variable (tests/test_coverage_boost.py)
user_input  # unused variable (tests/test_coverage_boost.py)
abort  # unused variable (tests/test_coverage_boost.py)
stop_words  # Protocol param (hephaistos/rag/optional_backends.py)
sublinear_tf  # Protocol param (hephaistos/rag/optional_backends.py)
max_features  # Protocol param (hephaistos/rag/optional_backends.py)
token_pattern  # Protocol param (hephaistos/rag/optional_backends.py)

# select_option() accepts keybindings for API compatibility but no longer uses it.
# NOTE: kept for backward-compatible call signature — callers may still pass it.
keybindings  # unused variable (hephaistos/terminal/__init__.py)
