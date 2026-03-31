"""WebSocket server for the OpenTUI frontend.

Run this to enable the rich TUI interface. Connects to the existing
chat engine and sessions while accepting connections from the TUI.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
import signal
from pathlib import Path
from typing import Any

import websockets
from websockets.server import WebSocketServerProtocol

from hephaistos.chat.engine import ChatConfig, EngineError, stream_reply
from hephaistos.chat.session import (
    ChatSession,
    _derive_title,
    create_session,
    list_armory_sessions,
    resume_session,
    save_session,
    session_has_messages,
    validate_armory_path,
)
from hephaistos.chat import storage as chat_storage
from hephaistos.armory.storage import (
    ArmoryError,
    discover_startup_armory,
    initialize,
    normalize_path,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_PORT = 8765


def _make_message(msg_type: str, **kwargs: Any) -> str:
    payload = {"type": msg_type, **kwargs}
    return json.dumps(payload)


def _load_config() -> ChatConfig:
    """Load config from environment, allowing empty API key initially."""
    api_key = os.environ.get("HEPHAISTOS_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    base_url = os.environ.get("HEPHAISTOS_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("HEPHAISTOS_MODEL", "gpt-4o-mini")
    return ChatConfig(api_key=api_key, base_url=base_url, model=model)


class ChatServer:
    def __init__(self) -> None:
        self.session: ChatSession | None = None
        self.pending_message_id: str | None = None

    def _get_or_create_session(self) -> ChatSession:
        if self.session is None:
            config = _load_config()
            self.session = create_session(config, discover_startup_armory())
        return self.session

    def _ensure_configured(self) -> None:
        """Ensure the session has a valid config with API key."""
        if self.session is None:
            self.session = create_session(_load_config(), discover_startup_armory())
        if not self.session.config.api_key or not self.session.config.api_key.strip():
            raise EngineError("No API key configured. Set HEPHAISTOS_API_KEY or OPENAI_API_KEY environment variable.")

    async def handle_message(
        self,
        websocket: WebSocketServerProtocol,
        data: dict[str, Any],
    ) -> None:
        msg_type = data.get("type", "")

        try:
            if msg_type == "send_message":
                await self._handle_send_message(websocket, data)
            elif msg_type == "switch_armory":
                self._handle_switch_armory(websocket, data)
            elif msg_type == "create_armory":
                self._handle_create_armory(websocket, data)
            elif msg_type == "list_sessions":
                self._handle_list_sessions(websocket, data)
            elif msg_type == "resume_session":
                self._handle_resume_session(websocket, data)
            elif msg_type == "save":
                self._handle_save(websocket)
            elif msg_type == "new_chat":
                self._handle_new_chat()
            else:
                await websocket.send(
                    _make_message("error", error=f"Unknown message type: {msg_type}")
                )
        except Exception as exc:
            logger.exception("Error handling message")
            await websocket.send(_make_message("error", error=str(exc)))

    async def _handle_send_message(
        self,
        websocket: WebSocketServerProtocol,
        data: dict[str, Any],
    ) -> None:
        message = data.get("message", "").strip()
        if not message:
            return

        # Ensure we have a valid config with API key before proceeding
        self._ensure_configured()
        session = self.session

        session.conversation.add("user", message)

        message_id = _generate_id()
        self.pending_message_id = message_id

        await websocket.send(
            _make_message(
                "message",
                message_id=message_id,
                role="user",
                content=message,
            )
        )

        assistant_id = _generate_id()
        accumulated = ""

        try:
            for chunk in stream_reply(session.config, session.conversation):
                accumulated += chunk
                await websocket.send(
                    _make_message(
                        "message_chunk",
                        message_id=assistant_id,
                        role="assistant",
                        content=chunk,
                    )
                )

            session.conversation.add("assistant", accumulated)
            if not session.title:
                session.title = _derive_title(session.conversation)
            session.dirty = True

            await websocket.send(
                _make_message(
                    "message_done",
                    message_id=assistant_id,
                )
            )
        except EngineError as exc:
            session.conversation.messages.pop()
            await websocket.send(
                _make_message(
                    "error",
                    error=str(exc),
                )
            )

    async def _handle_switch_armory(
        self,
        websocket: WebSocketServerProtocol,
        data: dict[str, Any],
    ) -> None:
        path_str = data.get("armory_path", "").strip()
        if not path_str:
            return

        try:
            armory_path = validate_armory_path(path_str)
            self._start_fresh_session(armory_path)
            await self._send_session_info(websocket)
        except ArmoryError as exc:
            await websocket.send(_make_message("error", error=str(exc)))

    async def _handle_create_armory(
        self,
        websocket: WebSocketServerProtocol,
        data: dict[str, Any],
    ) -> None:
        path_str = data.get("armory_path", "").strip()
        if not path_str:
            return

        armory_path = normalize_path(path_str)

        try:
            initialize(armory_path)
            self._start_fresh_session(armory_path)
            await self._send_session_info(websocket)
        except ArmoryError as exc:
            await websocket.send(_make_message("error", error=str(exc)))

    async def _handle_list_sessions(
        self,
        websocket: WebSocketServerProtocol,
        data: dict[str, Any],
    ) -> None:
        path_str = data.get("armory_path", "").strip()
        if not path_str:
            return

        try:
            armory_path = validate_armory_path(path_str)
            sessions = list_armory_sessions(armory_path)
            await websocket.send(
                _make_message(
                    "sessions_list",
                    sessions=sessions,
                )
            )
        except ArmoryError as exc:
            await websocket.send(_make_message("error", error=str(exc)))

    async def _handle_resume_session(
        self,
        websocket: WebSocketServerProtocol,
        data: dict[str, Any],
    ) -> None:
        path_str = data.get("armory_path", "").strip()
        session_id = data.get("session_id", "").strip()
        if not path_str or not session_id:
            return

        try:
            armory_path = validate_armory_path(path_str)
            config = _load_config()
            if not config.api_key or not config.api_key.strip():
                raise EngineError("No API key configured. Set HEPHAISTOS_API_KEY or OPENAI_API_KEY environment variable.")
            self.session = resume_session(config, armory_path, session_id)
            await self._send_session_info(websocket)
        except (ArmoryError, chat_storage.ChatStorageError) as exc:
            await websocket.send(_make_message("error", error=str(exc)))

    async def _handle_save(
        self,
        websocket: WebSocketServerProtocol,
    ) -> None:
        if self.session is None or self.session.armory_path is None:
            return

        if not self.session.dirty or not session_has_messages(self.session):
            return

        try:
            path = save_session(self.session)
            await websocket.send(_make_message("saved", path=str(path)))
        except chat_storage.ChatStorageError as exc:
            await websocket.send(_make_message("error", error=str(exc)))

    def _handle_new_chat(self) -> None:
        if self.session is None:
            return
        armory_path = self.session.armory_path
        self.session = create_session(self.session.config, armory_path)

    def _start_fresh_session(self, armory_path: Path | None) -> None:
        if (
            self.session is not None
            and self.session.dirty
            and self.session.armory_path is not None
        ):
            if session_has_messages(self.session):
                try:
                    save_session(self.session)
                except chat_storage.ChatStorageError:
                    pass
        self.session = create_session(
            self.session.config if self.session else _load_config(),
            armory_path,
        )

    async def _send_session_info(self, websocket: WebSocketServerProtocol) -> None:
        if self.session is None:
            return
        await websocket.send(
            _make_message(
                "session_info",
                session_id=self.session.session_id,
                model=self.session.config.model,
                base_url=self.session.config.base_url,
            )
        )
        await websocket.send(
            _make_message(
                "armory_info",
                armory_path=str(self.session.armory_path)
                if self.session.armory_path
                else None,
                source_file_count=self.session.source_file_count,
            )
        )


async def handle_connection(
    websocket: WebSocketServerProtocol,
) -> None:
    server = ChatServer()
    session = server._get_or_create_session()

    # Send session info - use placeholder if no API key configured
    await websocket.send(
        _make_message(
            "session_info",
            session_id=session.session_id,
            model=session.config.model,
            base_url=session.config.base_url,
        )
    )
    await websocket.send(
        _make_message(
            "armory_info",
            armory_path=str(session.armory_path) if session.armory_path else None,
            source_file_count=session.source_file_count,
        )
    )

    async for raw in websocket:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            await websocket.send(_make_message("error", error="Invalid JSON"))
            continue
        await server.handle_message(websocket, data)


def _generate_id() -> str:
    return secrets.token_hex(8)


async def run_server(port: int = DEFAULT_PORT) -> None:
    logger.info(f"Starting WebSocket server on port {port}")
    stop = asyncio.Event()

    def signal_handler() -> None:
        logger.info("Received shutdown signal")
        stop.set()

    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, signal_handler)
            except (OSError, ValueError):
                pass
    except RuntimeError:
        pass

    async with websockets.serve(
        handle_connection,
        "localhost",
        port,
        ping_interval=30,
        ping_timeout=10,
    ):
        await stop.wait()
        logger.info("Server shutdown complete")


def main(port: int = DEFAULT_PORT) -> None:
    try:
        asyncio.run(run_server(port))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
