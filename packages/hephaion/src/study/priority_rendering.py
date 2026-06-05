from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from _types import is_string_mapping
from palette import LIGHT_THEME

from study.priority_analysis import PriorityAnalysis, priority_tier
from study.priority_types import (
    PriorityCheatSheet,
    PriorityCheatSheetTopic,
    PriorityExamQuestion,
    PrioritySource,
    PriorityTopic,
    PriorityVerificationReport,
    _CheatSheetTopicSections,
    _PriorityVerificationChecks,
)

_SENTENCE_RE = re.compile(r"[^.!?\n]+")
_WHITESPACE_RE = re.compile(r"\s+")
_LATEX_MATH_COMMAND_RE = re.compile(r"\\([A-Za-z]+|.)")
_LATEX_MATH_UNSAFE_CHAR_RE = re.compile(r"[%#&~]")
_LATEX_MATH_DELIMITERS = (("$", "$"), (r"\(", r"\)"), (r"\[", r"\]"))
_ALLOWED_LATEX_MATH_COMMAND_NAMES = """
alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa
lambda mu nu xi pi rho sigma tau upsilon phi varphi chi psi omega Gamma Delta
Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega cdot times div pm mp le leq ge
geq neq approx sim equiv propto to rightarrow leftarrow Rightarrow Leftarrow
leftrightarrow in notin subset subseteq supset supseteq cup cap emptyset
forall exists nabla partial infty sum prod int lim log ln exp sin cos tan min
max arg sqrt frac left right cdots ldots dots text
""".strip()
_ALLOWED_LATEX_MATH_COMMANDS = frozenset(_ALLOWED_LATEX_MATH_COMMAND_NAMES.split())
_ALLOWED_LATEX_MATH_SYMBOL_COMMANDS = frozenset({",", ";", ":", "!", " ", "_"})


def build_priority_cheat_sheet(
    analysis: PriorityAnalysis,
    *,
    model_payload: dict[str, object] | None,
    focus: str,
) -> PriorityCheatSheet:
    sources = _priority_sources(analysis)
    source_ids = {source.path: source.source_id for source in sources}
    topics = tuple(
        _cheat_sheet_topic(topic, analysis, source_ids, model_payload=model_payload)
        for topic in analysis.topics
    )
    uncertainties = _analysis_uncertainties(analysis, topics)
    return PriorityCheatSheet(
        title="Heph priority sheet",
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        focus=focus.strip(),
        sources=sources,
        topics=topics,
        exam_questions=analysis.exam_questions,
        uncertainties=uncertainties,
    )


def render_priority_latex(sheet: PriorityCheatSheet) -> str:
    body = [
        r"\documentclass[10pt,a4paper,landscape]{article}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{lmodern}",
        r"\usepackage{amsmath,amssymb,mathtools}",
        r"\usepackage{geometry}",
        r"\usepackage{multicol}",
        r"\usepackage{array,booktabs,tabularx}",
        r"\usepackage{enumitem}",
        r"\usepackage{microtype}",
        r"\usepackage{xcolor}",
        r"\geometry{margin=8mm}",
        r"\setlength{\parindent}{0pt}",
        r"\setlength{\parskip}{1.5pt}",
        r"\setlist[itemize]{leftmargin=*,topsep=1pt,itemsep=1pt,parsep=0pt}",
        r"\setlist[enumerate]{leftmargin=*,topsep=1pt,itemsep=1pt,parsep=0pt}",
        r"\definecolor{hephSourceText}{HTML}{"
        + LIGHT_THEME.text_muted.removeprefix("#").upper()
        + "}",
        r"\newcommand{\sourceids}[1]{\textcolor{hephSourceText}{\footnotesize #1}}",
        r"\newcommand{\topicrule}{\vspace{2pt}\hrule\vspace{3pt}}",
        r"\pagestyle{empty}",
        r"\begin{document}",
        _latex_header(sheet),
        r"\begin{multicols*}{2}",
    ]
    for topic in sheet.topics:
        body.extend(_latex_topic(topic))
    body.append(r"\end{multicols*}")
    body.extend(_latex_exam_patterns(sheet.exam_questions))
    body.extend(_latex_sources(sheet.sources))
    if sheet.uncertainties:
        body.extend((r"\section*{Uncertainty}", r"\begin{itemize}"))
        body.extend(r"\item " + _latex_text(item) for item in sheet.uncertainties)
        body.append(r"\end{itemize}")
    body.append(r"\end{document}")
    return "\n".join(body) + "\n"


