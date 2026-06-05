from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn

from heph_ai.providers.endpoints import is_keyless_endpoint
from heph_ai.runtime.config import ChatConfig
from heph_ai.runtime.conversation import Conversation
from heph_ai.runtime.engine import has_configured_access, stream_completion
from heph_ai.runtime.errors import EngineError, RetryConfig

from hephaion._types import parse_json_object_fragment
from hephaion.study.priority_analysis import PriorityAnalysis
from hephaion.study.priority_progress import (
    _emit_progress,
    _format_elapsed_since,
    _ProgressHeartbeat,
    _write_text_artifact,
)
from hephaion.study.priority_rendering import (
    _truncate,
    build_priority_cheat_sheet,
    render_priority_latex,
    verify_priority_output,
)
from hephaion.study.priority_types import (
    PriorityCheatSheet,
    PriorityChunk,
    PriorityPdfCompiler,
    PriorityPdfError,
    PriorityProgressReporter,
    PriorityReport,
    PriorityVerificationReport,
    _PriorityReportArtifacts,
)
from hephaion.study.priority_web import (
    duckduckgo_search,
)
from hephaion.study.priority_web import (
    with_web_prerequisites as _with_web_prerequisites,
)

_WEB_PREREQ_ENV = "HEPHAION_PRIORITY_WEB_PREREQS"
_MODEL_STREAM_PROGRESS_SECONDS = 8.0
_LATEX_ENGINE_NAMES = ("latexmk", "lualatex", "xelatex", "pdflatex", "tectonic")
_LATEX_COMPILE_TIMEOUT_SECONDS = 30
_WHITESPACE_RE = re.compile(r"\s+")
_duckduckgo_search = duckduckgo_search


_PRIORITY_SCHEMA = """
{
  "summary": "1-2 sentence source-grounded overview",
  "topics": [
    {
      "name": "exact topic name from the materials",
      "importance": "critical|high|medium|low",
      "why": "why this is important based only on supplied evidence",
      "learning_actions": ["concrete, measurable goal grounded in the material"],
      "prerequisites": ["required prerequisite found in evidence or marked as web-backed"]
    }
  ],
  "past_exams": [
    {
      "source": "materials/...",
      "focus": "what the exam asked about",
      "marks": "visible mark distribution or unknown"
    }
  ],
  "learning_plan": ["ordered next steps grounded in evidence"],
  "unknowns": ["important detail missing from indexed materials"]
}
""".strip()


_PRIORITY_SYSTEM_PROMPT = """
You are Heph priority analysis. Produce a priority report using only the supplied
indexed material excerpts for topics, exam claims, marks, and source evidence. Do not add outside
facts for those sections. Web-backed prerequisite hints may be used only when they are explicitly
listed in the local scan context; label them as web-backed if you mention them. If the material
does not specify a detail, write that it is unknown. Favor exact topic names from the evidence
over filename fragments. Make each learning action a concrete, checkable goal rather than a vague
instruction to review the topic.
Return JSON only, matching this schema:
""".strip()


def generate_priority_report(
    analysis: PriorityAnalysis,
    output_dir: Path,
    *,
    config: ChatConfig | None = None,
    focus: str = "",
    compiler: PriorityPdfCompiler | None = None,
    keep_tex: bool = False,
    progress: PriorityProgressReporter | None = None,
) -> PriorityReport:
    report_started_at = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=True)
    _emit_progress(
        progress,
        f"Ran priority.report --topics {len(analysis.topics)} --output {output_dir}.",
    )
    analysis = _analysis_with_optional_web_prerequisites(analysis, config, progress)
    artifacts = _build_priority_report_artifacts(analysis, config, focus, progress)
    path = output_dir / f"hephaion-priority-{datetime.now(UTC):%Y%m%d-%H%M%S}.pdf"
    sidecar_path = path.with_suffix(".json")
    compiler = compiler or ExternalLatexCompiler.discover()
    tex_path = _compile_priority_report_pdf(
        analysis,
        artifacts.sheet,
        artifacts.tex_text,
        path=path,
        sidecar_path=sidecar_path,
        compiler=compiler,
        keep_tex=keep_tex,
        progress=progress,
    )
    verification = _verify_priority_report_artifacts(
        analysis,
        artifacts,
        path=path,
        sidecar_path=sidecar_path,
        progress=progress,
    )
    _emit_progress(
        progress,
        f"Priority report verified in {_format_elapsed_since(report_started_at)}.",
    )
    return PriorityReport(
        path=path,
        used_model=artifacts.model_payload is not None,
        topic_count=len(analysis.topics),
        source_count=len(set(analysis.past_exam_sources) | set(analysis.material_sources)),
        tex_path=tex_path,
        sidecar_path=sidecar_path,
        verification=verification,
    )


