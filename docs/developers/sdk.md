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
- `HephSdkCapabilities` and `get_sdk_capabilities()` for feature discovery.
- `validate_sdk_service_contract()` for implementation-route drift checks.
- `HephEvent` DTOs for structured turn streams.
- Session source-file snapshots and enable/disable controls for material scope.
- Explicit session disposal state for stale handles after replacement.
- Material, index, and extraction-health DTOs for armory management.
- Structured provider summaries for credential-source and active-provider status.
- Structured model choice and model switching helpers for provider-aware clients.
- Structured app settings snapshots and update helpers for GUI/mobile preferences.
- Dynamic service-state availability through `available_call_methods` and
  `available_stream_methods`, so clients can enable controls from state instead
  of duplicating busy, runtime, and session preconditions.
- Per-method availability records through `call_method_availability` and
  `stream_method_availability`, including stable unavailable reason codes for
  disabled controls.
- Abortable prompt and operation streams, including structured cancellation
  errors for transport clients.
- Top-level stable constants for service/JSONL method names, busy-allowed
  methods, availability requirements, unavailable reasons, SDK stability levels,
  and deprecation surfaces.
- Capability-advertised method availability requirements so clients can see
  which methods require an armory, a session, an armory-backed session, or
  attached source files.
- JSON-ready `to_dict()` helpers for transport clients.
- `JsonlSdkProcess`, `JsonlSdkClient`, and JSONL request/message helpers for
  Python clients that spawn `heph sdk serve`.
- `ArmorySummary`, `ArmoryValidationSummary`, `SessionSummary`, `ProviderSummary`,
  `ModelChoiceSummary`, and `HephMessage` value objects.

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

`HephRuntime.build_index(progress=...)` can also report live
`IndexProgressEvent` values while still returning the final `IndexSummary`.

For armory file pickers:

```python
from heph.sdk import HephRuntime

validation = HephRuntime.validate_armory("~/my-armory")
if validation.valid:
    runtime = HephRuntime.open_armory(validation.path)
else:
    print(validation.error)
```

`validate_armory()` checks the path, required layout, and marker file without
opening the armory, remembering it, or changing the active service runtime.

For model selection:

```python
from heph.sdk import HephRuntime

runtime = HephRuntime.plain()

for provider in runtime.list_providers():
    print(provider.display_name, provider.credential_source)

for choice in runtime.list_model_choices():
    print(choice.provider_display_name, choice.model, choice.is_current)

runtime.switch_model("openai", "gpt-5.5")
```

For app settings:

```python
from heph.sdk import HephService

service = HephService.plain()
settings = service.call("settings")["settings"]
service.call(
    "update_settings",
    {
        "theme": "light",
        "thinking_visibility": "all",
        "live_tokens_visible": True,
    },
)
```

`settings` returns `sdk_app_settings` with current values, read-only privacy
status, valid choice lists, and `mutable_keys`. `update_settings` persists
supported app preferences and applies display settings such as thinking
visibility and live token/cost visibility to the active runtime/session when one
exists. Privacy consent is intentionally summarized but not mutated through this
generic SDK method. Python GUI clients can import `SdkAppSettingContract`,
`SDK_APP_SETTING_CONTRACTS`, and `SDK_APP_SETTING_VALUE_TYPES` from `heph.sdk`
when building typed settings forms.

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

The serve command accepts startup overrides for provider/model settings,
generation limits, reasoning level, thinking visibility, and temperature. SDK
values advertised as `number` or `number_or_null` must be finite JSON numbers;
`NaN` and infinities are rejected before config or transport state changes.

The service speaks newline-delimited JSON on stdin/stdout. Each request is a
single JSON object with an `id`, `method`, and optional `params` object:

```json
{"id":"state-1","method":"state"}
{"id":"caps-1","method":"capabilities"}
{"id":"turn-1","method":"prompt","params":{"text":"Explain these notes."}}
{"id":"cancel-1","method":"abort"}
```

Responses are JSON objects with explicit transport types:

```json
{"type":"ready","protocol":"heph-sdk-jsonl","version":1,"capabilities":{...},"state":{...}}
{"type":"response","id":"state-1","ok":true,"result":{...}}
{"type":"stream_start","id":"turn-1","method":"prompt"}
{"type":"stream_event","id":"turn-1","event":{"type":"assistant_delta","delta":"..."}}
{"type":"stream_end","id":"turn-1","ok":true}
```

Python clients that spawn the process can use the managed process helper
instead of writing startup, shutdown, and framing code by hand:

```python
from heph.sdk import JsonlSdkProcess, JsonlSdkProcessOptions

options = JsonlSdkProcessOptions(armory_path="~/my-armory")

with JsonlSdkProcess(options) as process:
    ready = process.ready
    state = process.client.call("state")

    for event in process.client.stream("prompt", {"text": "Explain these notes."}):
        render(event)
```

`JsonlSdkProcessOptions` expands `~` in `armory_path` before spawning the child
process. `JsonlSdkProcess` starts `heph sdk serve`, reads the ready handshake
with a startup timeout, and closes stdin on exit so the service can shut down
cleanly; stdin EOF aborts an active prompt or operation stream before shutdown
waits for worker threads. If the process does not exit within its shutdown
timeout, it is killed. If the killed process still does not exit within the
timeout, `close()` raises `JsonlSdkProcessError` rather than a raw subprocess
error. Startup, shutdown, close, and stream-control timeouts must be finite
non-negative numbers or `None`; invalid timeout values raise SDK client/process
errors before touching transport state.
`create_armory=True` requires `armory_path`; `session_id` cannot be combined
with `start_session=False`.
Apps that launch Heph from a sandbox, app bundle, or test harness can pass an
explicit `cwd` and `env` to `JsonlSdkProcess` so the child process uses app-owned
paths, settings, and dependency resolution. Startup failures that happen before
the ready handshake include a bounded stderr tail, and `process.stderr_tail`
remains available after the child exits for app logs or diagnostics screens. The
latest known child exit status is exposed as `process.returncode` even after
`close()` clears the live process handle.
`JsonlSdkProcess.close()` also marks the managed `JsonlSdkClient` closed before
tearing down child pipes, so stale client references fail with a stable
`JsonlSdkClientProtocolError` instead of leaking pipe-specific errors. Direct
`JsonlSdkClient.close()` is idempotent, wakes pending stream-control waiters,
and only closes the helper state; callers that own custom streams still own the
actual pipe lifecycle.
`JsonlSdkClient.read_ready()` validates the protocol/version handshake and the
advertised capability compatibility policy. `JsonlSdkClient` and
`JsonlSdkProcess` accept an `accepted_stability_levels` sequence for clients
that intentionally opt into non-public SDK stability; the default is public-only.
`call()` raises
`JsonlSdkServerError` for structured server error envelopes and validates
successful results against the advertised JSONL call result spec before
returning them. `stream()` yields event payloads until `stream_end`, validates
each event against that stream method's advertised event contract, and raises
the same structured error when a stream fails. Cancellation stream failures use
the `JsonlSdkStreamCancelledError` subclass so clients can handle user-initiated
cancel separately from model and server failures. `call()` only accepts JSONL
call methods, and `stream()` only accepts JSONL stream methods; wrong-category
requests are rejected before anything is written to the child process. Low-level
read/write failures from app-owned pipes are raised as
`JsonlSdkClientProtocolError` so callers can handle transport failures through
one SDK error family. On the server side, `heph sdk serve` treats a closed
stdin/stdout transport as normal shutdown, while direct `JsonlSdkServer` callers
can catch `JsonlSdkTransportClosedError` if they need custom lifecycle handling. More
advanced clients can use `JsonlSdkClient`, `encode_jsonl_request()`,
`parse_jsonl_message()`, `jsonl_ready_from_message()`, and
`jsonl_error_from_message()` directly when they need their own subprocess
lifecycle, request routing, or UI event loop. `encode_jsonl_request()` and
`JsonlSdkClient.write_request()` validate method names and params against the
advertised JSONL method specs before writing to the transport.
When a UI cancel button needs to stop the active stream while `stream()` is
being consumed, call `JsonlSdkClient.abort_active_stream()` from the UI control
path. The stream iterator consumes the interleaved abort response and then
raises `JsonlSdkStreamCancelledError` from the stream's final error envelope.
For status panels that need to refresh during a long stream, use
`JsonlSdkClient.call_active_stream()` for busy-safe methods such as `state`,
`capabilities`, and `settings`; the stream iterator keeps ownership of the
reader and routes the interleaved response back to the waiting caller. If a
timed active-stream call returns late, the stream iterator drains and discards
that late response or error so it cannot leak into the next request.
Use the high-level `call()` and `stream()` helpers only while no stream is being
consumed. During an active stream, `call_active_stream()` and
`abort_active_stream()` require the stream iterator to be running so their
responses can be consumed by that single reader.
When you provide explicit request ids, keep active stream and stream-control ids
unique. The Python client rejects collisions before writing to the transport,
and the JSONL server rejects requests whose ids collide with the active stream;
both checks prevent stream events from being routed to the wrong waiting caller.

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
resumed, or forked session. When `HephService` replaces the active session or
runtime, the previous `HephSession` is disposed. Stale direct handles keep their
identity and snapshots, expose `is_disposed`, and reject new streams,
subscriptions, saves, refreshes, and source-scope mutations with `HephSdkError`.
Direct `HephRuntime.fork_session()` also requires a live idle session handle
from the same runtime armory; `HephService(runtime=..., session=...)` enforces
the same ownership rule at construction time.

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
- source scope: inspect and enable or disable attached source files;
- config: inspect and switch model/provider settings, reasoning level, and
  thinking visibility;