def verify_priority_output(
    analysis: PriorityAnalysis,
    sheet: PriorityCheatSheet,
    tex_text: str,
    *,
    pdf_path: Path | None,
) -> PriorityVerificationReport:
    checks = _priority_verification_checks(analysis, sheet, tex_text, pdf_path=pdf_path)
    return PriorityVerificationReport(
        extraction_ok=checks.extraction_ok,
        priority_ok=checks.priority_ok,
        source_support_ok=checks.source_support_ok,
        latex_ok=checks.latex_ok,
        pdf_ok=checks.pdf_ok,
        anti_regression_ok=checks.anti_regression_ok,
        practice_ok=checks.practice_ok,
        issues=tuple(_priority_verification_issues(checks)),
        warnings=_priority_verification_warnings(analysis),
    )


def _priority_verification_checks(
    analysis: PriorityAnalysis,
    sheet: PriorityCheatSheet,
    tex_text: str,
    *,
    pdf_path: Path | None,
) -> _PriorityVerificationChecks:
    return _PriorityVerificationChecks(
        extraction_ok=bool(analysis.chunks),
        priority_ok=_verify_priority_order(analysis),
        source_support_ok=_verify_sheet_source_support(sheet),
        latex_ok=_verify_latex_text(tex_text),
        pdf_ok=_verify_pdf_artifact(pdf_path),
        anti_regression_ok=_verify_report_text_has_no_forbidden_patterns(tex_text),
        practice_ok=_verify_priority_prompt_context(analysis),
    )


def _verify_sheet_source_support(sheet: PriorityCheatSheet) -> bool:
    return all(topic.source_ids or topic.uncertainty for topic in sheet.topics)


def _verify_pdf_artifact(pdf_path: Path | None) -> bool:
    return pdf_path is not None and pdf_path.is_file() and pdf_path.stat().st_size > 0


def _verify_report_text_has_no_forbidden_patterns(tex_text: str) -> bool:
    return "HEPHAION PRIORITY" not in tex_text


def _verify_priority_prompt_context(analysis: PriorityAnalysis) -> bool:
    return bool(analysis.topics)


def _priority_verification_issues(checks: _PriorityVerificationChecks) -> Iterator[str]:
    issue_specs = (
        (checks.extraction_ok, "no indexed chunks were available"),
        (checks.priority_ok, "top priorities are not supported by past-exam signals"),
        (
            checks.source_support_ok,
            "one or more topic sections lack source IDs or uncertainty labels",
        ),
        (checks.latex_ok, "generated LaTeX failed syntax or anti-debug checks"),
        (checks.pdf_ok, "compiled PDF was not produced"),
        (
            checks.anti_regression_ok,
            "report text contains a forbidden raw metric or boilerplate pattern",
        ),
        (checks.practice_ok, "priority context is empty or exposes raw metric strings"),
    )
    yield from (message for passed, message in issue_specs if not passed)


def _priority_verification_warnings(analysis: PriorityAnalysis) -> tuple[str, ...]:
    if analysis.past_exam_sources:
        return ()
    return ("no past-exam sources were identified from content",)


def _priority_sources(analysis: PriorityAnalysis) -> tuple[PrioritySource, ...]:
    ordered = [*analysis.past_exam_sources, *analysis.material_sources]
    deduped = tuple(dict.fromkeys(ordered))
    sources: list[PrioritySource] = []
    for index, source in enumerate(deduped, start=1):
        role = "past exam" if source in analysis.past_exam_sources else "supporting material"
        sources.append(PrioritySource(source_id=f"S{index}", path=source, role=role))
    return tuple(sources)


