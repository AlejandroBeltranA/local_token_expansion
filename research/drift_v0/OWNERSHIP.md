# Ownership and Contamination Controls

## Owners

- Agent A (`task_pack`): `research/drift_v0/tasks/`
- Agent B (`runtime+verifiers`): `research/drift_v0/runner/`
- Agent C (`analysis`): `research/drift_v0/analysis/`

## Hard Boundaries

- Agent A does not inspect model outputs before task freeze.
- Agent B does not edit prompts/tasks.
- Agent C does not edit tasks or verifier logic.

## Freeze Rule

- Freeze all `tasks/*.jsonl` before full runs.
- Any post-freeze change requires a new version file (for example, `e2_tasks_v2.jsonl`).

## Reproducibility Rules

- Keep raw logs append-only in `data/raw/` (outside this folder if preferred).
- Store run metadata: model, quantization, seed, temperature, max tokens, context limit.
- Analysis reads evaluated logs only; it must not mutate raw logs.

## Review Rule

- Cross-review at least once per PR:
  - A reviews B or C for boundary checks.
  - B reviews A or C for schema/instrumentation checks.
  - C reviews A or B for metric-consistency checks.
