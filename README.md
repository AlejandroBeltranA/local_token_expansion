# Local Token Expansion (LTE)

Local Token Expansion (LTE) is a local-first evaluation harness for measuring when LLMs stop being operationally useful under workflow pressure.

Most LLM benchmarks ask whether a model can complete a task. LTE asks a different question: when does the model stop being useful inside a constrained workflow? It measures output expansion, cap pressure, verbosity drift, repetition, context stress, latency cliffs, and persistent failure states, then maps those signals to intervention decisions: `continue`, `retry`, `repair`, `escalate`, or `abort`.

This repository is not a general model leaderboard. It is a harness for producing deployment-relevant signals from local model runs.

## Why This Matters

LLM workflows often fail before they become obviously wrong. A model can remain fluent while drifting out of contract, exceeding token budgets, repeating prior content, or slowing enough to make the surrounding system unusable. These failures matter because automated systems need to know when to keep going, when to repair an output, and when to stop.

LTE makes those thresholds explicit. It complements task-accuracy benchmarks by measuring operational degradation under the same prompts, caps, hardware, and stress policy.

## What LTE Measures

| Metric | Definition | Use |
| --- | --- | --- |
| Expansion Ratio | Output tokens divided by input tokens. | Shows whether outputs are growing beyond the workflow's budget. |
| Length Overrun Rate | Share of outputs that approach `max_tokens`. | Flags cap pressure and likely truncation risk. |
| Verbosity Drift | Length change across concise and detailed prompt variants. | Tests whether the model respects requested response shape. |
| Runaway Continuation Score | Repetition pressure, currently based on repeated n-grams. | Catches loops and recycled phrasing. |
| Latency | Generation time per prompt or stress step. | Identifies local runtime and context-growth cliffs. |
| Stress failure state | Persistent failure under a growing context window. | Marks when continued automatic use is no longer justified. |

These metrics do not measure truthfulness, safety, or broad capability. They measure whether a model remains usable under an operational contract.

## Intervention Signals

LTE turns measurement into an operational decision.

| Signal | Meaning |
| --- | --- |
| `continue` | The run remains inside the operational envelope. |
| `retry` | An isolated recoverable failure merits one tighter attempt. |
| `repair` | The output shape is wrong, but the content can be deterministically corrected. |
| `escalate` | The model still produces output but should not be trusted without oversight. |
| `abort` | Persistent or unrecoverable failure makes continued use unjustified. |

## For Evaluation Teams

LTE is useful when the question is not "which model is best overall?" but:

- when does this model stop being usable in this workflow?
- does the model become verbose or repetitive under stress?
- does it reliably stay within output constraints?
- when should an automated system retry, repair, escalate, or abort?
- how do local models compare under the same operational pressure?

Rather than collapse these questions into one aggregate score, LTE preserves the run artefacts, trigger states, and intervention recommendation.

## What This Is Not

LTE is not a frontier benchmark, a safety benchmark, or a universal reliability score. It does not claim broad model quality, factuality, alignment, or production readiness. Results should be interpreted as workflow-specific evidence about the prompts, caps, local hardware, backend, and stress settings used in a run.

Mock outputs are included for pipeline verification. They are not evidence about model quality.

## Repository Layout

| Path | Purpose |
| --- | --- |
| `lte/` | Maintained runtime, metrics, reporting, stress runner, contracts, schema, and backends. |
| `configs/` | Benchmark, stress, and unified-run configs. |
| `suites/` | YAML-defined probe suites. |
| `examples/` | Deterministic mock configs and outputs for smoke testing. |
| `docs/` | Methodology, positioning, working paper draft, product notes, and integration notes. |
| `results/` | Checked-in run artefacts, including the five-model weekend sweep. |
| `research/` | Exploratory and legacy research tracks. |
| `tests/` | Unit and smoke tests for metrics, contracts, CLI behaviour, suites, and scripts. |

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

List available suites:

```bash
lte list-suites
```

List configured models:

```bash
lte list-models --config configs/stress_all_models.yaml
```

## Run Tests

```bash
python -m pytest -q
```

The tests use the mock backend where possible. MLX-backed benchmark runs require local model files under `mlx_models/`.

## Run the Benchmark

Run the default benchmark config:

```bash
lte run --config configs/default.yaml --progress
```

This writes:

- `results/run_<run_id>.jsonl`
- `reports/run_<run_id>/report.md`

Generate a report from an existing run:

```bash
lte report --input results/run_<run_id>.jsonl --output reports/run_<run_id>/
```

Run the unified benchmark and stress flow:

```bash
lte unified --config configs/unified_weekend.yaml --run-id unified_real_demo --progress
```

Unified runs write one artefact set under `results/unified_<run_id>/`:

- `benchmark.jsonl`
- `stress.jsonl`
- `merged.jsonl`
- `summary.json`
- `report.md`

## Stress Mode

