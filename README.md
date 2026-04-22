# Local Token Expansion (LTE)

Local Token Expansion (LTE) is a local-first evaluation harness for measuring when LLMs stop being operationally useful under workflow pressure.

Local-first LLM evaluation harness for reliability, stress testing, operational degradation, and intervention signals.

Most LLM benchmarks focus on task accuracy, preference, or leaderboard performance. LTE focuses on a different failure surface: operational degradation. It measures how models behave when prompts grow, outputs expand, latency rises, repetition appears, or failures persist long enough that an automated workflow should stop, retry, repair, escalate, or abort.

## Why This Matters

Production LLM workflows often fail before they become obviously wrong. A model can become too verbose for the downstream contract, push against token caps, repeat itself, slow down under context growth, or require repeated repair attempts. Those failures matter for routing, escalation, local deployment, and monitoring even when a static task benchmark looks acceptable.

LTE turns those behaviors into deployment-relevant signals. It is meant to complement standard evals by asking whether a model remains useful inside a constrained workflow.

## What This Is Not

LTE is not a general model leaderboard. It does not claim broad model capability, truthfulness, safety, alignment, or universal reliability. Results should be interpreted as workflow-specific evidence about operational degradation under the prompts, caps, local hardware, and stress settings used in a run.

## What LTE Measures

| Metric | What it captures | Why it matters |
| --- | --- | --- |
| Expansion Ratio | Output tokens divided by input tokens. | Detects output growth that can break cost, latency, or downstream parsing assumptions. |
| Length Overrun Rate | Share of outputs that approach the configured `max_tokens` cap. | Flags cap pressure and likely truncation risk. |
| Verbosity Drift | Change in output length across concise and detailed prompt variants. | Shows whether a model respects requested response shape under prompt pressure. |
| Runaway Continuation Score | Repetition pressure, currently based on repeated n-grams in generated text. | Catches looping or continuation behavior that makes output operationally unusable. |
| Latency | Generation latency per prompt or stress step. | Exposes local hardware and context-growth cliffs relevant to deployment. |
| Stress failure state | Persistent failure under a growing context window. | Identifies when continued automatic use should stop or escalate. |

## Intervention Signals

LTE emits intervention signals for downstream systems:

| Signal | Meaning |
| --- | --- |
| `continue` | Output remains within the operational envelope. |
| `retry` | A transient failure may be worth another attempt. |
| `repair` | Output appears recoverable through a targeted fix or structured repair pass. |
| `escalate` | Automation should hand off or route to a more capable path. |
| `abort` | Persistent or unrecoverable failure makes continued use unjustified. |

## For Evaluation Teams

LTE is useful when the question is not "which model is best overall?" but:

- when does this model stop being usable in this workflow?
- does the model become verbose or repetitive under stress?
- does it reliably stay within output constraints?
- when should an automated system retry, repair, escalate, or abort?
- how do local models compare under the same operational pressure?

The repository is structured around reproducible local runs, JSONL artifacts, Markdown reports, and explicit intervention recommendations rather than a single aggregate score.

## Repository Layout

| Path | Purpose |
| --- | --- |
| `lte/` | Maintained runtime, metrics, reporting, stress runner, schema, contracts, and backends. |
| `configs/` | Runnable benchmark, stress, and unified-run configuration files. |
| `suites/` | YAML-defined probe suites. |
| `examples/` | Deterministic mock configs and example outputs for smoke testing. |
| `docs/` | Methodology, positioning, working paper draft, product notes, and integration notes. |
| `results/` | Checked-in run artifacts, including the five-model weekend sweep. |
| `research/` | Exploratory and legacy research tracks. |
| `tests/` | Unit and smoke tests for metrics, contracts, CLI behavior, suites, and scripts. |

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

The test suite uses the mock backend where possible. MLX-backed benchmark runs require local model files under `mlx_models/`.

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

Run the unified benchmark plus stress flow:

```bash
lte unified --config configs/unified_weekend.yaml --run-id unified_real_demo --progress
```

Unified runs write one artifact set under `results/unified_<run_id>/`:

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

For a unified multi-model sweep over the benchmark battery plus stress:

