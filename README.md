# Local Token Expansion (LTE)

LTE is a local-first reliability and intervention pipeline for LLM-based systems.

It is designed to detect when a model stops being operationally useful in an automated workflow and to emit explicit intervention signals for downstream systems:

- `continue`
- `retry`
- `repair`
- `escalate`
- `abort`

The focus is not general model quality. LTE measures operational degradation on local hardware: over-expansion, cap pressure, repetition, context decay, latency cliffs, and persistent failure under stress.

## Start Here

- Working paper: [docs/whitepaper_draft.md](docs/whitepaper_draft.md)
- Methodology: [docs/methodology.md](docs/methodology.md)
- Product direction: [docs/product_direction.md](docs/product_direction.md)
- Weekend sweep results: [results/weekend_sweep_full/report.md](results/weekend_sweep_full/report.md)
- Research tracks: [research/README.md](research/README.md)

## What LTE Measures

- `Expansion Ratio (ER)`: output tokens relative to input tokens
- `Length Overrun Rate (LORR)`: how often outputs push against `max_tokens`
- `Verbosity Drift (VD)`: how much longer "detailed" variants become than concise ones
- `Runaway Continuation Score (RCS)`: repetition pressure in model outputs
- Stress failure state: when repeated failures make continued use unjustified

These metrics are meant to support deployment decisions, not leaderboard ranking.

## Repo Layout

- `lte/`: maintained runtime, metrics, reporting, stress runner, and backends
- `configs/`: runnable benchmark and stress configs
- `suites/`: YAML-defined probe suites
- `examples/`: deterministic mock runs for smoke testing and report generation
- `docs/`: methodology, working paper, and project notes
- `research/`: exploratory and legacy research tracks

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

List suites:

```bash
lte list-suites
```

Run tests:

```bash
python -m pytest -q
```

## MLX Setup

LTE is designed for local model execution on Apple Silicon via MLX.

Download or prepare MLX-formatted models:

```bash
python experiments/download_models.py
```

Models are placed or symlinked under `mlx_models/` by default.

## Running LTE

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

Run the unified single-model benchmark + stress flow:

```bash
lte unified --config configs/unified_weekend.yaml --run-id unified_real_demo --progress
```

This writes one merged artifact set under `results/unified_<run_id>/` including:

- `benchmark.jsonl`
- `stress.jsonl`
- `merged.jsonl`
- `summary.json`
- `report.md`

## Stress Mode

Use stress mode to find the point where the model stops being worth using under a growing context window.

```bash
lte stress --config configs/stress_all_models.yaml --progress
```

For a unified multi-model sweep over the full benchmark battery plus stress:

```bash
lte unified --config configs/stress_all_models.yaml --run-id unified_sweep --progress
```

Stress mode is designed to stop after persistent failure rather than a single bad step. Failure can be defined through:

- repetition (`max_rcs`)
- near-cap outputs (`fail_on_lorr`)
- latency thresholds (`max_latency_ms`)
- required consecutive failed steps (`consecutive`)

For a small deterministic example without MLX:

```bash
lte stress --config examples/stress_mock_config.yaml --run-id demo_stress --force
```

## Example Outputs

Small deterministic example runs are checked into `examples/` for smoke testing and report generation.

Treat these as harness examples, not as evidence of task quality. The mock backend is intended for deterministic pipeline verification rather than meaningful model evaluation.

## Reproducing The Published Sweep

The five-model sweep used in the working paper is documented under `results/weekend_sweep_full/`:

- `report.md`: top-level run summary
- `baseline_phase_summary.json`: baseline aggregation
- `generated_configs/`: per-run configs
- `runs/`: per-run artifacts used to generate figures and summaries

The checked-in results are the primary public artifact for that sweep. The command below is an example for running a local weekend-style pipeline, not a guarantee of bit-for-bit reproduction of every checked-in artifact.

```bash
lte unified --config configs/unified_weekend.yaml --run-id my_run --progress
```

For a deterministic smoke test:

```bash
lte unified --config examples/unified_mock_config.yaml --run-id mock_demo
```

## Methodology

- Benchmark methodology: [docs/methodology.md](docs/methodology.md)
- Product direction: [docs/product_direction.md](docs/product_direction.md)
- Inspect integration notes: [docs/inspect_integration.md](docs/inspect_integration.md)
- `drift_v0` operating protocol: [research/drift_v0/AGENT_OPERATING_PROTOCOL.md](research/drift_v0/AGENT_OPERATING_PROTOCOL.md)

## Legacy and Research Tracks

Not everything in this repo is equally mature.

- `lte/` is the maintained product surface.
- `research/propensity/` is exploratory legacy work.
- `research/drift_v0/` is a research track focused on explicit trigger logic, interventions, and accountability framing.

If you are trying to understand the project quickly, start with `lte/`, `configs/`, `suites/`, and the docs above.
