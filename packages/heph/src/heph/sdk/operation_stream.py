"""Worker-thread stream helper for SDK operation streams."""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from queue import Queue

type OperationStreamPayload = dict[str, object]
type OperationStreamPublish = Callable[[OperationStreamPayload], None]
type OperationStreamWorker = Callable[[OperationStreamPublish], OperationStreamPayload | None]


@dataclass(frozen=True, slots=True)
class _OperationStreamDone:
    payload: OperationStreamPayload | None = None
    error: BaseException | None = None


type _OperationStreamItem = OperationStreamPayload | _OperationStreamDone


def iter_operation_stream(
    *,
    thread_name: str,
    worker: OperationStreamWorker,
) -> Iterator[OperationStreamPayload]:
    """Yield payloads published by *worker* and surface its final result or error."""
    items: Queue[_OperationStreamItem] = Queue()

    def publish(payload: OperationStreamPayload) -> None:
        items.put(payload)

    def run_worker() -> None:
        try:
            payload = worker(publish)
        except BaseException as exc:
            items.put(_OperationStreamDone(error=exc))
        else:
            items.put(_OperationStreamDone(payload=payload))

    thread = threading.Thread(target=run_worker, name=thread_name)
    thread.start()
    try:
        while True:
            item = items.get()
            if isinstance(item, _OperationStreamDone):
                if item.error is not None:
                    raise item.error
                if item.payload is not None:
                    yield item.payload
                return
            yield item
    finally:
        thread.join()


__all__ = [
    "OperationStreamPayload",
    "OperationStreamPublish",
    "OperationStreamWorker",
    "iter_operation_stream",
]
