# drift_v0 Project Summary

## 1) What this project is trying to achieve

`drift_v0` evaluates **operational reliability** of local LLMs in a deployment-like setting.  
The goal is not task intelligence alone, but whether a model stays **machine-actionable** under stress:

- schema/format adherence,
- short-horizon state consistency,
- non-repetitive behavior,
- intervention recoverability.

The accountability framing is: when failures are detected, the system should produce auditable intervention signals (`retry`, `reset`, `escalate`) that can be assigned to clear ownership in deployment workflows.

## 2) How we built it

We implemented a reproducible pipeline with three stages:

1. **Raw generation** (`runner/run_experiments.py`)
   - Runs task packs against local MLX models.
   - Supports `E1`, `E2`, `E3` and closed-loop intervention execution.

2. **Evaluation** (`runner/evaluate_events.py`)
   - Applies trigger checks:
     - `schema_failure`
     - `repetition_loop`
     - `state_contradiction`
   - Emits intervention outputs:
     - retry once
     - then reset/escalate if unresolved.

3. **Analysis** (`analysis/summarize.py`)
   - Produces paper-ready markdown tables and machine-readable artifacts.
   - Reports failure rates, first-failure turn, retry effectiveness, escalation rates, and E3 deltas.

We then added an overnight sweep runner (`runner/run_sweep.py`) to evaluate model/config grids automatically.

## 3) Experimental setup used in this run

- Models: 5 local MLX models
  - Meta-Llama-3.1-8B-Instruct-3bit
  - Mistral-7B-Instruct-v0.3
  - Phi-3-mini-4k-instruct-4bit
  - Phi-4-mini-instruct-8bit
  - SmolLM-1.7B-Instruct-4bit
- Config grid:
  - temperature: `0.0, 0.2, 0.6`
  - top_p: `0.8, 0.95, 1.0`
- Total conditions: `45` (5 x 3 x 3)
- Task packs:
  - `E1`: single-turn contract tasks
  - `E2`: 3-turn carried-state tasks
  - `E3`: E2 tasks under `1k` and `4k` context-budget arms

## 4) What we found

### 4.1 High failure regime, with meaningful model-family differences

Across all 45 conditions:

- `E1` failure rates ranged: `0.8889` to `1.0`
- `E2` failure rates ranged: `0.9` to `1.0`
- `E3` failure rates ranged: `0.925` to `1.0`

Within-model decoding variation was limited in this setup; model family accounted for more spread than temperature/top_p.

### 4.2 Best observed operating region

The strongest conditions were consistently `Mistral-7B-Instruct-v0.3`, with identical top-ranked scores across all tested temperature/top_p settings:

- `E1=0.8889`, `E2=0.925`, `E3=0.925` (composite score `0.9106`).

### 4.3 Intervention policy detected failures but did not recover them

- Retry effectiveness remained `0.0` in the sweep outputs.
- Escalation-after-retry was effectively `1.0` where retries were attempted.

This indicates the current retry prompts function more as a detection/escalation gate than a true recovery mechanism.

### 4.4 Failure-taxonomy insight from post-hoc log inspection

Post-hoc breakdown on `E2/E3` primary turns showed:

- dominant failures were **near token-cap outputs** and **non-extractable schema failures**,
- repetition-only failures were rare.

Model-specific contrast:

- **Mistral**: lower fail rate than peers and a much higher fraction of extractable JSON among failures.
- Several other models failed with mostly non-extractable outputs under the same tasks.

This suggests many failures are contractability under constrained output budget, not only memory retention.

## 5) Interpretation

This run provides useful evidence, but it primarily reflects:

- model differences in strict contract adherence,
- prompt-contract rigidity under short-horizon stateful tasks,
- limited recovery from first-order intervention prompts.

It is less sensitive (in current design) to:

- temperature/top_p effects within a model,
- clean separation between `E2` and `E3` context-pressure regimes.

## 6) Limitations

- Validator strictness penalizes wrappers/prose around otherwise valid payloads.
- `max_tokens=256` likely amplifies truncation/format failures in state-heavy prompts.
- `E3` pressure did not consistently produce large deltas from `E2`.

## 7) Practical value of this run

The run is still high-value and reusable:

- establishes a reproducible benchmark + sweep harness,
- identifies best/worst model families for this contract profile,
- provides a failure taxonomy for accountability-oriented deployment decisions,
- yields auditable intervention traces suitable for policy/reporting framing.

## 8) Recommended next iteration

1. Split hard vs soft failures in official metrics (wrapper-tolerant extraction path).  
2. Add a stronger recovery baseline (e.g., deterministic repair step or second-pass repair model).  
3. Recalibrate prompt contracts to avoid complete ceiling effects while preserving strictness.  
4. Re-run a smaller targeted grid around top models to isolate E3 sensitivity.

## 9) Key artifacts from this sweep

- Sweep manifest: `/tmp/drift_v0_sweep/sweep_manifest.csv`
- Per-condition reports: `/tmp/drift_v0_sweep/<condition_id>/report/`
- Post-hoc failure cause tables:
  - `/tmp/drift_v0_failure_cause_by_model.csv`
  - `/tmp/drift_v0_failure_cause_overall.csv`
