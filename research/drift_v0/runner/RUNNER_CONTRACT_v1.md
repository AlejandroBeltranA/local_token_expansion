# RUNNER CONTRACT v1

## Purpose

`evaluate_events.py` consumes raw runner events JSONL and emits evaluated JSONL with fixed trigger flags
and intervention decisions for `drift_v0`.

`run_experiments.py` can now emit raw events with in-loop trigger evaluation and immediate retry/escalation
execution, so recovery metrics are measured from actual runtime behavior.

## Input Contract

Each input line must be a JSON object. Required by protocol for stable output:

- `run_id`
- `experiment_id`
- `task_id`
- `model`
- `turn`
- `prompt`
- `response`

Recommended IO telemetry fields:

- `seed`
- `tokens_in`
- `tokens_out`
- `latency_ms`
- `episode_id`

Optional task metadata (if not supplied via `--task-pack`):

- `verifier`
- `expected_schema`
- `max_words`
- `sentences`

Optional state reference used for contradiction checks:

- `expected_state` (or `state_expected` / `target_state`)

## Verifier Behavior

Registered triggers:

- `schema_failure`
  - `schema_json` and `state_consistency`: validates JSON parse + schema from registry.
  - `length_and_sentence_count`: validates `max_words` and exact sentence count.
- `repetition_loop`
  - true on high prior-turn 4-gram overlap or duplicate-sentence ratio.
- `state_contradiction`
  - true when `consistency_check=false`, expected-state mismatch, user identity drift, or
    action/balance directional contradiction in state-like payloads.

## Intervention Policy

Two-step controller per episode:

1. First triggered turn: one retry action (`retry_schema_constrained`, `retry_loop_break`, `retry_state_reconcile`).
2. If a subsequent turn still triggers before recovery:
   - `state_contradiction` -> `escalate_human_review`
   - otherwise -> `reset_session_minimal_context`

`recovered=true` only when a clean turn follows a previously attempted retry.

## Output Contract

Every output line is JSON with these protocol-stable fields (always present):

- `run_id`
- `experiment_id`
- `task_id`
- `model`
- `seed`
- `turn`
- `prompt`
- `response`
- `tokens_in`
- `tokens_out`
- `latency_ms`
- `schema_failure`
- `repetition_loop`
- `state_contradiction`
- `intervention_action`
- `recovered`
- `escalated`

Any extra input fields are preserved after the stable protocol fields.

## Runtime Raw Event Extensions (`run_experiments.py`)

When running `run_experiments.py`, each generated attempt (primary and retry) is written as its own event row.
Additional fields:

- `attempt_kind`: `primary` or `retry`
- `parent_turn`: `null` for primary, original turn number for retry
- `policy_applied`: concrete action executed for that attempt (`none`, `retry_*`, `reset_session_minimal_context`, `escalate_human_review`)

Closed-loop policy:

1. Generate primary response and evaluate triggers in-loop.
2. If action is `retry_*`, generate exactly one retry response immediately with a trigger-specific repair prompt.
3. Re-evaluate retry response:
   - if clean: mark recovered and continue.
   - if unresolved: apply and log step-2 policy (`reset_session_minimal_context` or `escalate_human_review`).

## CLI Usage

```bash
python research/drift_v0/runner/evaluate_events.py \
  --input research/drift_v0/examples/events_sample.jsonl \
  --output /tmp/evaluated.jsonl \
  --task-pack research/drift_v0/tasks/e1_single_turn_sample.jsonl \
  --task-pack research/drift_v0/tasks/e2_short_horizon_sample.jsonl \
  --schema-registry research/drift_v0/tasks/schema_registry.json
```

If `--task-pack` is omitted, event-level verifier fields are used when present.
