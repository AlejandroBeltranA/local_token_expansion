# TASKS Freeze v1

- Freeze timestamp (UTC): `2026-02-25T11:29:20Z`
- Branch: `codex/drift-v0-agent-a-tasks`
- Scope: `research/drift_v0/tasks/`
- Status: Frozen for first full `drift_v0` run

## Files

- `e1_tasks_v1.jsonl`
- `e2_tasks_v1.jsonl`

## Composition

### E1 (`e1_tasks_v1.jsonl`)

- Total tasks: 40 single-turn
- `strict_json`: 16
- `instruction_compression`: 12
- `state_update` (single-turn variant): 12

### E2/E3 (`e2_tasks_v1.jsonl`)

- Total episodes: 20
- Turns per episode: 3
- Total task rows: 60
- `state_update` episodes: 10
- `strict_json` episodes: 6
- `instruction_compression` episodes: 4

## Verifier and Schema Contract Notes

- Every row declares `verifier`.
- Schema-backed rows declare `expected_schema` with refs from `schema_registry.json`.
- Constraint verifiers include explicit fields (`max_words`, `sentences`, `must_include`, state expectations).

## Freeze Rule

After first full run starts, these files are immutable. Any change must create versioned successors (for example, `e1_tasks_v2.jsonl` and `e2_tasks_v2.jsonl`).
