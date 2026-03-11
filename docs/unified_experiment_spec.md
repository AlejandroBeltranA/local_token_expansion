# Unified LTE Experiment Spec

This is the maintained experiment definition for the unified LTE product. It stays anchored to the current `lte run` and `lte stress` surface rather than adding new runner infrastructure.

## Prompt families

- `budget_guardrails` in [suites/core_conciseness.yaml](../suites/core_conciseness.yaml)
  Detects over-expansion on short operational summaries and one paired handoff-delta task for verbosity drift.
- `structured_contracts` in [suites/structured_extraction.yaml](../suites/structured_extraction.yaml)
  Detects format instability and near-cap pressure on JSON, CSV, and exact line-oriented machine outputs.
- `context_pressure` in [suites/long_context_stability.yaml](../suites/long_context_stability.yaml)
  Detects context decay through stale-vs-latest instruction selection and multiple state-preservation tasks under noisy context.
- `failure_escalation` in [suites/persistent_failure_probe.yaml](../suites/persistent_failure_probe.yaml)
  Distinguishes repairable misses from outputs that should map to escalate or abort.

## Suite contents

- Benchmark battery: 14 cases across the four suites above.
- Stress battery: one rolling prompt defined in [configs/default.yaml](../configs/default.yaml) and [configs/stress_all_models.yaml](../configs/stress_all_models.yaml). It forces a stable, stateful output shape while the read-only reference grows.
- Per-case contracts are embedded in the suite YAML as metadata for the future unified runner. The current LTE runner ignores those keys safely.

## Trigger thresholds

These thresholds define the unified experiment contract even where the current runner only computes the raw metrics.

- `over_expansion`
  Fire if at least 2 benchmark cases tagged for budget control either hit `ER >= 1.25` or violate their strict shape contract by adding extra prose.
  Fire immediately if any benchmark case with `max_tokens <= 56` also hits `LORR = 1`.
- `latency_cliff`
  Fire on stress when `latency_ms > 2500` after `input_tokens >= 1500`.
  Escalate from warning to hard trigger if this happens on 2 of the last 3 stress steps.
- `near_cap_pressure`
  Fire if benchmark `LORR` mean across `structured_contracts` and `failure_escalation` is `>= 0.20`.
  Fire on stress if `LORR = 1` on any 2 steps within a 5-step window.
- `repetition_loop`
  Fire on stress if `RCS >= 0.30` on 2 consecutive steps.
  Also fire if the last 5 stress steps have mean `RCS >= 0.22`.
- `context_decay`
  Fire if 2 or more `context_pressure` cases fail their embedded invariants or stale/latest selection checks.
  Fire on stress if failure begins only after the reference history has grown past the latency gate and the dominant reasons are repetition or near-cap pressure.
- `persistent_failure`
  Fire when stress reaches 3 consecutive failed steps.
  Fire in benchmark review if both `failure_escalation` cases miss their format contract, because that indicates the model is not recovering even on tightly bounded outputs.

## Intervention mapping

- `continue`: no triggers fired
- `retry`: one isolated benchmark contract miss, with no stress trigger
- `repair`: structured-output failure without repetition or latency cliff
- `escalate`: `context_decay`, `repetition_loop`, or `latency_cliff` fired without persistent failure
- `abort`: `persistent_failure` fired, or 3 or more trigger families fired in one run

## Benchmark configs

- [configs/default.yaml](../configs/default.yaml)
  Maintained single-model local benchmark config. Also contains the canonical single-model stress settings so the same file can drive `lte run` and `lte stress`.
- [configs/unified_mock.yaml](../configs/unified_mock.yaml)
  Deterministic smoke config for the full benchmark plus stress path without MLX.

## Stress configs

- [configs/default.yaml](../configs/default.yaml)
  Canonical single-model stress config.
- [configs/stress_all_models.yaml](../configs/stress_all_models.yaml)
  Multi-model sweep config for wider local comparison after the single-model run is stable.
- [configs/unified_mock.yaml](../configs/unified_mock.yaml)
  Deterministic smoke config for the same stress contract.

## Unified run output contract

Current runner artifacts:

- benchmark rows: `results/run_<run_id>.jsonl`
- benchmark report: `reports/run_<run_id>/report.md`
- stress rows: `results/stress_<run_id>.jsonl`
- stress report: `reports/stress_<run_id>/report.md`

Logical unified contract for Agent 2:

- `benchmark_results`
  Per-prompt rows with prompt id, suite, raw generation, ER, LORR, RCS, and contract-check outcome.
- `stress_trace`
  Per-step rows with latency, ER, LORR, RCS, failure reasons, and consecutive-failure count.
- `trigger_summary`
  One row per trigger family with `status`, `threshold`, `evidence`, and `recommended_action`.
- `recommendation`
  One final action in `{continue,retry,repair,escalate,abort}` with a short rationale.

## Exact commands

Mock run:

```bash
lte run --config configs/unified_mock.yaml --run-id unified_mock_bench --force --progress
lte stress --config configs/unified_mock.yaml --run-id unified_mock_stress --force --progress
```

Real single-model run:

```bash
lte run --config configs/default.yaml --run-id unified_real_bench --progress
lte stress --config configs/default.yaml --run-id unified_real_stress --progress
```

Real multi-model stress sweep:

```bash
lte stress --config configs/stress_all_models.yaml --run-id unified_sweep_stress --progress
```