def _analysis_with_optional_web_prerequisites(
    analysis: PriorityAnalysis,
    config: ChatConfig | None,
    progress: PriorityProgressReporter | None,
) -> PriorityAnalysis:
    if not _web_prerequisites_enabled(config):
        return analysis
    _emit_progress(progress, "Checking web-backed prerequisite hints for top topics...")
    return replace(
        analysis,
        topics=tuple(_with_web_prerequisites(list(analysis.topics), _duckduckgo_search)),
    )


def _web_prerequisites_enabled(config: ChatConfig | None) -> bool:
    env_enabled = os.environ.get(_WEB_PREREQ_ENV, "").lower() in {"1", "true", "yes", "on"}
    return env_enabled or (
        config is not None and config.is_feature_enabled("priority_web_prereqs")
    )


def _build_priority_report_artifacts(
    analysis: PriorityAnalysis,
    config: ChatConfig | None,
    focus: str,
    progress: PriorityProgressReporter | None,
) -> _PriorityReportArtifacts:
    _emit_progress(progress, "Building report sections from indexed evidence...")
    model_payload = _priority_report_model_payload(analysis, config, focus, progress)
    sheet_started_at = time.perf_counter()
    sheet = build_priority_cheat_sheet(analysis, model_payload=model_payload, focus=focus)
    _emit_progress(
        progress,
        f"Built priority sheet IR ({len(sheet.topics)} topics, {len(sheet.sources)} sources) "
        f"in {_format_elapsed_since(sheet_started_at)}.",
    )
    render_started_at = time.perf_counter()
    tex_text = render_priority_latex(sheet)
    _emit_progress(
        progress,
        f"Rendered LaTeX priority sheet ({len(tex_text.encode('utf-8'))} bytes) "
        f"in {_format_elapsed_since(render_started_at)}.",
    )
    return _PriorityReportArtifacts(sheet=sheet, tex_text=tex_text, model_payload=model_payload)


def _priority_report_model_payload(
    analysis: PriorityAnalysis,
    config: ChatConfig | None,
    focus: str,
    progress: PriorityProgressReporter | None,
) -> dict[str, object] | None:
    can_use_model = config is not None and _can_use_model(config)
    if can_use_model:
        model_name = config.model or "configured model"
        _emit_progress(progress, f"Requesting model synthesis from {model_name}...")
    model_payload = _model_priority_payload(
        analysis,
        config=config,
        focus=focus,
        progress=progress,
    )
    _emit_model_payload_progress(model_payload, can_use_model, progress)
    return model_payload


def _emit_model_payload_progress(
    model_payload: dict[str, object] | None,
    can_use_model: bool,
    progress: PriorityProgressReporter | None,
) -> None:
    if model_payload is not None:
        _emit_progress(progress, "Model synthesis complete; grounding to indexed evidence.")
    elif can_use_model:
        _emit_progress(progress, "Model synthesis unavailable; using deterministic local output.")
    else:
        _emit_progress(progress, "Using deterministic local output (no model configured).")


def _verify_priority_report_artifacts(
    analysis: PriorityAnalysis,
    artifacts: _PriorityReportArtifacts,
    *,
    path: Path,
    sidecar_path: Path,
    progress: PriorityProgressReporter | None,
) -> PriorityVerificationReport:
    _emit_progress(progress, f"Read compiled PDF {path} for verification.")
    verify_started_at = time.perf_counter()
    verification = verify_priority_output(
        analysis,
        artifacts.sheet,
        artifacts.tex_text,
        pdf_path=path,
    )
    _emit_progress(
        progress,
        f"Ran priority verification checks in {_format_elapsed_since(verify_started_at)}.",
    )
    _write_priority_sidecar(sidecar_path, verification, progress=progress)
    if not verification.passed:
        issue_text = "; ".join(verification.issues) or "verification failed"
        raise PriorityPdfError(f"Priority PDF verification failed: {issue_text}")
    return verification


def _write_priority_sidecar(
    path: Path,
    report: PriorityVerificationReport,
    *,
    progress: PriorityProgressReporter | None = None,
) -> None:
    _write_text_artifact(
        path,
        json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n",
        progress=progress,
        label="verification sidecar",
    )


