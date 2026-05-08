from __future__ import annotations

import re
from re import Pattern

OVERVIEW_SUBJECT_RE = r"(?:material|materials|document|documents|pdf|pdfs|file|files)"
OVERVIEW_REQUEST_RE: Pattern[str] = re.compile(
    r"\b(?:"
    r"what is (?:the |this )?(?:material|document|pdf|file)(?: about)?|"
    r"what does (?:the |this )?(?:material|document|pdf|file) cover|"
    rf"explain (?:the |this |all )?{OVERVIEW_SUBJECT_RE}"
    r"(?: simply| in simple terms| to me)?|"
    rf"teach (?:me )?(?:the |this |all )?{OVERVIEW_SUBJECT_RE}|"
    rf"walk (?:me )?through (?:the |this |all )?{OVERVIEW_SUBJECT_RE}|"
    r"summari[sz]e (?:the |this )?(?:material|document|pdf|file)|"
    r"overview of (?:the |this )?(?:material|document|pdf|file)|"
    r"what is this about"
    r")\b",
    re.IGNORECASE,
)
