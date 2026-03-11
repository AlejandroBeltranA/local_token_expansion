# Product Direction

## Public Product Statement

This project is a local-first reliability and intervention pipeline for LLM-based systems. Its purpose is to detect when a model is no longer operationally useful in an automated workflow and to emit explicit signals that tell a downstream system whether it should continue, retry, repair, escalate, or stop.

The central problem is not only whether a model can answer a task once, but whether it remains worth using over time on local hardware under realistic constraints such as bounded context windows, latency pressure, and output-budget limits. The project therefore treats failure as an operational state, not only a task-quality judgment.

## Core Question

When does a local model become unreliable enough that another system should stop trusting it?

## First-Class Outcomes

The maintained public surface should support:

- repeatable local evaluation runs,
- explicit trigger detection for operational degradation,
- report generation over those triggers,
- intervention recommendations that a downstream system can consume.

## Product Scope

The first-class product is a unified reliability gate with three layers:

1. Measurement
   Detect changes in output length, latency, repetition, and task adherence.

2. Stress
   Probe how those failures emerge as context and interaction history grow.

3. Intervention
   Convert observed failures into machine-actionable decisions such as retry, escalate, or abort.

## Trigger Taxonomy

These triggers define when the system should consider a model run operationally degraded.

### 1. Over-Expansion

Definition:
Output length grows beyond what the task reasonably requires.

Examples:

- high expansion ratio relative to prompt size,
- large concise-vs-detailed drift when the task did not justify it,
- repeated long-form continuations on tightly constrained prompts.

Why it matters:
Over-expansion wastes budget, increases latency, and often precedes truncation or low-signal output.

### 2. Latency Cliff

Definition:
Response latency rises beyond a usable threshold, especially once the context window is busy.

Examples:

- latency exceeding a configured threshold,
- repeated slow responses after context growth,
- step-to-step latency spikes under otherwise stable settings.

Why it matters:
A downstream system may prefer a weaker but bounded model over an accurate but unusably slow one.

### 3. Near-Cap Pressure

Definition:
The model repeatedly pushes against `max_tokens` or other output-budget limits.

Examples:

- length overrun rate near 1,
- high fraction of outputs landing at or near generation cap,
- truncation-like behavior where formatting breaks at the tail.

Why it matters:
Near-cap outputs are often the point where parseability and usefulness collapse.

### 4. Repetition Loop

Definition:
The model begins recycling phrases, structures, or whole prior answers instead of producing useful new work.

Examples:

- high n-gram repetition,
- high overlap with prior step output,
- repeated sentence templates under rolling context.

Why it matters:
This is often the clearest signal that the model is no longer adding value.

### 5. Context Decay

Definition:
Additional context stops improving performance and instead degrades adherence, novelty, or consistency.

Examples:

- state-carrying tasks fail more often as history grows,
- relevant prior information is ignored or contradicted,
- reference text is copied instead of used.

Why it matters:
The nominal context window is not the same thing as useful context capacity.

### 6. Persistent Failure

Definition:
The system observes multiple consecutive failed steps and treats the run as operationally unusable.

Examples:

- N consecutive failure steps in stress mode,
- repeated retry failure with no recovery,
- continuing degradation after one repair attempt.

Why it matters:
One bad step may be noise. Persistent failure is the threshold for stop or escalation.

## Intervention States

The system should map trigger observations to a small set of downstream actions:

- `continue`: no meaningful degradation detected
- `retry`: failure may be recoverable with one constrained retry
- `repair`: attempt a deterministic or schema-constrained correction step
- `escalate`: hand off to a human or higher-assurance subsystem
- `abort`: terminate the run because continued use is not justified

## How Existing Work Fits

### LTE

Role:
Primary maintained harness.

Contribution:

- benchmark runner,
- suite execution,
- token/latency/repetition metrics,
- stress testing,
- report generation.

### Propensity experiments

Role:
Exploratory precursor, not the public center of gravity.

Contribution:

- novelty collapse framing,
- repeated-answer and usefulness-decay ideas,
- longer-horizon degradation intuition.

Public status:
Either archive as legacy research or absorb only the reusable concepts.

### drift_v0

Role:
Intervention and accountability layer.

Contribution:

- explicit trigger flags,
- retry/reset/escalation logic,
- operational reporting over failure states,
- stronger bridge to governance and responsibility framing.

Public status:
Keep if integrated into the unified product story; otherwise mark as a research track.

## Proposed Repo Architecture

The repo should present one main product and demote exploratory history.

Suggested structure:

- `lte/`
  - maintained runtime, metrics, stress, intervention logic
- `configs/`
  - maintained benchmark and stress configs
- `suites/`
  - maintained task suites
- `docs/`
  - `methodology.md`
  - `product_direction.md`
  - `trigger_taxonomy.md` or equivalent
  - `intervention_policy.md`
- `examples/`
  - small reproducible sample runs and reports
- `research/` or `legacy/`
  - older exploratory experiments
  - paper drafts and notebooks not needed for the product surface

## Naming Implication

`Local Token Expansion` is too narrow if the public product is really a reliability gate. Token expansion is one trigger, not the full mission.

If the project remains under the LTE name, the docs should explicitly redefine LTE as a broader local reliability framework rather than a single-metric benchmark.

If renamed, the new name should reflect:

- local execution,
- reliability degradation,
- stop or escalation logic,
- operational use in downstream systems.

## Decision Criteria For Public Release

The repo is coherent enough to publish when:

- the README describes one product, not several unrelated experiments,
- examples demonstrate real trigger behavior cleanly,
- intervention states are documented and tied to measurable conditions,
- legacy work is either integrated or clearly archived,
- a local user can run tests and a mock end-to-end pipeline without guessing.