def _cheat_sheet_topic(
    topic: PriorityTopic,
    analysis: PriorityAnalysis,
    source_ids: dict[str, str],
    *,
    model_payload: dict[str, object] | None,
) -> PriorityCheatSheetTopic:
    source_labels = tuple(source_ids[source] for source in topic.sources if source in source_ids)
    sections = _cheat_sheet_topic_sections(topic, analysis, model_payload=model_payload)
    return PriorityCheatSheetTopic(
        title=topic.topic,
        tier=priority_tier(topic),
        source_ids=source_labels,
        prerequisites=_topic_prerequisites(topic),
        definitions=tuple(sections.definitions[:3]),
        formulas=tuple(sections.formulas[:4]),
        procedures=tuple(sections.procedures[:3]),
        exam_tasks=tuple(sections.exam_tasks[:4]),
        pitfalls=tuple(sections.pitfalls[:3]),
        uncertainty=_topic_uncertainty(
            topic,
            definitions=sections.definitions,
            formulas=sections.formulas,
            procedures=sections.procedures,
        ),
    )


def _cheat_sheet_topic_sections(
    topic: PriorityTopic,
    analysis: PriorityAnalysis,
    *,
    model_payload: dict[str, object] | None,
) -> _CheatSheetTopicSections:
    payload = _topic_model_payload(topic, model_payload)
    evidence_sentences = _topic_sentences(topic)
    definitions = _payload_string_list(payload, "definitions") or evidence_sentences[:2]
    formulas = _payload_string_list(payload, "formulas") or _select_formula_lines(topic)
    procedures = _payload_string_list(payload, "procedures")
    exam_tasks = _exam_tasks_for_topic(topic, analysis.exam_questions)
    pitfalls = _payload_string_list(payload, "pitfalls")
    return _CheatSheetTopicSections(
        definitions=definitions,
        formulas=formulas,
        procedures=procedures,
        exam_tasks=exam_tasks,
        pitfalls=pitfalls,
    )


def _topic_model_payload(
    topic: PriorityTopic,
    model_payload: dict[str, object] | None,
) -> dict[str, object] | None:
    raw_topics = model_payload.get("topics") if model_payload is not None else None
    if not isinstance(raw_topics, list):
        return None
    topic_name = topic.topic.lower()
    for raw_topic in raw_topics:
        if matched_topic := _payload_topic_entry(raw_topic, topic_name):
            return matched_topic
    return None


def _payload_topic_entry(raw_topic: object, topic_name: str) -> dict[str, object] | None:
    if not is_string_mapping(raw_topic):
        return None
    raw_name = raw_topic.get("name")
    if isinstance(raw_name, str) and raw_name.strip().lower() == topic_name:
        return dict(raw_topic)
    return None


def _topic_uncertainty(
    topic: PriorityTopic,
    *,
    definitions: list[str],
    formulas: list[str],
    procedures: list[str],
) -> tuple[str, ...]:
    uncertainty: list[str] = []
    if not definitions and not formulas and not procedures:
        uncertainty.append(
            "Indexed materials do not expose enough factual content for this topic."
        )
    if topic.confidence < 0.45:
        uncertainty.append("Extraction confidence is limited; verify against the cited sources.")
    return tuple(uncertainty)


def _analysis_uncertainties(
    analysis: PriorityAnalysis,
    topics: tuple[PriorityCheatSheetTopic, ...],
) -> tuple[str, ...]:
    if not analysis.past_exam_sources:
        return ("No past exams were identified; ranking falls back to material coverage.",)
    return tuple(_analysis_uncertainty_items(analysis, topics))


def _analysis_uncertainty_items(
    analysis: PriorityAnalysis,
    topics: tuple[PriorityCheatSheetTopic, ...],
) -> Iterator[str]:
    if not analysis.exam_questions:
        yield "Past exams were found, but question extraction was incomplete."
    if any(topic.uncertainty for topic in topics):
        yield "Some topics lack enough local factual support for full cheat-sheet blocks."