- app settings: inspect and update GUI/mobile preferences such as theme,
  activity trace mode, thinking visibility, live token/cost visibility, and
  vocabulary strictness.

The Python SDK remains the source of truth. The transport is only a
serialization boundary for non-Python clients.

`HephService` is the intended core for that transport boundary. It maintains an
active runtime and optional active session. Direct Python clients should use
`state_snapshot()` for typed `HephSdkState` values, while transports can keep
calling `state()` for the same contract-validated JSON-ready dictionary shape.
The snapshot and payload include a top-level `service` object with
`is_busy`, `prompt_active`, `active_operation`, `available_call_methods`, and
`available_stream_methods`, so clients can disable state-changing controls
without inspecting internal `ChatSession` objects or reimplementing busy-method
policy. The same service object also includes `call_method_availability` and
`stream_method_availability`: ordered records with `method`, `available`, and
`unavailable_reason`. Standard SDK-generated reason codes are advertised in
`capabilities.service.method_unavailable_reasons` and include values such as
`busy`, `missing_armory`, `missing_session`, `missing_armory_session`, and
`missing_session_sources`.
`prompt_active` is true for both service-owned prompt streams and direct streams
on the active `HephSession`; `active_operation` names non-prompt operation
streams such as `build_index`. `available_call_methods` lists the call methods
that are valid for the current runtime and session state, then narrows to the
busy-safe calls during a prompt or operation stream. `available_stream_methods`
lists only currently valid streams: `prompt` requires an active session, and
`build_index` requires an open armory. Direct Python state uses service stream
method names, while JSONL transport state maps those same currently available
streams and detailed stream availability records to JSONL names such as
`build_index_stream`.
Session state includes display settings that can affect rendering for the active
conversation, including `thinking_visibility`, `live_tokens_visible`, and
`live_cost_visible`.