def _save_priority_draft(
    analysis: PriorityAnalysis,
    sheet: PriorityCheatSheet,
    tex_text: str,
    *,
    path: Path,
    sidecar_path: Path,
    progress: PriorityProgressReporter | None,
) -> Path:
    tex_path = path.with_suffix(".tex")
    _write_text_artifact(tex_path, tex_text, progress=progress, label="LaTeX draft")
    verification = verify_priority_output(analysis, sheet, tex_text, pdf_path=None)
    _write_priority_sidecar(sidecar_path, verification, progress=progress)
    return tex_path


def _model_priority_payload(
    analysis: PriorityAnalysis,
    *,
    config: ChatConfig | None,
    focus: str,
    progress: PriorityProgressReporter | None = None,
) -> dict[str, object] | None:
    if config is None or not _can_use_model(config):
        return None
    model_name = config.model or "configured model"
    context_chunks = _representative_chunks(analysis)
    _emit_model_context_progress(context_chunks, progress)
    conversation = _priority_model_conversation(analysis, focus=focus, chunks=context_chunks)
    _emit_progress(
        progress,
        f"Ran model synthesis {model_name} with {len(context_chunks)} evidence excerpt(s).",
    )
    raw_payload = _read_model_priority_response(
        config,
        conversation,
        model_name,
        progress=progress,
    )
    if raw_payload is None:
        return None
    return _parse_model_priority_payload(raw_payload, progress)


def _parse_model_priority_payload(
    raw_payload: str,
    progress: PriorityProgressReporter | None,
) -> dict[str, object] | None:
    parsed = parse_json_object_fragment(raw_payload)
    if parsed is None:
        _emit_progress(
            progress,
            "Model response was not valid JSON; using deterministic fallback.",
        )
        return None
    _emit_progress(progress, "Parsed model JSON priority payload.")
    return parsed


def _emit_model_context_progress(
    context_chunks: Sequence[PriorityChunk],
    progress: PriorityProgressReporter | None,
) -> None:
    for index, chunk in enumerate(context_chunks, start=1):
        _emit_progress(
            progress,
            f"Read model context {index}/{len(context_chunks)}: "
            f"{_priority_chunk_progress_label(chunk)}.",
        )


def _priority_model_conversation(
    analysis: PriorityAnalysis,
    *,
    focus: str,
    chunks: Sequence[PriorityChunk],
) -> Conversation:
    conversation = Conversation()
    conversation.add("system", f"{_PRIORITY_SYSTEM_PROMPT}\n{_PRIORITY_SCHEMA}")
    conversation.add("user", _priority_model_context(analysis, focus=focus, chunks=chunks))
    return conversation


def _priority_chunk_progress_label(chunk: PriorityChunk) -> str:
    label = (
        f"@{_material_display_name(chunk.source)} chunk {chunk.index} "
        f"chars {chunk.char_start}-{chunk.char_end}"
    )
    if chunk.heading:
        label += f' heading "{_truncate(chunk.heading, 56)}"'
    return label


def _material_display_name(rel_path: str) -> str:
    return rel_path.removeprefix("materials/")


def _read_model_priority_response(
    config: ChatConfig,
    conversation: Conversation,
    model_name: str,
    *,
    progress: PriorityProgressReporter | None,
) -> str | None:
    parts: list[str] = []
    started_at = time.perf_counter()
    last_progress_at = started_at
    chunk_count = 0
    char_count = 0
    try:
        with _ProgressHeartbeat(progress, f"Waiting on {model_name} model stream") as heartbeat:
            for delta in stream_completion(
                config,
                conversation,
                retry=RetryConfig(max_retries=1),
            ):
                if not delta.content:
                    continue
                parts.append(delta.content)
                chunk_count += 1
                char_count += len(delta.content)
                last_progress_at = _emit_model_stream_progress(
                    heartbeat,
                    model_name,
                    started_at=started_at,
                    last_progress_at=last_progress_at,
                    chunk_count=chunk_count,
                    char_count=char_count,
                    progress=progress,
                )
    except EngineError:
        _emit_progress(
            progress,
            f"Model synthesis failed after {_format_elapsed_since(started_at)}; "
            "using deterministic local output.",
        )
        return None
    raw_payload = "".join(parts)
    _emit_progress(
        progress,
        f"Read complete model response from {model_name}: {len(raw_payload)} character(s) "
        f"across {chunk_count} delta(s) in {_format_elapsed_since(started_at)}.",
    )
    return raw_payload


