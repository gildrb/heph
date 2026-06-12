# Heph SDK

Heph's SDK is the first stable embedding layer for native apps, GUI shells,
automation, and future language-agnostic transports.

The goal is not to reimplement Heph in every UI. Native clients should own
their presentation and platform behavior, while Heph keeps one shared runtime
for armories, retrieval, citations, memory, provider configuration, and session
lifecycle.

```text
SwiftUI / GUI / automation client
  -> transport or direct Python embedding
  -> heph.sdk.HephRuntime
  -> hephaion chat, armory, retrieval, memory, and AI runtime services
```

## Current Surface

`heph.sdk` currently exposes:

- `HephRuntime` for armory attachment and session replacement.
- `HephSession` for one active chat session.
- `HephService` for stateful, dictionary-returning transport adapters.
- `HephEvent` DTOs for structured turn streams.
- Material, index, and extraction-health DTOs for armory management.
- JSON-ready `to_dict()` helpers for transport clients.
- `ArmorySummary`, `SessionSummary`, and `HephMessage` value objects.

```python
from heph.sdk import AssistantDelta, HephRuntime

runtime = HephRuntime.open_armory("~/my-armory")
session = runtime.new_session()

for event in session.prompt("Explain these notes."):
    if isinstance(event, AssistantDelta):
        print(event.delta, end="")
```

For one-shot usage:

```python
from heph.sdk import HephRuntime

runtime = HephRuntime.open_armory("~/my-armory")
session = runtime.new_session()
answer = session.ask("What should I review first?")
```

For material management:

```python
from heph.sdk import HephRuntime

runtime = HephRuntime.open_armory("~/my-armory")
runtime.import_materials("~/Downloads/week-1-notes.pdf")

for material in runtime.list_materials():
    print(material.display_name, material.role)

index = runtime.build_index()
health = runtime.scan_extraction_health()
```

For transport-style integration, use the service facade:

```python
from heph.sdk import HephService

service = HephService.open_armory("~/my-armory")
service.new_session()

for event in service.prompt("Explain these notes."):
    send_json(event)
```

For native clients that cannot embed Python directly, spawn the stdio service:

```bash
heph sdk serve --armory ~/my-armory
```

The service speaks newline-delimited JSON on stdin/stdout. Each request is a
single JSON object with an `id`, `method`, and optional `params` object:

```json
{"id":"state-1","method":"state"}
{"id":"turn-1","method":"prompt","params":{"text":"Explain these notes."}}
{"id":"cancel-1","method":"abort"}
```

Responses are JSON objects with explicit transport types:

```json
{"type":"ready","protocol":"heph-sdk-jsonl","version":1,"state":{...}}
{"type":"response","id":"state-1","ok":true,"result":{...}}
{"type":"stream_start","id":"turn-1","method":"prompt"}
{"type":"stream_event","id":"turn-1","event":{"type":"assistant_delta","delta":"..."}}
{"type":"stream_end","id":"turn-1","ok":true}
```

## Session and Runtime Split

Keep two concepts separate:

- `HephSession` owns one conversation: prompt streaming, final answer helpers,
  message snapshots, refresh, and save.
- `HephRuntime` owns replacement flows: create/open armories, new sessions,
  resume sessions, fork sessions, list sessions, import materials, index
  materials, and scan extraction health.

That split matters for native clients because replacing a session should be a
clear state transition. A SwiftUI app can hold a selected session ID, subscribe
to its events, and then re-subscribe when the runtime switches to a new,
resumed, or forked session.

## Native Apple Path

For a native Apple app, prefer a transport process over direct Swift-to-Python
binding:

```text
SwiftUI app
  -> local JSONL stdio process today
  -> JSON-RPC or WebSocket client later
  -> Heph SDK service
  -> heph.sdk.HephRuntime
```

The transport should expose the same SDK concepts:

- armories: create, open, list, validate;
- sessions: new, resume, fork, list, save;
- turns: prompt, abort, stream events;
- messages: list current conversation messages;
- config: inspect and switch model/provider settings.