Clients can discover the supported contract with `get_sdk_capabilities()`,
`HephService.capabilities()`, or the transport `capabilities` method. The JSONL
server also includes the same capability payload in its initial `ready` message.
For code generation or CI contract snapshots without starting a transport
service, `heph sdk capabilities` prints the same capability contract as JSON.
The checked fixture `docs/developers/sdk-capabilities.v35.json` is the current
versioned conformance artifact; external clients can diff it in CI and update it
only when they intentionally accept a new SDK capability version.
Capabilities list service methods, JSONL method names, stream event types, state
fields, JSONL message types, JSONL error codes, calls that remain available
while a stream is active, method availability requirements, and standard
method-unavailable reason codes.
Busy-safe calls are advertised in both `service.busy_allowed_call_methods` and
`jsonl.busy_allowed_call_methods` so embedded and transport clients can discover
which controls may remain interactive during a prompt or operation stream.
The `jsonl.message_specs` section describes the top-level transport envelopes
(`ready`, `response`, `error`, `stream_start`, `stream_event`, and `stream_end`)
so native clients can generate wire decoders without scraping examples. The
stdio server validates outgoing envelopes against those specs before writing
them to clients, including concrete `stream_event.event` payloads resolved from
the advertised event discriminator.
The `jsonl.request_spec` section describes the inbound request envelope
(`id`, `method`, and optional `params`) so transport clients can generate
encoders and local request validation from the same capability payload.
JSONL requests with top-level fields outside the advertised request envelope are
rejected with `invalid_request`, as are request fields whose JSON value type
does not match the advertised request spec.
The payload also includes a `methods` section with JSON-ready parameter specs
for service calls, service streams, JSONL calls, and JSONL streams. Native
clients can use those specs to build request validation, disable incomplete
forms, and keep transport wrappers aligned with the advertised SDK contract.
Parameter specs use the same SDK value-type language as result DTOs, including
reusable SDK types, arrays, maps, and literals.
Enum-like string parameters include a non-empty `choices` list, for example
theme, activity trace mode, vocabulary strictness, thinking visibility, and
reasoning level.
The SDK service and JSONL transport enforce the same method specs at runtime:
unsupported parameters, missing required parameters, wrong JSON value types, and
values outside advertised `choices` are rejected instead of being ignored.
The `results` section describes the payload returned by each service and JSONL
call method, using stable SDK DTO names such as `sdk_state`,
`sdk_session_state`, `provider_summary`, and `index_summary`. Service calls and
transport-shaped JSONL responses validate result payloads against the advertised
result and reusable DTO field specs before returning to clients.
The `streams` section describes the event types each service and JSONL stream
method can emit, plus the normal completion event such as `turn_complete` for
prompt streams and `index_complete` for index streams. Service stream events are
validated against those advertised event specs before reaching direct Python or
transport clients.
The `availability` section describes each service and JSONL method's stable
precondition. Each method maps to a `requirement` value such as `always`,
`armory`, `session`, `armory_session`, or `session_sources`, plus the
`unavailable_reason` that state snapshots use when that requirement is not met.
The `types` section resolves those reusable SDK DTO names into field specs for
client generators that want typed value objects instead of dictionaries.
Capability sections such as `service`, `jsonl`, `streams`, and `availability`
also have named DTO specs, so clients and runtime validators can detect nested
capability payload drift instead of treating the whole contract as loose maps.
Python clients can import the matching spec dataclasses, such as
`SdkMethodSpec`, `SdkObjectFieldSpec`, `SdkResultSpec`, and `SdkTypeSpec`, from
the public `heph.sdk` facade.
Spec dictionaries use `map<...>` value types, for example
`map<sdk_method_spec>` and `map<sdk_result_spec>`, so generated clients can
validate dynamic method-name keys while still checking each value structurally.
`validate_sdk_capabilities()` checks the advertised graph for list/spec drift,
availability drift, malformed value-type grammar, unresolved DTO type
references, JSONL request-envelope drift, discriminator drift, and stream event
drift.
`validate_sdk_service_contract()` checks the service implementation routes
against those advertised methods and route parameter contracts. `HephService`
runs both checks during construction.
`validate_sdk_jsonl_transport_contract()` checks JSONL dispatch routes and
transport method specs, including parameter contracts, against the advertised
JSONL surface and underlying service routes. `JsonlSdkServer` runs this check
before serving requests. Keep all three green when extending the SDK surface.
The `errors.jsonl` section describes each JSONL error code so native clients can
present stable recovery copy without hard-coding the Python docs. JSONL error
payloads always include `code`, `message`, and nullable `unavailable_reason`;
`unavailable_reason` is populated with the same stable reason values used by
state availability records when a valid method is unavailable or busy.
The `fields` section describes service, runtime, and session state field types
and nullability for clients that generate typed wrappers around the JSON-ready
state payload.
The `events.specs` section describes each SDK stream event payload so clients
can generate discriminated event unions without scraping examples or Python DTOs.
The `sdk_event` DTO is the shared `"type"` discriminator for those event
payloads; use `events.specs` for each concrete event shape.
The capability payload has its own `version`, separate from the JSONL
`protocol` and wire `version`. Its `compatibility` section is the machine-readable
client negotiation policy: `stability`, `min_client_capabilities_version`,
`current_capabilities_version`, `supported_jsonl_versions`, and short policy
strings for breaking changes, additive changes, and deprecations. GUI and mobile
clients should check this section during startup and refuse servers outside their
supported capability or JSONL version range.
Python clients can use `validate_sdk_client_compatibility()` /
`ensure_sdk_client_compatibility()` with a native `HephSdkCapabilities` object, or
`validate_sdk_client_payload_compatibility()` /
`ensure_sdk_client_payload_compatibility()` with the JSON-ready capability payload
from a transport handshake. These helpers accept only `public` SDK stability by
default; clients that intentionally bind to `preview` or `internal` surfaces
must pass `accepted_stability_levels` explicitly. Empty, non-string, or unknown
accepted stability levels are reported as compatibility issues so startup
negotiation can fail through one SDK error family.
The top-level `deprecations` list advertises planned removals as structured
entries with `surface`, `name`, `since_version`, nullable `removal_version`,
`replacement`, and `message`. Clients should prefer replacements when present and
keep rendering deprecated features until the compatibility policy allows removal.