def _emit_model_stream_progress(
    heartbeat: _ProgressHeartbeat,
    model_name: str,
    *,
    started_at: float,
    last_progress_at: float,
    chunk_count: int,
    char_count: int,
    progress: PriorityProgressReporter | None,
) -> float:
    now = time.perf_counter()
    if chunk_count == 1:
        heartbeat.stop()
        _emit_progress(
            progress,
            f"Read first model delta from {model_name} in {_format_elapsed_since(started_at)}.",
        )
        return now
    if now - last_progress_at < _MODEL_STREAM_PROGRESS_SECONDS:
        return last_progress_at
    _emit_progress(
        progress,
        f"Read {char_count} model character(s) from {model_name} "
        f"across {chunk_count} delta(s) in {_format_elapsed_since(started_at)}.",
    )
    return now


def _can_use_model(config: ChatConfig) -> bool:
    if not config.base_url or not config.model:
        return False
    return is_keyless_endpoint(config.base_url) or has_configured_access(config)


def _priority_model_context(
    analysis: PriorityAnalysis,
    *,
    focus: str,
    chunks: Iterable[PriorityChunk] | None = None,
) -> str:
    context_chunks = tuple(chunks) if chunks is not None else _representative_chunks(analysis)
    focus_line = f"User focus: {focus}\n" if focus else ""
    return "\n\n".join(
        (
            focus_line + analysis.render_for_prompt(limit=10),
            "Indexed excerpts to analyze:",
            "\n\n".join(_priority_model_evidence_lines(context_chunks)),
        )
    )


def _priority_model_evidence_lines(chunks: Iterable[PriorityChunk]) -> Iterator[str]:
    for idx, chunk in enumerate(chunks, start=1):
        yield "\n".join(
            (
                f"Evidence {idx}",
                f"Source: {chunk.source}",
                f"Heading: {chunk.heading or 'none'}",
                f"Text: {_compact_model_evidence_text(chunk.text)}",
            )
        )


def _compact_model_evidence_text(text: str) -> str:
    compact_text = _WHITESPACE_RE.sub(" ", text).strip()
    if len(compact_text) > 900:
        return f"{compact_text[:899]}…"
    return compact_text


def _representative_chunks(
    analysis: PriorityAnalysis,
    *,
    limit: int = 28,
) -> tuple[PriorityChunk, ...]:
    topic_names = {topic.topic.lower() for topic in analysis.topics}
    preferred_chunks = (
        chunk for chunk in analysis.chunks if _is_priority_model_context(chunk, topic_names)
    )
    return _first_unique_priority_chunks((*preferred_chunks, *analysis.chunks), limit=limit)


def _is_priority_model_context(chunk: PriorityChunk, topic_names: set[str]) -> bool:
    chunk_text = chunk.text.lower()
    return any(topic in chunk_text for topic in topic_names)


def _first_unique_priority_chunks(
    chunks: Iterable[PriorityChunk],
    *,
    limit: int,
) -> tuple[PriorityChunk, ...]:
    selected: list[PriorityChunk] = []
    seen: set[tuple[str, str]] = set()
    for chunk in chunks:
        key = (chunk.source, chunk.text[:120])
        if key in seen:
            continue
        selected.append(chunk)
        seen.add(key)
        if len(selected) >= limit:
            return tuple(selected)
    return tuple(selected)


class ExternalLatexCompiler:
    def __init__(self, executable: Path) -> None:
        self._executable = executable

    @classmethod
    def discover(cls) -> ExternalLatexCompiler | None:
        for name in _LATEX_ENGINE_NAMES:
            resolved = shutil.which(name)
            if resolved:
                return cls(Path(resolved))
        return None

    def compile(
        self,
        tex_path: Path,
        pdf_path: Path,
        *,
        progress: PriorityProgressReporter | None = None,
    ) -> None:
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        work_dir = tex_path.parent
        command, runs = self._compile_command(tex_path, work_dir)
        _emit_progress(progress, f"Ran {' '.join(command)} (cwd {work_dir}).")
        compile_started_at = time.perf_counter()
        for run_index in range(runs):
            run_started_at = time.perf_counter()
            try:
                subprocess.run(
                    command,
                    cwd=work_dir,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=_LATEX_COMPILE_TIMEOUT_SECONDS,
                )
            except subprocess.TimeoutExpired as exc:
                raise PriorityPdfError(
                    "LaTeX engine timed out while compiling the priority report."
                ) from exc
            _emit_progress(
                progress,
                f"Ran LaTeX pass {run_index + 1}/{runs} in "
                f"{_format_elapsed_since(run_started_at)}.",
            )
        built_pdf = work_dir / tex_path.with_suffix(".pdf").name
        if not built_pdf.is_file():
            raise PriorityPdfError(f"LaTeX engine did not produce {built_pdf}.")
        shutil.copy2(built_pdf, pdf_path)
        _emit_progress(
            progress,
            f"Wrote PDF {pdf_path} ({pdf_path.stat().st_size} bytes) "
            f"in {_format_elapsed_since(compile_started_at)}.",
        )

    def _compile_command(self, tex_path: Path, work_dir: Path) -> tuple[list[str], int]:
        engine = self._executable.name
        if engine == "latexmk":
            command = [
                str(self._executable),
                "-pdf",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-no-shell-escape",
                "-outdir=.",
                tex_path.name,
            ]
            return command, 1
        if engine == "tectonic":
            command = [
                str(self._executable),
                "--keep-logs",
                "--only-cached",
                "--outdir",
                str(work_dir),
                str(tex_path),
            ]
            return command, 1
        command = [
            str(self._executable),
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-no-shell-escape",
            f"-output-directory={work_dir}",
            str(tex_path),
        ]
        return command, 2


