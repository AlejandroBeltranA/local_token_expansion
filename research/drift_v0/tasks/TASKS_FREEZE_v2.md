# TASKS Freeze v2

- Freeze timestamp (UTC): `2026-02-25T13:43:32Z`
- Branch: `codex/drift-v0-agent-a-tasks`
- Scope: `research/drift_v0/tasks/`
- Status: Frozen for E3 pressure-focused run

## Files

- `e2_tasks_v2.jsonl`

## Why v2

This version keeps E2 family composition and verifier contracts, but increases carried state payload and memory constraints so E3 (`1k` vs `4k` budgets) can separate performance under realistic context pressure and recoverability checks.

## Composition

- Episodes: 20
- Turns per episode: 3
- Rows: 60
- `state_update` episodes: 10
- `strict_json` episodes: 6
- `instruction_compression` episodes: 4

## Pressure Additions

Every row in `e2_tasks_v2.jsonl` includes:

- `state_blob`: long context payload
- `state_blob_chars`: explicit payload size
- `must_preserve_keys`: key list that must remain stable across turns
- `preserve_key_values`: concrete values for machine-checkable memory constraints

## Contract Notes

- Existing verifier field names are preserved.
- Schema-backed tasks keep explicit `expected_schema` refs.
- No trigger names or protocol fields were renamed.

## Freeze Rule

After first full run with v2 starts, task rows are immutable. Any further change must create a new versioned file (for example, `e2_tasks_v3.jsonl`).