`heph sdk serve` is the first concrete transport. It supports:

- `state`
- `capabilities`
- `use_plain_runtime`
- `open_armory`
- `create_armory`
- `list_armories`
- `validate_armory`
- `new_session`
- `resume_session`
- `fork_session`
- `list_sessions`
- `save_session`
- `messages`
- `ask`
- `prompt`
- `abort`
- `settings`
- `list_providers`
- `list_model_choices`
- `switch_model`
- `set_source_enabled`
- `list_materials`
- `import_materials`
- `build_index`
- `build_index_stream`
- `scan_extraction_health`
- `update_config`
- `update_settings`

`prompt` and `build_index_stream` are streaming methods. While a prompt or
operation stream is active, clients can still call `state`, `capabilities`, and
`settings`; `abort` cancels active prompt streams and active operation streams
such as `build_index_stream`. Operation cancellation is observed at operation
checkpoints such as progress boundaries. Direct Python streams raise
`HephSdkOperationCancelledError`; JSONL streams end with `ok:false` and the
structured error code `"cancelled"`. Other service methods are rejected until
the stream ends. Clients should gate regular request controls from
`service.available_call_methods` and stream controls from
`service.available_stream_methods`; `service.is_busy`, `prompt_active`, and
`active_operation` remain available for status display. A plain runtime without
an active session therefore advertises no streams, an active plain session
advertises `prompt`, an open armory without a session advertises index
operations, and an armory-backed session advertises both prompt and index
streams. This lifecycle rule is enforced by `HephService` itself, so it applies
to both direct Python embeddings and JSONL transport clients. In Python, busy
requests raise `HephSdkBusyError`, while valid methods that are unavailable for
the current runtime/session state raise `HephSdkUnavailableError`. In JSONL,
those conditions are reported with error codes `"busy"` and `"unavailable"` plus
the structured `unavailable_reason` value.
Model runtime failures raised while handling a prompt are wrapped as
`HephSdkModelError` in direct Python embeddings and reported as structured JSONL
stream errors for transport clients. When the lower runtime classifies the
failure, JSONL uses the concrete model error code; otherwise it falls back to
`"engine_error"`.
JSONL `abort` is scoped to the prompt or operation stream owned by that
transport process; when no JSONL stream is active it returns a no-op state
payload.
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
- `reasoning_delta`
- `tool_call`
- `tool_result`
- `material_operation`
- `compact_request`
- `turn_complete`
- `notice`
- `guardrail`
- `index_progress`
- `index_complete`

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
facade. Factory helpers validate the same startup invariants as the process
wrapper: `create_armory=True` requires `armory_path`, and
`create_heph_service()` rejects `session_id` when `start_session=False`.
`create_heph_runtime()` rejects `session_id` because runtime construction does
not resume sessions, while `create_heph_session()` requires `start_session=True`
because it always returns a live session result.

