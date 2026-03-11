# drift_v0 Agent Operating Protocol

This file turns the existing ownership split into an execution protocol that multiple agents can actually follow without drifting into duplicated work or incompatible outputs.

## Objective

Produce a publishable, reproducible `drift_v0` project package by splitting work across specialized agents while keeping interfaces stable enough for later synthesis.

Success condition:

- tasks are frozen and versioned,
- runtime emits stable evaluated JSONL artifacts,
- analysis consumes those artifacts without rewriting history,
- the orchestrator can merge outputs into one coherent public-facing project.

## Agent Set

### Orchestrator

Scope:

- define the current milestone,
- assign work packages,
- enforce boundaries and merge order,
- reject vague claims or incompatible outputs,
- decide when a rerun is required.

Inputs:

- repository state,
- milestone definition,
- all agent handoffs.

Outputs:

- milestone brief,
- task assignments,
- integration checklist,
- final synthesis note.

### Agent A: Tasks and Protocol Surface

Owns:

- `research/drift_v0/tasks/`
- task freeze docs,
- schema/task documentation that defines what the benchmark asks models to do.

Must deliver:

- versioned task packs,
- freeze note describing what changed and what stayed fixed,
- explicit assumptions and intended verifier behavior.

Must not:

- inspect new model outputs before freeze,
- change runtime logic,
- change analysis metrics.

### Agent B: Runtime, Verifiers, Interventions

Owns:

- `research/drift_v0/runner/`
- verifier and intervention behavior,
- execution infrastructure and artifact contracts.

Must deliver:

- deterministic runner changes,
- exact JSONL field contract,
- runnable commands for smoke tests and sweeps,
- clear notes on any new artifact fields.

Must not:

- change tasks/prompts,
- reinterpret metrics in prose,
- edit analysis criteria to compensate for runtime failures.

### Agent C: Analysis and Reporting

Owns:

- `research/drift_v0/analysis/`
- report-generation logic,
- paper-facing summary tables and plots.

Must deliver:

- metrics scripts that read evaluated logs only,
- failure-cause and summary outputs,
- documentation of what is measured vs inferred.

Must not:

- change runtime behavior,
- change tasks,
- quietly patch malformed inputs by editing source artifacts.

## Required Artifacts Per Agent

Every agent handoff must contain:

1. changed files,
2. files intentionally not changed,
3. assumptions,
4. exact validation commands,
5. a short risk note.

## Contract Between Agents

### A -> B contract

Agent A must supply:

- frozen task pack filenames,
- expected schemas/verifiers,
- version note when tasks change.

Agent B is allowed to assume:

- task semantics are frozen for the milestone,
- new task versions imply a new benchmark revision.

### B -> C contract

Agent B must supply:

- raw/evaluated JSONL field definitions,
- meaning of trigger flags,
- meaning of retry/escalation fields,
- any new metadata fields such as `max_tokens` or context labels.

Agent C is allowed to assume:

- evaluated logs are append-only,
- field names are stable within the milestone,
- missing values are meaningful and not accidental unless explicitly declared.

### C -> Orchestrator contract

Agent C must supply:

- metrics definitions,
- source artifact paths,
- distinction between measured results and interpretation,
- unresolved ambiguities that would block publication claims.

## Convergence Loop

Run this sequence for each milestone:

1. Orchestrator issues a milestone brief with one primary question.
2. Agent A freezes task/task-doc surface.
3. Agent B updates runtime and proves the artifact contract still holds.
4. Agent C updates analysis against evaluated artifacts only.
5. Orchestrator runs integration review.
6. If any interface changed, loop only the affected downstream agents.

## Merge Gate

The orchestrator does not approve convergence until all of the following are true:

- no agent edited another agent's owned directory,
- trigger names remain stable unless explicitly re-registered,
- task versions are explicit,
- runtime outputs can be generated from repo-local commands,
- analysis can be regenerated from repo-local artifacts,
- README/docs match what the code actually does.

## Failure Modes To Watch

- Agent A adds tasks after looking at outputs.
- Agent B changes field names without telling Agent C.
- Agent C bakes one-off local paths into reports.
- The orchestrator summarizes results that are not reproducible from checked-in commands.

If any of these happen, the milestone is not coherent and should not be treated as publication-ready.