def _topic_sentences(topic: PriorityTopic) -> list[str]:
    sentences: list[str] = []
    seen: set[str] = set()
    for evidence in topic.evidence:
        for sentence_match in _SENTENCE_RE.finditer(evidence.excerpt):
            sentence = _WHITESPACE_RE.sub(" ", sentence_match.group(0)).strip()
            if len(sentence) < 12 or sentence.lower() in seen:
                continue
            seen.add(sentence.lower())
            sentences.append(sentence)
    return sentences


def _select_formula_lines(topic: PriorityTopic) -> list[str]:
    lines: list[str] = []
    for evidence in topic.evidence:
        lines.extend(
            line
            for unit in re.split(r"(?<=[.!?])\s+|\n", evidence.excerpt)
            if (line := _formula_line(unit))
        )
    return lines


def _formula_line(text: str) -> str:
    line = _WHITESPACE_RE.sub(" ", text).strip()
    return line if line and _looks_like_formula_line(line) else ""


def _looks_like_formula_line(line: str) -> bool:
    return "$" in line or "\\" in line or re.search(r"[=∑∫√≤≥→]", line) is not None


def _exam_tasks_for_topic(
    topic: PriorityTopic,
    exam_questions: tuple[PriorityExamQuestion, ...],
) -> list[str]:
    tasks: list[str] = []
    for question in exam_questions:
        if topic.topic not in question.topics:
            continue
        marks = f" ({question.marks} visible points)" if question.marks else ""
        tasks.append(f"{question.prompt}{marks}")
    return tasks


def _topic_prerequisites(topic: PriorityTopic) -> tuple[str, ...]:
    if topic.prerequisites:
        return topic.prerequisites
    if topic.web_prerequisites:
        return tuple(
            f"{item.term} (external prerequisite hint; verify locally)"
            for item in topic.web_prerequisites
        )
    return ("No explicit local prerequisite found.",)


def _latex_header(sheet: PriorityCheatSheet) -> str:
    focus = f"Focus: {_latex_text(sheet.focus)}. " if sheet.focus else ""
    source_count = len(sheet.sources)
    return "\n".join(
        (
            r"{\Large\textbf{" + _latex_text(sheet.title) + r"}}\\[-1pt]",
            r"\footnotesize "
            + focus
            + f"Generated {_latex_text(sheet.generated_at)}. "
            + f"{source_count} source(s). "
            + r"Claims are grounded in local sources unless listed as uncertainty.\\",
            r"\vspace{2mm}",
        )
    )


def _latex_topic(topic: PriorityCheatSheetTopic) -> list[str]:
    source_text = ", ".join(f"[{source_id}]" for source_id in topic.source_ids)
    lines = [
        r"\topicrule",
        r"\textbf{"
        + _latex_text(topic.title)
        + r"} "
        + r"\sourceids{"
        + _latex_text(f"{topic.tier} {source_text}".strip())
        + r"}",
    ]
    lines.extend(_latex_item_block("Definitions", topic.definitions))
    lines.extend(_latex_item_block("Formulas", topic.formulas))
    lines.extend(_latex_item_block("Procedures", topic.procedures))
    lines.extend(_latex_item_block("Exam tasks", topic.exam_tasks))
    lines.extend(_latex_item_block("Pitfalls", topic.pitfalls))
    lines.extend(_latex_item_block("Before this", topic.prerequisites))
    lines.extend(_latex_item_block("Uncertainty", topic.uncertainty))
    return lines


def _latex_item_block(title: str, items: tuple[str, ...]) -> list[str]:
    if not items:
        return []
    lines = [r"\textit{" + _latex_text(title) + r"}"]
    lines.append(r"\begin{itemize}")
    lines.extend(r"\item " + _latex_mixed_text(item) for item in items)
    lines.append(r"\end{itemize}")
    return lines