## Subscriptions and Abort

`HephSession.prompt()` yields events directly. SDK clients can also subscribe to
the same events:

```python
unsubscribe = session.subscribe(lambda event: log_event(event.to_dict()))

for event in session.prompt("Summarize chapter 2."):
    render(event)

unsubscribe()
```

Listener exceptions are logged and isolated. A failed listener does not stop the
prompt stream or prevent later listeners from receiving the same event.

`session.abort()` sets the active turn's abort signal. A transport adapter can
wire this to a cancel button or JSON-RPC `abort` method. `session.is_streaming`
is true while a turn is active. While streaming, direct session clients can
observe state, receive events, and abort the turn; mutation methods such as
`set_source_enabled()`, `refresh_materials()`, and `save()` raise
`HephSdkBusyError` until the stream ends.
`session.is_disposed` is true after the session has been replaced or explicitly
disposed. Disposed session snapshots remain readable, but clients should switch
back to the current service state before starting more work.

## Service Dispatch

`HephService.call(method, params)` handles non-streaming methods such as
`state`, `new_session`, `messages`, `ask`, `import_materials`, and
`update_config`.

`HephService.stream("prompt", {"text": "..."})` yields JSON-ready event
dictionaries for streaming turns. `HephService.stream("build_index")` yields
`index_progress` events and a final `index_complete` event while preserving the
regular `build_index` response method. Keeping streaming separate from regular
calls lets WebSocket, JSONL, and JSON-RPC adapters choose their own framing.

The stdio transport maps the same concept onto request IDs. A `prompt` request
emits `stream_start`, zero or more `stream_event` objects, and one
`stream_end`. A `build_index_stream` request uses the same stream framing for
index progress. Non-streaming requests emit one `response` or `error`.

The JSONL message types advertised through capabilities are:

- `ready`
- `response`
- `error`
- `stream_start`
- `stream_event`
- `stream_end`

The JSONL error codes advertised through capabilities are:

- `invalid_json`: a request line is not valid JSON.
- `invalid_request`: a request has the wrong envelope, id, method, or params
  shape.
- `busy`: a state-changing request was rejected while a prompt or operation
  stream was active.
- `unavailable`: a valid method is not available for the current runtime/session
  state.
- `sdk_error`: the SDK rejected a valid request, such as opening a missing
  armory.
- `cancelled`: an active SDK operation stream was cancelled.
- `engine_error`: the model runtime rejected a request without a more specific
  code.
- `account_setup`: provider account setup or billing prevented the model
  request.
- `provider_capacity`: provider capacity or rate limiting prevented the model
  request.
- `missing_credentials`: provider credentials are missing for the selected
  model.
- `missing_model_source`: no model source is configured.
- `missing_model`: no model is configured.
- `model_unavailable`: the selected model is unavailable for the configured
  provider endpoint.
- `circuit_open`: the model provider circuit breaker is open after recent
  failures.
- `internal_error`: an unexpected server-side exception escaped the SDK layer.

Every JSONL `error` payload includes `code`, `message`, and nullable
`unavailable_reason`. The reason is populated for `busy` and `unavailable`
responses so clients can reuse the same disabled-control recovery logic they
use for service-state availability records.

## Boundary Rules

- SDK modules must not import `interfaces.*`.
- SDK methods should return values or yield events; they should not print.
- SDK wrappers should hide mutable harness internals such as `ChatSession`,
  `TurnContract`, RAG indexes, and learning state unless a public DTO exists.
- New UI behavior should use SDK services rather than copying CLI or TUI logic.
- Cross-language clients should target a transport built over the SDK, not the
  internal harness objects.