def _compile_priority_report_pdf(
    analysis: PriorityAnalysis,
    sheet: PriorityCheatSheet,
    tex_text: str,
    *,
    path: Path,
    sidecar_path: Path,
    compiler: PriorityPdfCompiler | None,
    keep_tex: bool,
    progress: PriorityProgressReporter | None,
) -> Path | None:
    if compiler is None:
        _raise_missing_priority_pdf_engine(
            analysis,
            sheet,
            tex_text,
            path=path,
            sidecar_path=sidecar_path,
            progress=progress,
        )

    with tempfile.TemporaryDirectory(prefix="heph-priority-") as temp_dir_name:
        temp_tex_path = Path(temp_dir_name) / path.with_suffix(".tex").name
        _write_text_artifact(temp_tex_path, tex_text, progress=progress, label="temporary LaTeX")
        try:
            _run_priority_pdf_compiler(compiler, temp_tex_path, path, progress=progress)
        except (OSError, subprocess.CalledProcessError, PriorityPdfError) as exc:
            _raise_priority_pdf_compile_failed(
                exc,
                analysis,
                sheet,
                tex_text,
                path=path,
                sidecar_path=sidecar_path,
                progress=progress,
            )

    if not keep_tex:
        return None
    return _save_priority_tex_source(path, tex_text, progress=progress)


def _raise_missing_priority_pdf_engine(
    analysis: PriorityAnalysis,
    sheet: PriorityCheatSheet,
    tex_text: str,
    *,
    path: Path,
    sidecar_path: Path,
    progress: PriorityProgressReporter | None,
) -> NoReturn:
    tex_path = _save_priority_draft(
        analysis,
        sheet,
        tex_text,
        path=path,
        sidecar_path=sidecar_path,
        progress=progress,
    )
    _emit_progress(progress, f"No LaTeX engine found; saved draft to {tex_path}.")
    raise PriorityPdfError(
        "No LaTeX PDF engine found. Install latexmk, lualatex, xelatex, pdflatex, "
        f"or tectonic; LaTeX draft saved to {tex_path}."
    )


def _run_priority_pdf_compiler(
    compiler: PriorityPdfCompiler,
    temp_tex_path: Path,
    path: Path,
    *,
    progress: PriorityProgressReporter | None,
) -> None:
    compile_started_at = time.perf_counter()
    if isinstance(compiler, ExternalLatexCompiler):
        compiler.compile(temp_tex_path, path, progress=progress)
    else:
        _emit_progress(
            progress,
            f"Ran {compiler.__class__.__name__}.compile({temp_tex_path}, {path}).",
        )
        compiler.compile(temp_tex_path, path)
    _emit_progress(
        progress,
        f"PDF compile finished in {_format_elapsed_since(compile_started_at)}.",
    )
    if path.is_file() and not isinstance(compiler, ExternalLatexCompiler):
        _emit_progress(progress, f"Wrote PDF {path} ({path.stat().st_size} bytes).")


def _raise_priority_pdf_compile_failed(
    exc: Exception,
    analysis: PriorityAnalysis,
    sheet: PriorityCheatSheet,
    tex_text: str,
    *,
    path: Path,
    sidecar_path: Path,
    progress: PriorityProgressReporter | None,
) -> NoReturn:
    tex_path = _save_priority_draft(
        analysis,
        sheet,
        tex_text,
        path=path,
        sidecar_path=sidecar_path,
        progress=progress,
    )
    raise PriorityPdfError(
        f"Priority PDF compile failed; LaTeX draft saved to {tex_path}."
    ) from exc


def _save_priority_tex_source(
    path: Path,
    tex_text: str,
    *,
    progress: PriorityProgressReporter | None,
) -> Path:
    tex_path = path.with_suffix(".tex")
    _write_text_artifact(tex_path, tex_text, progress=progress, label="LaTeX source")
    return tex_path
