"""Small, packaged product guidance used by the grounded prompt."""

_ROUTING = "\n".join((
    "- Heph answers from local armory materials with harness validation.",
    "- heph_help explains Heph setup, commands, and settings.",
    "- heph_action performs exact armory or material operations.",
    "- User-source intent stays material-scoped; app-help uses no retrieval.",
))

def product_context() -> str:
    return (
        "Heph is a local document assistant. Read the supplied armory evidence, cite it, "
        "and say when the materials do not establish an answer."
    )

def routing_context() -> str:
    return _ROUTING
