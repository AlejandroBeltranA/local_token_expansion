# Task Blueprint (Shared Context)

This file defines what Agent A should generate and what Agent B/C should assume.

## Purpose by Experiment

- `E1` (single-turn baseline): isolate intrinsic reliability under strict output constraints.
- `E2` (3-turn carried state): detect early trajectory breakage with minimal horizon.
- `E3` (context pressure): rerun E2 tasks at `1k` and `4k` context budgets.

## Task Families

Use a balanced mix so failures are not prompt-family artifacts.

1. `strict_json`
- Prompt requests JSON only.
- Verifier: `schema_json`.
- Primary trigger exposure: `schema_failure`.

2. `instruction_compression`
- Prompt asks concise, constrained output (single sentence, max words).
- Verifier: `length_and_sentence_count`.
- Primary trigger exposure: `repetition_loop` and instruction drift.

3. `state_update`
- Multi-turn state mutation with arithmetic or ledger-style updates.
- Verifier: `state_consistency`.
- Primary trigger exposure: `state_contradiction`.

## Composition Targets

- E1 (40 tasks)
  - 16 `strict_json`
  - 12 `instruction_compression`
  - 12 `state_update` (single-turn variant)

- E2/E3 (20 episodes, 3 turns each)
  - 10 `state_update`
  - 6 `strict_json` with evolving constraints
  - 4 `instruction_compression` with carryover memory

## Prompt Authoring Rules

- Keep domain-neutral and policy-safe.
- Avoid niche knowledge dependencies.
- Keep required outputs deterministic and machine-checkable.
- Each task must declare:
  - `verifier`
  - `expected_schema` (when applicable)
  - explicit limits (`max_words`, `sentences`, etc.) where relevant.

## Freeze Rule

After first full run starts, task packs are frozen. Any change requires a new versioned file:
- `e1_tasks_v2.jsonl`
- `e2_tasks_v2.jsonl`