```bash
lte unified --config configs/stress_all_models.yaml --run-id unified_sweep --progress
```

Failure can be defined through:

- repetition (`max_rcs`)
- near-cap outputs (`fail_on_lorr`)
- latency thresholds (`max_latency_ms`)
- required consecutive failed steps (`consecutive`)

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

The five-model sweep is preserved under `results/weekend_sweep_full/`. It used four benchmark probe suites from `configs/default.yaml` plus the stress configuration in `configs/stress_all_models.yaml`. The checked-in baseline summary contains six baseline runs per model, covering two temperatures and three seeds.

The most consistent degradation patterns in this artifact were over-expansion across all five models, context decay in four of five models, persistent failure in three of five models, and latency cliff behavior for Mistral-7B-Instruct-v0.3 under the configured stress rule.

| Model | Baseline runs | Recommendation counts | Trigger counts | Mean contract failures | Mean stress latency |
| --- | ---: | --- | --- | ---: | ---: |
| Phi-4-mini-instruct-8bit | 6 | `escalate`: 6 | `context_decay`: 6, `over_expansion`: 6 | 7.0 | 2866.9 ms |
| Meta-Llama-3.1-8B-Instruct-3bit | 6 | `escalate`: 6 | `context_decay`: 6, `over_expansion`: 6 | 9.0 | 4429.1 ms |
| Mistral-7B-Instruct-v0.3 | 6 | `abort`: 6 | `latency_cliff`: 6, `over_expansion`: 6, `persistent_failure`: 6 | 4.0 | 6301.3 ms |
| Phi-3-mini-4k-instruct-4bit | 6 | `abort`: 6 | `context_decay`: 6, `near_cap_pressure`: 6, `over_expansion`: 6, `persistent_failure`: 6 | 11.0 | 5226.1 ms |
| SmolLM-1.7B-Instruct-4bit | 6 | `abort`: 6 | `context_decay`: 6, `near_cap_pressure`: 6, `over_expansion`: 6, `persistent_failure`: 6 | 12.0 | 2924.6 ms |

Read the full artifact report: [`results/weekend_sweep_full/report.md`](results/weekend_sweep_full/report.md). The aggregated baseline summary is in [`results/weekend_sweep_full/baseline_phase_summary.json`](results/weekend_sweep_full/baseline_phase_summary.json).

These results are not a universal ranking. They describe the behavior of this harness, prompt set, local runtime, and stress policy.

## Example Outputs

Small deterministic example runs are checked into `examples/` for smoke testing and report generation. Treat mock outputs as pipeline verification artifacts, not model-quality evidence.

## Methodology

- Methodology: [`docs/methodology.md`](docs/methodology.md)
- Evaluation positioning: [`docs/eval_positioning.md`](docs/eval_positioning.md)
- Working paper draft: [`docs/whitepaper_draft.md`](docs/whitepaper_draft.md)
- Product direction: [`docs/product_direction.md`](docs/product_direction.md)
- Inspect integration notes: [`docs/inspect_integration.md`](docs/inspect_integration.md)
- Research overview: [`research/README.md`](research/README.md)

## Current Maturity

The maintained product surface is the `lte/` package, the CLI, the configs, the suites, and the tests. The `research/` directory contains useful context, but not every research track is equally mature or intended as the main entry point.

LTE is currently best read as an evaluation harness and reproducibility artifact for operational degradation signals. It is not a finished benchmark suite with broad external validation.

## Limitations

- Metrics focus on operational degradation, not semantic correctness.
- Current probes may not cover reasoning, truthfulness, or alignment.
- Local hardware performance affects latency metrics.
- Mock examples are for pipeline verification, not model-quality evidence.
- Results should be interpreted as workflow-specific, not universal model rankings.
- The current result schema is still evolving, so historical artifacts may not have identical fields.

## Roadmap

- Add task-correctness probes alongside operational metrics.
- Stabilize reporting schemas for easier comparison across runs.
- Improve model-routing and escalation policy examples.
- Add richer Inspect integration examples.
- Separate mature harness paths from exploratory research artifacts more clearly.
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

No formal citation metadata is provided yet. If you use the repository, cite the GitHub repository and the checked-in run artifacts you rely on.