Stress mode grows the context window and stops after persistent operational failure rather than a single bad step.

```bash
lte stress --config configs/stress_all_models.yaml --progress
```

For a unified multi-model sweep over the benchmark battery and stress test:

```bash
lte unified --config configs/stress_all_models.yaml --run-id unified_sweep --progress
```

Failure can be defined through repetition (`max_rcs`), near-cap outputs (`fail_on_lorr`), latency thresholds (`max_latency_ms`), and required consecutive failed steps (`consecutive`).

For a deterministic smoke test without MLX:

```bash
lte stress --config examples/stress_mock_config.yaml --run-id demo_stress --force
```

## MLX Setup

LTE is designed for local model execution on Apple Silicon through MLX. Download or prepare MLX-formatted models:

```bash
python experiments/download_models.py
```

Models are expected under `mlx_models/` by default. Mock configs in `examples/` do not require MLX or local model weights.

## Key Results From Published Sweep

The five-model sweep is preserved under `results/weekend_sweep_full/`. It used the four benchmark probe suites in `configs/default.yaml` and the stress configuration in `configs/stress_all_models.yaml`. The checked-in baseline summary contains six baseline runs per model, covering two temperatures and three seeds.

The most consistent degradation pattern was over-expansion, which appeared across all five models. Context decay appeared in four models, persistent failure in three, and latency cliff behaviour in Mistral-7B-Instruct-v0.3 under the configured stress rule.

| Model | Baseline runs | Recommendation counts | Trigger counts | Mean contract failures | Mean stress latency |
| --- | ---: | --- | --- | ---: | ---: |
| Phi-4-mini-instruct-8bit | 6 | `escalate`: 6 | `context_decay`: 6, `over_expansion`: 6 | 7.0 | 2866.9 ms |
| Meta-Llama-3.1-8B-Instruct-3bit | 6 | `escalate`: 6 | `context_decay`: 6, `over_expansion`: 6 | 9.0 | 4429.1 ms |
| Mistral-7B-Instruct-v0.3 | 6 | `abort`: 6 | `latency_cliff`: 6, `over_expansion`: 6, `persistent_failure`: 6 | 4.0 | 6301.3 ms |
| Phi-3-mini-4k-instruct-4bit | 6 | `abort`: 6 | `context_decay`: 6, `near_cap_pressure`: 6, `over_expansion`: 6, `persistent_failure`: 6 | 11.0 | 5226.1 ms |
| SmolLM-1.7B-Instruct-4bit | 6 | `abort`: 6 | `context_decay`: 6, `near_cap_pressure`: 6, `over_expansion`: 6, `persistent_failure`: 6 | 12.0 | 2924.6 ms |

Read the full artefact report: [`results/weekend_sweep_full/report.md`](results/weekend_sweep_full/report.md). The aggregated baseline summary is in [`results/weekend_sweep_full/baseline_phase_summary.json`](results/weekend_sweep_full/baseline_phase_summary.json).

These results are not a universal ranking. They describe this harness, prompt set, local runtime, and stress policy.

## Methodology

- Methodology: [`docs/methodology.md`](docs/methodology.md)
- Evaluation positioning: [`docs/eval_positioning.md`](docs/eval_positioning.md)
- Working paper draft: [`docs/whitepaper_draft.md`](docs/whitepaper_draft.md)
- Product direction: [`docs/product_direction.md`](docs/product_direction.md)
- Inspect integration notes: [`docs/inspect_integration.md`](docs/inspect_integration.md)
- Research overview: [`research/README.md`](research/README.md)

## Current Maturity

The maintained surface is the `lte/` package, CLI, configs, suites, and tests. The `research/` directory contains useful context, but not every track is equally mature or intended as the main entry point.

LTE is best read as an evaluation harness and reproducibility artefact for operational degradation signals. It is not a finished benchmark suite with broad external validation.

## Limitations

- Metrics focus on operational degradation, not semantic correctness.
- Current probes may not cover reasoning, truthfulness, or alignment.
- Local hardware performance affects latency metrics.
- Mock examples are for pipeline verification, not model-quality evidence.
- Results are workflow-specific, not universal model rankings.
- The result schema is still evolving, so historical artefacts may not have identical fields.

## Roadmap

- Add task-correctness probes alongside operational metrics.
- Stabilise reporting schemas for comparison across runs.
- Improve model-routing and escalation-policy examples.
- Add richer Inspect integration examples.
- Separate maintained harness paths from exploratory research artefacts more clearly.
- Expand reproducibility notes for local hardware and MLX model setup.

## Maintainer Notes

Suggested GitHub topics:

```text
llm-evaluation
ai-evals
model-reliability
local-llms
stress-testing
agent-evaluation
mlx
ai-safety
```

## Citation

No formal citation metadata is provided yet. If you use the repository, cite the GitHub repository and the checked-in run artefacts you rely on.
