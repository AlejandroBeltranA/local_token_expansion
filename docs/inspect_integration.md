# Inspect Integration

This note describes how the [Inspect framework](https://inspect.aisi.org.uk/) could be used in this project without collapsing the existing local reliability harness into a full rewrite.

## Short Answer

Inspect is a good fit as an optional orchestration and logging layer.

It is not, at least initially, a good fit as a wholesale replacement for LTE.

## Why Inspect Is Relevant

The official Inspect documentation shows a few capabilities that map well onto this project:

- `Task` definitions over datasets and prompts
- custom `scorer` functions for non-trivial grading
- reusable evaluation logs written per run
- `inspect view` and related log analysis tooling
- `EarlyStopping` hooks that can skip or stop work once a condition is met
- tool-using agents and sandbox support for more complex evaluation flows

Sources:

- [Inspect tutorial](https://inspect.aisi.org.uk/tutorial.html)
- [Inspect tasks](https://inspect.aisi.org.uk/tasks.html)
- [Inspect scorers](https://inspect.aisi.org.uk/scorers.html)
- [Inspect early stopping](https://inspect.aisi.org.uk/early-stopping.html)
- [Inspect log files](https://inspect.aisi.org.uk/eval-logs.html)

## Where It Fits Best

### 1. Wrapping LTE suites as Inspect tasks

The existing `suites/*.yaml` definitions could be mapped into Inspect `Task` objects.

This would let LTE prompts run inside a more standard evaluation interface while preserving the current suite logic.

Good use cases:

- concise vs detailed paired prompts
- structured extraction tasks
- stateful reliability tasks from `drift_v0`

### 2. Implementing stop triggers with Inspect scorers

LTE’s degradation signals can be represented as Inspect scoring outputs.

Examples:

- expansion ratio threshold breach
- near-cap pressure
- repetition-loop detection
- invalid structured output
- state contradiction

This is attractive because Inspect’s scorer model matches the idea of "turn behavior -> explicit judgment -> logged artifact."

### 3. Using early stopping for persistent failure

Inspect’s `EarlyStopping` protocol is directly relevant to this project’s central question: when should the system stop because the model is no longer worth using?

A practical mapping would be:

- maintain per-sample or per-episode failure state,
- stop once N consecutive failures occur,
- record the reason and metadata in the eval log.

This matches LTE stress logic and could reduce wasted compute in larger sweeps.

### 4. Standardizing logs and analysis

Inspect writes structured eval logs and supports analysis over them.

This could help if you want:

- a standardized transcript/log format,
- easier human inspection of failure traces,
- compatibility with third-party analysis tooling built around Inspect logs.

## Where Inspect Is Not Enough By Itself

There are parts of the current project that Inspect does not replace cleanly:

- MLX-specific backend assumptions for local Apple Silicon runs
- the current LTE stress runner built around rolling context growth
- existing JSONL and report logic already tuned to your local workflow
- some of the custom failure metrics that are not ordinary "correct/incorrect" eval scores

So the migration risk is real: a rewrite around Inspect would likely slow the project before it improves it.

## Recommended Integration Strategy

### Phase 1: Add a compatibility spike

Create one small Inspect prototype that wraps a single LTE suite and one custom scorer.

Suggested target:

- suite: `suites/structured_extraction.yaml`
- custom scorer: invalid JSON / invalid table formatting

Goal:

- prove the task mapping,
- inspect the resulting logs,
- decide whether the logging/analysis value is worth the extra dependency.

### Phase 2: Port one stress-oriented task

Port one task where stop behavior matters.

Suggested target:

- a `drift_v0` short-horizon task or LTE stress case

Goal:

- implement custom failure scoring,
- implement early stopping for persistent failure,
- compare Inspect logs against current JSONL artifacts.

### Phase 3: Decide the long-term boundary

After two small integrations, decide whether Inspect should become:

- a supported optional backend,
- the default orchestration layer for some evals,
- or simply an experiment adapter for external interoperability.

## Concrete Recommendation

Use Inspect as:

- an optional task/scoring/logging layer,
- especially for experiments where transcript analysis and standard eval artifacts are valuable.

Do not use Inspect yet as:

- a forced replacement for LTE CLI,
- a reason to rewrite the MLX/stress stack,
- a dependency that blocks the core local reliability workflow.

## Immediate Next Step

If adopted, the first implementation should be a minimal `experiments/inspect/` prototype that:

- loads one LTE suite,
- runs one model,
- logs one custom reliability scorer,
- demonstrates one early stopping rule.

If that prototype is useful, it can be promoted into the main project. If not, the cost stays contained.
