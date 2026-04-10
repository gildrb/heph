# Vulture whitelist for false-positive dead code detections

# prompt_toolkit Completer.get_completions protocol requires this parameter
_.complete_event

# signal.signal() handler protocol requires (signum, frame) parameters
_.signum
_.frame