The Python SDK remains the source of truth. The transport is only a
serialization boundary for non-Python clients.

`HephService` is the intended core for that transport boundary. It maintains an
active runtime and optional active session. Direct Python clients should use
`state_snapshot()` for typed `HephSdkState` values, while transports can keep
calling `state()` for the same JSON-ready dictionary shape.
The snapshot and payload include a top-level `service` object with
`prompt_active`, so clients can disable state-changing controls without
inspecting internal `ChatSession` objects.

`heph sdk serve` is the first concrete transport. It supports:

- `state`
- `use_plain_runtime`
- `open_armory`
- `create_armory`
- `list_armories`
- `new_session`
- `resume_session`
- `fork_session`
- `list_sessions`
- `save_session`
- `messages`
- `ask`
- `prompt`
- `abort`
- `list_materials`
- `import_materials`
- `build_index`
- `scan_extraction_health`
- `update_config`

`prompt` is the streaming method. While a prompt stream is active, clients can
still call `state` and `abort`; other service methods are rejected until the
stream ends. This lifecycle rule is enforced by `HephService` itself, so it
applies to both direct Python embeddings and JSONL transport clients.
In Python, this raises `HephSdkBusyError`, a subclass of `HephSdkError`. In
JSONL, the same condition is reported with error code `"busy"`.
JSONL `abort` is scoped to the prompt stream owned by that transport process;
when no JSONL stream is active it returns a no-op state payload.
Direct `HephSession` users get the same `HephSdkBusyError` when starting a
second prompt on a session that is already streaming.

## Event Contract

SDK events are stable DTOs with a `kind` attribute in Python and a `"type"` key
in their dictionary form:

```python
event.to_dict()
# {"type": "assistant_delta", "delta": "..."}
```

The current event families are:

- `assistant_delta`
- `tool_call`
- `tool_result`
- `material_operation`
- `compact_request`
- `turn_complete`
- `notice`
- `guardrail`

UI clients should render these structurally. Do not parse assistant text or
notice wording to infer state.

## Factory Helpers

For Pi-style session construction, use the factory helpers:

```python
from heph.sdk import HephSdkOptions, create_heph_session

result = create_heph_session(
    HephSdkOptions(
        armory_path="~/my-armory",
        model="gpt-4o-mini",
        temperature=0.2,
    )
)

session = result.session
```

Use `create_heph_runtime()` when an app wants to own session replacement
itself, and `create_heph_service()` when it wants a stateful transport-ready
facade.

## Subscriptions and Abort

`HephSession.prompt()` yields events directly. SDK clients can also subscribe to
the same events:

```python
unsubscribe = session.subscribe(lambda event: log_event(event.to_dict()))

for event in session.prompt("Summarize chapter 2."):
    render(event)

unsubscribe()
```

`session.abort()` sets the active turn's abort signal. A transport adapter can
wire this to a cancel button or JSON-RPC `abort` method. `session.is_streaming`
is true while a turn is active.

## Service Dispatch

`HephService.call(method, params)` handles non-streaming methods such as
`state`, `new_session`, `messages`, `ask`, `import_materials`, and
`update_config`.

`HephService.stream("prompt", {"text": "..."})` yields JSON-ready event
dictionaries for streaming turns. Keeping streaming separate from regular calls
lets WebSocket, JSONL, and JSON-RPC adapters choose their own framing.

The stdio transport maps the same concept onto request IDs. A `prompt` request
emits `stream_start`, zero or more `stream_event` objects, and one
`stream_end`. Non-streaming requests emit one `response` or `error`.

## Boundary Rules

- SDK modules must not import `interfaces.*`.
- SDK methods should return values or yield events; they should not print.
- SDK wrappers should hide mutable harness internals such as `ChatSession`,
  `TurnContract`, RAG indexes, and learning state unless a public DTO exists.
- New UI behavior should use SDK services rather than copying CLI or TUI logic.
- Cross-language clients should target a transport built over the SDK, not the
  internal harness objects.
