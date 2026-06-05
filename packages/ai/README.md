# heph-ai

Provider, model, and runtime primitives for Heph.

This package owns API configuration, provider auth, model catalogs, streaming
runtime behavior, retry/resilience, usage accounting, and request shaping. It
must stay below app, harness, and interface packages.
