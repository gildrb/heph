from __future__ import annotations

import re
from re import Pattern

OVERVIEW_SUBJECT_RE = r"(?:material|materials|document|documents|pdf|pdfs|file|files)"
OVERVIEW_REQUEST_RE: Pattern[str] = re.compile(
    r"\b(?:"
    rf"what (?:is|are) (?:the |this |these )?{OVERVIEW_SUBJECT_RE}(?: about)?|"
    rf"what (?:does|do) (?:the |this |these )?{OVERVIEW_SUBJECT_RE} cover|"
    rf"explain (?:the |this |all )?{OVERVIEW_SUBJECT_RE}"
    r"(?: simply| in simple terms| to me)?|"
    rf"teach (?:me )?(?:the |this |all )?{OVERVIEW_SUBJECT_RE}|"
    rf"walk (?:me )?through (?:the |this |all )?{OVERVIEW_SUBJECT_RE}|"
    rf"(?:read|scan) (?:through |over )?(?:the |this |all |every |enabled |indexed )*"
    rf"{OVERVIEW_SUBJECT_RE}|"
    rf"(?:look|go) through (?:the |this |all |every |enabled |indexed )*"
    rf"{OVERVIEW_SUBJECT_RE}|"
    r"summari[sz]e (?:the |this )?(?:material|document|pdf|file)|"
    r"overview of (?:the |this )?(?:material|document|pdf|file)|"
    rf"(?:give|provide|create|write) (?:me )?(?:a |an )?(?:concise |short |brief |grounded )*"
    rf"overview (?:of |for )(?:the |this |all |enabled |indexed )*{OVERVIEW_SUBJECT_RE}|"
    rf"(?:give|provide|create|write) .{{0,80}}\boverview\b.{{0,80}}\b{OVERVIEW_SUBJECT_RE}|"
    r"what is this about"
    r")\b",
    re.IGNORECASE,
)