def _latex_exam_patterns(exam_questions: tuple[PriorityExamQuestion, ...]) -> list[str]:
    if not exam_questions:
        return []
    lines = [
        r"\newpage",
        r"\section*{Past-exam pattern table}",
        r"\footnotesize",
        r"\begin{tabularx}{\linewidth}{p{0.24\linewidth}p{0.09\linewidth}p{0.2\linewidth}X}",
        r"\toprule",
        r"Source & Points & Topic & Tested skill \\",
        r"\midrule",
    ]
    for question in exam_questions[:60]:
        points = str(question.marks) if question.marks else "unknown"
        topics = ", ".join(question.topics[:3]) if question.topics else "unknown"
        lines.append(
            _latex_text(question.source)
            + " & "
            + _latex_text(points)
            + " & "
            + _latex_text(topics)
            + " & "
            + _latex_mixed_text(_truncate(question.prompt, 180))
            + r" \\"
        )
    lines.extend((r"\bottomrule", r"\end{tabularx}"))
    return lines


def _latex_sources(sources: tuple[PrioritySource, ...]) -> list[str]:
    if not sources:
        return []
    lines = [r"\section*{Source list}", r"\footnotesize", r"\begin{multicols}{2}"]
    source_lines = (
        r"\noindent ["
        + _latex_text(source.source_id)
        + "] "
        + _latex_text(source.path)
        + " -- "
        + _latex_text(source.role)
        + r"\\"
        for source in sources
    )
    lines.extend(source_lines)
    lines.append(r"\end{multicols}")
    return lines


def _latex_text(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)


def _latex_mixed_text(value: str) -> str:
    parts = re.split(r"(\$[^$\n]+\$|\\\([^)]*\\\)|\\\[[\s\S]*?\\\])", value)
    rendered: list[str] = []
    for part in parts:
        if not part:
            continue
        if _is_safe_latex_math(part):
            rendered.append(part)
        else:
            rendered.append(_latex_text(part))
    return "".join(rendered)


def _looks_like_latex_math(value: str) -> bool:
    return any(
        value.startswith(open_delimiter) and value.endswith(close_delimiter)
        for open_delimiter, close_delimiter in _LATEX_MATH_DELIMITERS
    )


def _is_safe_latex_math(value: str) -> bool:
    if not _looks_like_latex_math(value):
        return False
    content = _latex_math_content(value)
    if not content or _LATEX_MATH_UNSAFE_CHAR_RE.search(content):
        return False
    return all(
        _allowed_latex_math_command(match) for match in _LATEX_MATH_COMMAND_RE.finditer(content)
    )


def _allowed_latex_math_command(match: re.Match[str]) -> bool:
    command = match.group(1)
    if command.isalpha():
        return command in _ALLOWED_LATEX_MATH_COMMANDS
    return command in _ALLOWED_LATEX_MATH_SYMBOL_COMMANDS


def _latex_math_content(value: str) -> str:
    for open_delimiter, close_delimiter in _LATEX_MATH_DELIMITERS:
        if value.startswith(open_delimiter) and value.endswith(close_delimiter):
            return value[len(open_delimiter) : -len(close_delimiter)]
    return value


def _verify_priority_order(analysis: PriorityAnalysis) -> bool:
    if not analysis.topics:
        return False
    if not analysis.past_exam_sources:
        return True
    top = analysis.topics[0]
    return top.exam_hits > 0 or top.exam_marks > 0


def _verify_latex_text(tex_text: str) -> bool:
    if tex_text.count("{") != tex_text.count("}"):
        return False
    return r"\geometry{margin=8mm}" in tex_text and r"\begin{multicols*}{2}" in tex_text


def _truncate(value: str, max_chars: int) -> str:
    value = _WHITESPACE_RE.sub(" ", value).strip()
    if len(value) <= max_chars:
        return value
    return f"{value[: max_chars - 1]}…"


def _payload_string_list(payload: dict[str, object] | None, key: str) -> list[str]:
    value = _payload_list_value(payload, key)
    if not isinstance(value, list):
        return []
    return [item for item in (_payload_string_item(item) for item in value) if item]


def _payload_list_value(payload: dict[str, object] | None, key: str) -> object:
    return payload.get(key) if payload is not None else None


def _payload_string_item(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""
