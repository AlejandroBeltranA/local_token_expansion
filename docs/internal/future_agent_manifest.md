# Future Agent Manifest

## What This Project Is

This repo is building an empirical accountability scaffold for language-model intervention.

The central question is:

- which observable model behaviors justify `retry`, `repair`, `escalate`, or `abort` in a workflow?

This is not a generic capability benchmark project and it is not a model leaderboard project.

Local models are the current experimental substrate because they are cheap and fast to iterate on. The next intended step is to plug API-based models into the same scaffold without changing the accountability logic.

## What Was Built

### 1. Unified intervention-centered experiment

The maintained experiment lives in:

- [suites/](../suites/)
- [configs/](../configs/)
- [lte/unified.py](../lte/unified.py)
- [lte/contracts.py](../lte/contracts.py)

The experiment now uses:

- bounded-output probes
- structured-output probes
- state-integrity probes
- a rolling stress probe

These are intervention probes, not broad benchmark tasks.

### 2. Trigger families and intervention mapping

The maintained trigger families are:

- `over_expansion`
- `near_cap_pressure`
- `context_decay`
- `latency_cliff`
- `persistent_failure`

The maintained intervention states are:

- `continue`
- `retry`
- `repair`
- `escalate`
- `abort`

The current experiment explicitly distinguishes:

- recoverable failures
- unrecoverable failures

That distinction now flows through suite metadata, contract evaluation, unified summaries, and weekend sweep artifacts.

### 3. Tuned probe battery

The battery was tuned after inspecting actual outputs from multiple local models.

Weak or generic prompts were replaced with more intervention-relevant probes:

- release-summary prompts were replaced by handoff-delta prompts
- the generic checklist prompt was replaced by exact line-oriented action extraction
- the weak compression prompt was replaced by ledger carry-forward JSON
- the rolling stress prompt was made more stateful

The goal of these changes was to make the experiment more informative for a paper about intervention legitimacy, not to maximize model separation for its own sake.

### 4. Weekend sweep scaffold

The maintained sweep runner is:

- [scripts/run_unified_weekend.py](../scripts/run_unified_weekend.py)

It now:

- runs the unified scaffold over all configured models by default
- writes per-run checkpoint JSON
- writes `progress.json` with ETA and current run state
- groups aggregate results by intervention regime
- preserves recoverable vs unrecoverable failure counts

This scaffold is intended for repeated empirical sweeps, not one-off demos.

## Why It Was Built This Way

The experiment was reshaped around the paper’s accountability argument:

- we do not primarily care which model is “best”
- we care which behaviors justify intervention
- we care whether those behaviors can be detected cheaply and repeatably
- we care whether intervention regimes are stable across seeds and modest parameter changes

The current design reflects that:

- benchmark probes expose bounded-output, structured-output, and state-integrity failures
- stress exposes operational breakdown under growing context
- trigger summaries convert measured behavior into intervention decisions

## Current Empirical Result

The completed weekend sweep under:

- [results/weekend_sweep_full/report.md](../results/weekend_sweep_full/report.md)
- [results/weekend_sweep_full/baseline_phase_summary.json](../results/weekend_sweep_full/baseline_phase_summary.json)

showed stable intervention regimes across all tested local models.

Observed regime split:

- `escalate`: Phi-4-mini-instruct-8bit, Meta-Llama-3.1-8B-Instruct-3bit
- `abort`: Mistral-7B-Instruct-v0.3, Phi-3-mini-4k-instruct-4bit, SmolLM-1.7B-Instruct-4bit

This result is important because it shows stable behavioral pathways to intervention, not just raw model differences.

## Files Future Agents Should Read First

Start here:

- [docs/product_direction.md](../product_direction.md)
- [docs/handover_unified_experiment.md](handover_unified_experiment.md)
- [docs/unified_experiment_spec.md](../unified_experiment_spec.md)
- [docs/paper_accountability_scaffold.md](../paper_accountability_scaffold.md)
- [docs/probe_intervention_table.md](../probe_intervention_table.md)
- [docs/paper_intro_results_draft.md](../paper_intro_results_draft.md)
- [docs/paper_methods_draft.md](../paper_methods_draft.md)
- [docs/paper_discussion_limitations_draft.md](../paper_discussion_limitations_draft.md)
- [docs/paper_results_draft.md](../paper_results_draft.md)

Then inspect:

- [lte/unified.py](../lte/unified.py)
- [lte/contracts.py](../lte/contracts.py)
- [scripts/run_unified_weekend.py](../scripts/run_unified_weekend.py)

## What Not To Re-Center On

Do not re-center the project on:

- general model performance benchmarking
- leaderboard-style reporting
- the older `research/propensity` pipeline as the main product
- the older `research/drift_v0` runner as the main product

Those tracks can still provide ideas, but the maintained center of gravity is now the unified accountability scaffold.

## Safe Next Steps

Reasonable next steps include:

- running the same scaffold on API-based models
- calibrating trigger thresholds against human judgments
- improving result presentation and paper assets
- adding a small number of domain-specific intervention probes without breaking the scaffold

Unhelpful next steps include:

- adding many new benchmark tasks without intervention rationale
- broadening the scope back into generic eval infrastructure
- changing the accountability framing back into capability ranking
