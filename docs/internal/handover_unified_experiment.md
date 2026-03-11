# Handover: Unified Reliability Experiment

## Why This Exists

This handover is for the next agent because the work drifted into side-track cleanup and `drift_v0` infrastructure instead of staying centered on the actual product defined in [docs/product_direction.md](../product_direction.md).

The next agent should ignore that drift and build the correct thing.

## Actual Goal

Build one end-to-end LTE-centered experiment that:

- runs a defined prompt battery,
- stress tests local models systematically,
- measures failure systematically,
- and emits clear stop / escalate signals.

The product is a unified reliability gate with three layers:

1. measurement
2. stress
3. intervention

Do not recentre the work on `research/drift_v0/`. That track is supporting research, not the product.

## Core Question

When does a local model become unreliable enough that another system should stop trusting it?

## Required Experiment Shape

### 1. Prompt Battery

Define and/or refine suites that directly probe:

- over-expansion
- structured output adherence
- instruction-following under tight constraints
- state carryover / context decay
- long-context usefulness

The prompt set should not be ad hoc. It should be explicitly versioned and easy to rerun.

### 2. Stress Protocol

Use LTE stress mode or extend it so it measures:

- latency cliff
- repetition loop
- near-cap pressure
- context decay
- persistent failure

### 3. Unified Trigger System

The experiment must surface these triggers in one place:

- `over_expansion`
- `latency_cliff`
- `near_cap_pressure`
- `repetition_loop`
- `context_decay`
- `persistent_failure`

### 4. Unified Output

One experiment run should produce:

- per-prompt benchmark results,
- per-model stress traces,
- a consolidated model summary,
- explicit intervention recommendations:
  - `continue`
  - `retry`
  - `repair`
  - `escalate`
  - `abort`

## What Was Already Done

Useful work that should be reused:

- [docs/product_direction.md](../product_direction.md)
- top-level [README.md](../README.md) was reframed around the unified product
- repo structure now separates research under [research/](../research/)
- LTE remains the maintained runtime surface under [lte/](../lte/)
- mock-tested drift weekend runner exists, but it is not the correct center of gravity for the product

Relevant current code:

- [lte/cli.py](../lte/cli.py)
- [lte/stress.py](../lte/stress.py)
- [lte/reporting.py](../lte/reporting.py)
- [configs/default.yaml](../configs/default.yaml)
- [configs/stress_all_models.yaml](../configs/stress_all_models.yaml)
- [suites/](../suites/)

## What Was A Mistake

Do not spend the next turn:

- polishing `research/drift_v0/` as if it were the product
- building more paper-oriented infrastructure first
- debating Inspect integration
- doing more repo-surface cleanup unless it directly unblocks the unified experiment

## Recommended Split: Two Agents

Yes, split this into two agents.

### Agent 1: Experiment Design

Owns:

- suites
- configs
- trigger definitions
- output contract for the unified run

Deliverables:

1. a concrete prompt battery
2. a trigger spec with thresholds
3. benchmark + stress config set for the unified experiment
4. a short doc describing the experiment contract

Files likely involved:

- [suites/](../suites/)
- [configs/](../configs/)
- new docs under [docs/](..)

### Agent 2: Unified Runner

Owns:

- the end-to-end execution path
- aggregation
- consolidated reporting
- mock and real run entrypoints

Deliverables:

1. one runner command that executes benchmark + stress together
2. one merged artifact set per run
3. one consolidated report over measurement + stress + intervention
4. tests for the mock end-to-end path

Files likely involved:

- [lte/](../lte/)
- [scripts/](../scripts/)
- [tests/](../tests/)

## Suggested Agent Prompts

### Prompt for Agent 1

Build the unified LTE experiment spec described in [docs/product_direction.md](../product_direction.md).

Your job is to define:

- the prompt families,
- the suites,
- the trigger taxonomy as executable thresholds,
- and the config files for the end-to-end run.

Focus on the product, not the research archive. Do not work in `research/` unless you are borrowing ideas.

Deliver:

1. new or updated suite files
2. new or updated config files
3. one short experiment-spec doc
4. exact commands for a mock run and a real run

### Prompt for Agent 2

Build the unified LTE runner described in [docs/product_direction.md](../product_direction.md).

Your job is to implement one end-to-end command that:

- runs the benchmark prompt battery,
- runs stress tests,
- aggregates the outputs,
- computes the trigger summary,
- and writes one consolidated report.

Do not re-center on `research/drift_v0/`. Reuse only what is necessary.

Deliver:

1. one runner entrypoint
2. one merged output directory structure
3. one consolidated report
4. tests for the mock end-to-end path

## Immediate Build Order

1. Agent 1 defines the experiment and configs.
2. Agent 2 implements the unified runner against that contract.
3. Run the full mock path.
4. Run one real local model.
5. Only then widen to multiple models / weekend sweep.

## Definition Of Done

The work is done when a user can run one command and get:

- benchmark results,
- stress results,
- trigger-based failure summaries,
- and an explicit recommendation about whether the model remained worth using.
