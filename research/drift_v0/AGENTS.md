# AGENTS Instructions for `research/drift_v0`

These instructions apply to all files under `research/drift_v0/`.

## Mission

Build a reproducible `drift_v0` experiment track with strict contamination control across 3 agents:

- Agent A: tasks
- Agent B: runtime/verifiers/interventions
- Agent C: analysis/reporting

## Branch Model (Required)

- Base branch: `codex/drift-v0`
- Agent branches:
  - `codex/drift-v0-agent-a-tasks`
  - `codex/drift-v0-agent-b-runner`
  - `codex/drift-v0-agent-c-analysis`

Do not work directly on `codex/drift-v0` from agent threads. Open PRs into `codex/drift-v0`.

## Ownership Boundaries (Required)

- Agent A may edit only:
  - `research/drift_v0/tasks/`
  - docs that describe task definitions
- Agent B may edit only:
  - `research/drift_v0/runner/`
  - docs that describe runtime/verifier behavior
- Agent C may edit only:
  - `research/drift_v0/analysis/`
  - docs that describe metrics/plots/reporting

Agents must not edit folders owned by other agents.

## Contamination Controls (Required)

- Agent A must not inspect model outputs before tasks are frozen.
- Agent B must not author or modify prompts/tasks.
- Agent C must not modify tasks or verifier logic.
- After freeze, any task change requires a new versioned task file.

## Merge Order (Required)

1. Agent A PR merged first (task freeze).
2. Agent B PR merged second (runtime + trigger flags + interventions).
3. Agent C PR merged third (metrics and summaries over evaluated logs).

## Pre-registered Triggers (Do Not Change Without Approval)

- `schema_failure`
- `repetition_loop`
- `state_contradiction`

Intervention policy remains two-step:
1) one trigger-specific recovery attempt, then
2) reset/escalate if unresolved.

## Quality Bar

- Keep changes minimal and focused.
- Preserve JSONL contracts and field names in `protocol_v0.md`.
- Add or update concise docs when behavior changes.
- Do not add unrelated dependencies.

## Required Handoff in Every PR

- What was changed.
- What was intentionally not changed.
- Any assumptions made.
- Exact command(s) used for local validation.

## Orchestrator Merge Checklist (A -> B -> C)

1. Scope check
- PR edits only allowed folders per this file.
- No cross-agent contamination.

2. Contract check
- Fields in `protocol_v0.md` are preserved (no silent renames).
- Trigger names unchanged:
  - `schema_failure`
  - `repetition_loop`
  - `state_contradiction`

3. Validation check
- PR includes exact local commands and a concise output summary.
- Commands are runnable on a MacBook without heavy new dependencies.

4. Quality check
- Diff is minimal and focused.
- Docs are updated where behavior changed.
- No unrelated refactors.

5. Order gate
- Merge Agent A only after task freeze is explicit.
- Merge Agent B only after confirming no task edits.
- Merge Agent C only after B output format is stable.

6. Integration smoke test after each merge
- After A: task files parse and are versioned/frozen.
- After B: evaluator runs on sample/raw events.
- After C: summary runs on evaluated events and emits expected metrics.

## PR Review Template

Use this checklist in each PR review:

- [ ] Scope: changes are limited to allowed directories.
- [ ] Scope: no contamination boundary violations.
- [ ] Protocol: `protocol_v0.md` logging fields preserved.
- [ ] Protocol: trigger names unchanged.
- [ ] Protocol: intervention policy remains two-step.
- [ ] Implementation: diff is minimal and focused.
- [ ] Implementation: no unrelated refactors/heavy deps.
- [ ] Documentation: updated where interfaces changed.
- [ ] Validation: exact commands are provided and reproducible.
- [ ] Validation: output format/metrics match expected contracts.
- [ ] Handoff includes changed files, assumptions, and validation notes.

Suggested approval comment:
"Approved. Scope and protocol checks pass, local validation is reproducible, and outputs match drift_v0 contracts."

Suggested changes-requested comment:
"Changes requested: scope/protocol mismatch found. Align with AGENTS boundaries and protocol_v0 field/trigger contracts, then re-run validation and post command/output summary."
