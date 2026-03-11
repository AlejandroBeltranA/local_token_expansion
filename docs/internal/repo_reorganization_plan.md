# Repo Reorganization Plan

## Goal

Restructure the repository so the public-facing project reads as one coherent product:

> a local-first reliability and intervention pipeline for detecting when LLM-based systems stop being worth using in downstream workflows.

The reorganization should make that story obvious from the top level without deleting the research history that led to it.

## Guiding Rule

The repo should optimize for first impressions, reproducibility, and conceptual coherence.

That means:

- the maintained product surface should be small and obvious,
- research history should remain accessible but should not compete with the main story,
- the README should match the file tree,
- a new user should know where to start in under a minute.

## Proposed Top-Level Shape

### First-Class Public Surface

These directories and files should represent the main product:

- `lte/`
- `configs/`
- `suites/`
- `docs/`
- `examples/`
- `tests/`
- `pyproject.toml`
- `README.md`

This is the maintained runtime, evaluation, stress-testing, and reporting surface.

### Archived or Secondary Research Surface

These should remain public but should stop competing with the product surface:

- `research/propensity/run_propensity.py`
- `research/propensity/analysis.ipynb`
- `research/propensity/outputs/`
- `research/drift_v0/`
- `research/papers/drift_v0/`

They are useful, but they are not the shortest path to understanding the product.

## Recommended Structural Change

Introduce a `research/` or `legacy/` area and move older exploratory material there.

Preferred structure:

- `research/propensity/`
  - old long-horizon novelty/usefulness experiments
- `research/drift_v0/`
  - accountability and intervention-focused research track
- `research/papers/drift_v0/`
  - paper assets and figure-generation scripts

This keeps the work public while making its status explicit.

## What Stays First-Class

### 1. LTE runner and reporting

Keep:

- `lte/cli.py`
- `lte/stress.py`
- `lte/reporting.py`
- `lte/metrics.py`
- `lte/config.py`
- `lte/backends/`

Reason:

This is the cleanest expression of the product.

### 2. Benchmark and stress configs

Keep:

- `configs/default.yaml`
- `configs/stress_all_models.yaml`

Reason:

They define the primary supported workflows.

### 3. Suites

Keep:

- `suites/core_conciseness.yaml`
- `suites/structured_extraction.yaml`
- `suites/long_context_stability.yaml`

Reason:

They form the maintained benchmark surface and can expand over time.

### 4. Docs

Keep and strengthen:

- `docs/methodology.md`
- `docs/product_direction.md`
- `docs/inspect_integration.md`

Add later if needed:

- `docs/trigger_taxonomy.md`
- `docs/intervention_policy.md`

Reason:

The product is as much about operational framing as it is about code.

## What Gets Demoted

### 1. Propensity experiments

Move to:

- `research/propensity/`

Includes:

- `research/propensity/run_propensity.py`
- `research/propensity/run_all_models.py`
- `research/propensity/local_llm_propensity.json`
- `research/propensity/analysis.ipynb`
- `research/propensity/outputs/*`
- `research/propensity/prompt_summary.md`

Reason:

This work contributed important ideas, but it is exploratory and should not define the public product surface.

### 2. drift_v0 research track

Move to:

- `research/drift_v0/`

Includes:

- all of `research/drift_v0/`

Reason:

This track is valuable, especially for intervention and accountability framing, but it currently reads as a parallel product.

### 3. Paper assets

Move to:

- `research/papers/drift_v0/`

Includes:

- `research/papers/drift_v0/`

Reason:

Paper artifacts should not live where product users expect stable runtime assets.

## What Needs Integration Instead of Movement

Some concepts should be absorbed into LTE rather than left isolated in research folders.

### From propensity work

Promote into maintained product:

- novelty collapse as a formal degradation signal,
- usefulness decay over repeated steps,
- repeated-answer / already-answered behavior as a trigger candidate.

### From drift_v0

Promote into maintained product:

- explicit intervention states,
- retry / escalate / abort logic,
- clearer trigger definitions for operational stop conditions,
- stronger schema/stateful tasks.

## Proposed Milestones

### Milestone 1: Clarify status in place

Completed.

Actions taken:

- add status labels in README and docs,
- state which areas are maintained and which are research tracks,
- add links from product docs into research docs where relevant.

This established the public boundary before structural moves.

### Milestone 2: Restructure directories

Completed.

Actions taken:

- propensity materials into `research/propensity/`
- `drift_v0` into `research/drift_v0/`
- paper assets into `research/papers/drift_v0/`

Follow-up work:

- imports,
- scripts,
- docs,
- artifact-generation paths.

### Milestone 3: Promote reusable concepts

Implement inside LTE:

- richer trigger taxonomy,
- intervention policy hooks,
- optional stateful and repair-oriented suites.

At this point the repo stops reading as "benchmark plus old experiments" and starts reading as one product with research appendices.

## Recommended Branch Split

Use the integration branch as the coordinator branch and make the reorg explicit.

Suggested branches:

- `codex/repo-product-surface`
  - README, docs, naming, top-level structure decisions
- `codex/repo-runtime-integration`
  - LTE promotion of selected triggers/intervention hooks
- `codex/repo-research-archive`
  - moving exploratory materials under `research/`
- `codex/repo-inspect-spike`
  - minimal Inspect prototype

This is cleaner than trying to spread one giant reorganization across the existing `drift_v0` agent branches.

## Inspect Prototype Plan

The Inspect integration should begin as a contained experiment, not a rewrite.

### Directory

Create:

- `experiments/inspect/`

Initial contents:

- `README.md`
- `structured_extraction_eval.py`
- `scorers.py`
- `datasets/structured_extraction.jsonl` or adapter logic from `suites/structured_extraction.yaml`

### Prototype Objective

Demonstrate that Inspect can represent one LTE evaluation end to end:

- one task,
- one model,
- one custom reliability scorer,
- one early stopping rule,
- one Inspect log artifact.

### Recommended First Target

Use `structured_extraction` first.

Reason:

- task definitions are simple,
- scoring criteria are explicit,
- failure is easy to interpret,
- it does not require the full rolling-context machinery immediately.

### Custom Scorers For The Prototype

Start with:

- `valid_json_only`
- `output_near_cap`
- `latency_threshold`

Then optionally add:

- `expansion_ratio_breach`

### Early Stopping Prototype

Implement one simple policy:

- stop after `N` consecutive failures on parseability or near-cap pressure.

This is enough to test whether Inspect’s early-stopping model is useful for the project’s stop-trigger goals.

### Success Criteria

The Inspect spike is successful if it proves all of the following:

- task mapping is straightforward,
- custom scorers can express LTE-style reliability triggers,
- logs are useful enough to justify the extra dependency,
- early stopping works for persistent failure conditions.

If it does not prove those points, it should remain an experiment and not influence the main architecture.

## Naming Recommendation

There is still a naming mismatch.

`Local Token Expansion` is historically accurate but product-incomplete.

Short term:

- keep the LTE acronym,
- redefine it in docs as the broader reliability and intervention harness.

Longer term:

- consider a rename only after the repo structure is coherent.

Do not rename the project before the file tree and README stop sending mixed signals.

## Immediate Next Actions

1. Add status labels to research areas in the README.
2. Decide whether the archive container should be `research/` or `legacy/`.
3. Create the `experiments/inspect/` spike rather than debating Inspect abstractly.
4. After that, do the directory moves in one controlled reorganization pass.
