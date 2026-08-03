from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, ParamSpec, Protocol, TypeVar

from ai.providers.config import ProviderConfig
from ai.providers.model_choices import configured_model_choices
from harness.chat.model_selection import switch_model

from interfaces.tui.display_text import menu_label_value
from interfaces.tui.flow_state import InlineFlow
from interfaces.tui.model_flow import (
    _duplicate_model_names,
    _model_choice_from_label,
    _model_flow_option,
)

try:
    from textual.widgets import Input
except ImportError:
    Input = None  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from harness.chat.session import ChatSession

_P = ParamSpec("_P")
_WidgetT = TypeVar("_WidgetT")


class _ModelFlowHost(Protocol):
    session: ChatSession
    _inline_flow: InlineFlow

    def query_one(self, selector: str, expect_type: type[_WidgetT]) -> _WidgetT: ...

    def run_worker(self, work: Callable[[], object], *, thread: bool = False) -> object: ...

    def call_from_thread(
        self,
        callback: Callable[_P, object],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> object: ...

    def _append_notice(self, text: str) -> None: ...

    def _refresh_status(self) -> None: ...

    def _update_info_panel(self) -> None: ...

    def _filter_inline_menu_options(self, query: str) -> None: ...

    def _open_inline_menu(
        self,
        *,
        name: str,
        step: str,
        title: str,
        options: list[tuple[str, str]],
        prompts: dict[str, str] | None = None,
        selected_label: str | None = None,
    ) -> None: ...

    def _close_inline_flow(self, notice: str = "") -> None: ...

    def _model_flow_options(
        self,
        pc: ProviderConfig,
        choices: list[tuple[str, str, str, bool]],
    ) -> list[tuple[str, str]]: ...

    def _refresh_models_flow_worker(self) -> None: ...

    def _refresh_models_flow_options(
        self,
        choices: list[tuple[str, str, str, bool]],
    ) -> None: ...


class TuiModelFlowMixin:
    def _model_flow_options(
        self: _ModelFlowHost,
        pc: ProviderConfig,
        choices: list[tuple[str, str, str, bool]],
    ) -> list[tuple[str, str]]:
        active = pc.get_active()
        current_model = self.session.config.model
        duplicate_models = _duplicate_model_names(choices)
        active_slug = active.slug if active is not None else None
        return [
            _model_flow_option(
                model=model,
                display_name=display_name,
                is_free=is_free,
                is_duplicate=model in duplicate_models,
                is_current=active_slug == slug and model == current_model,
            )
            for slug, model, display_name, is_free in choices
        ]

    def _open_models_flow(self: _ModelFlowHost) -> None:
        pc = ProviderConfig.load()
        choices = configured_model_choices(pc)
        if not choices:
            self._append_notice("No models available. Use /login to connect a provider.")
            return
        self._open_inline_menu(
            name="models",
            step="menu",
            title=f"Models  {menu_label_value('model', self.session.config.model)}",
            options=self._model_flow_options(pc, choices),
        )
        self.run_worker(self._refresh_models_flow_worker, thread=True)

    def _refresh_models_flow_worker(self: _ModelFlowHost) -> None:
        try:
            pc = ProviderConfig.load()
            choices = configured_model_choices(pc, refresh_live=True)
        except Exception:
            return
        self.call_from_thread(self._refresh_models_flow_options, choices)

    def _refresh_models_flow_options(
        self: _ModelFlowHost,
        choices: list[tuple[str, str, str, bool]],
    ) -> None:
        if not self._inline_flow.active or self._inline_flow.name != "models":
            return
        pc = ProviderConfig.load()
        options = self._model_flow_options(pc, choices)
        if not options or options == self._inline_flow.all_options:
            return
        self._inline_flow.all_options = options
        composer = self.query_one("#composer", Input)
        self._filter_inline_menu_options(composer.value)

    def _perform_model_switch(self: _ModelFlowHost, model: str) -> None:
        pc = ProviderConfig.load()
        choices = configured_model_choices(pc)
        matching = _model_choice_from_label(model, choices)
        if matching is None:
            self._close_inline_flow("Model not found.")
            return
        slug, _model, _display_name, _is_free = matching
        if not switch_model(self.session, slug, _model):
            self._close_inline_flow("Model unavailable.")
            return
        self._close_inline_flow(f"model: {_model}")
        self._refresh_status()
        self._update_info_panel()
