# API Backend Calibration

This note explains how LTE should be interpreted when the inference backend is remote rather than local.

## Core Principle

LTE is a deployer-side scaffold. The deployer still controls:

- prompts and prompt suites,
- contract evaluation,
- trigger logic,
- intervention states,
- and audit artifacts.

When LTE is used with an API backend, only inference moves remote. The accountability layer remains local.

## What Stays Comparable

Across local and API-backed runs, LTE should preserve the same:

- prompt content,
- system instructions,
- contracts,
- benchmark structure,
- stress procedure,
- and intervention vocabulary.

Those shared elements make the resulting contract failures, recoverable/unrecoverable splits, and trigger patterns meaningfully comparable.

## What Requires Calibration

Some operational signals do not mean the same thing across backends.

### Latency

For local MLX runs, latency primarily reflects on-device operational degradation under growing context.

For API runs, latency reflects end-to-end client-observed service latency, which may include network conditions, provider queueing, and service variability that are not equivalent to local runtime collapse.

Because of that difference, LTE should not treat a single gated API latency exceedance the same way it treats a single gated local latency exceedance.

Current policy:

- local backends may fire `latency_cliff` on any gated latency exceedance,
- API backends fire `latency_cliff` only on a hard trigger: 2 of the last 3 gated stress steps exceed the latency threshold.

This keeps latency observable for hosted deployments without allowing one-off network noise to dominate the intervention decision.

### Token Counting

Token accounting also differs by backend.

- `mlx` uses native tokenizer counts and fails hard if native counting is unavailable.
- `openai` and `anthropic` use provider-reported usage tokens.
- `mock` uses approximate counting only for fixture generation and smoke tests.

This means cross-backend comparisons should primarily rely on contract outcomes and trigger regimes, while raw token counts should be interpreted with backend awareness.

## Paper Framing

For the paper, the clean methodological claim is:

> LTE holds the deployer-side scaffold constant across local and hosted inference backends, while calibrating backend-dependent operational signals such as latency according to what they actually measure.

That preserves the central objective of the work. LTE is not a claim that every metric has identical meaning across infrastructure layers. It is a claim that deployers can apply a common accountability scaffold across those layers without collapsing unlike signals into a false apples-to-apples comparison.
