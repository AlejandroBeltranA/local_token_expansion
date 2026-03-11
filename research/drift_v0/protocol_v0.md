# Protocol v0

## Objective

Estimate early failure signals in local LLM workflows and map those signals to explicit intervention
actions suitable for accountability framing.

## Experiments

- `E1` (baseline): 2 models, 40 single-turn tasks, 1 run/task.
- `E2` (short horizon): same 2 models, 20 tasks, 3 turns/task, carried state.
- `E3` (context pressure): best E2 model, same 20 tasks, context budgets `1k` and `4k`.

## Fixed Triggers (pre-registered)

- `schema_failure`: output violates required JSON schema or strict format contract.
- `repetition_loop`: high overlap with prior turn (`4-gram` repetition or duplicate sentence ratio).
- `state_contradiction`: output conflicts with tracked state object for the episode.

## Intervention Policy

- Step 1 (recovery attempt): run one trigger-specific repair prompt.
- Step 2 (escalation):
  - if still failing: reset session with minimal state snapshot, or
  - escalate to human review for unresolved state contradiction.

## Logging Contract (per turn)

- identifiers: `run_id`, `experiment_id`, `task_id`, `model`, `seed`, `turn`
- IO: `prompt`, `response`, `tokens_in`, `tokens_out`, `latency_ms`
- trigger flags: `schema_failure`, `repetition_loop`, `state_contradiction`
- policy outputs: `intervention_action`, `recovered`, `escalated`

## Primary Metrics

- failure rate by trigger and experiment
- first-failure turn distribution (E2/E3)
- recovery success rate after one repair attempt
- E3 degradation delta (`4k` minus `1k`)
