# Drift v0

`drift_v0` is a lightweight, MacBook-feasible experiment track for detecting LLM failure signals
that should trigger intervention.

## Scope

- `E1`: Single-turn baseline reliability.
- `E2`: Three-turn short-horizon reliability with carried state.
- `E3`: Context-pressure comparison (`1k` vs `4k`) on E2-style tasks.

## Multi-agent workflow

Use the repo-local agent protocol rather than ad hoc parallel threads:

- operating protocol: [`AGENT_OPERATING_PROTOCOL.md`](./AGENT_OPERATING_PROTOCOL.md)
- copy-paste prompts: [`AGENT_PROMPTS.md`](./AGENT_PROMPTS.md)
- hard ownership boundaries: [`OWNERSHIP.md`](./OWNERSHIP.md)
- folder-local guardrails: [`AGENTS.md`](./AGENTS.md)

## Agent Split

- Agent A owns [`tasks/`](./tasks/).
- Agent B owns [`runner/`](./runner/).
- Agent C owns [`analysis/`](./analysis/).

See [`OWNERSHIP.md`](./OWNERSHIP.md) for strict boundaries and review rules.
Shared task context lives in [`tasks/task_blueprint.md`](./tasks/task_blueprint.md) and
[`tasks/schema_registry.json`](./tasks/schema_registry.json).

## Quick Run

1. Ensure your task file exists (`tasks/*.jsonl`).
2. Run model episodes with your existing backend and write JSONL events.
3. Run:
   - `python research/drift_v0/runner/evaluate_events.py --input <events.jsonl> --output <evaluated.jsonl>`
   - `python research/drift_v0/analysis/summarize.py --input <evaluated.jsonl>`

The evaluator emits trigger flags and intervention decisions. The summarizer prints compact
metrics for `E1/E2/E3`.

## End-to-end Run (Raw -> Evaluated -> Analysis)

```bash
python research/drift_v0/runner/run_experiments.py \
  --task-pack research/drift_v0/tasks/e1_tasks_v1.jsonl \
  --output /tmp/drift_v0_e1_raw.jsonl \
  --model-name <your_model_name> \
  --model-path <your_mlx_model_path> \
  --backend mlx

python research/drift_v0/runner/evaluate_events.py \
  --input /tmp/drift_v0_e1_raw.jsonl \
  --output /tmp/drift_v0_e1_eval.jsonl \
  --task-pack research/drift_v0/tasks/e1_tasks_v1.jsonl \
  --schema-registry research/drift_v0/tasks/schema_registry.json

python research/drift_v0/analysis/summarize.py \
  --input /tmp/drift_v0_e1_eval.jsonl \
  --output-dir /tmp/drift_v0_e1_report
```

## Overnight Parameter Sweep

Use `run_sweep.py` to evaluate multiple models and decoding settings automatically.

1. Copy and edit config:
```bash
cp research/drift_v0/runner/sweep_config_template.json /tmp/drift_v0_sweep_config.json
```

2. Launch sweep:
```bash
python research/drift_v0/runner/run_sweep.py \
  --config /tmp/drift_v0_sweep_config.json \
  --output-root /tmp/drift_v0_sweep
```

3. Resume interrupted sweep:
```bash
python research/drift_v0/runner/run_sweep.py \
  --config /tmp/drift_v0_sweep_config.json \
  --output-root /tmp/drift_v0_sweep \
  --resume
```

4. Background overnight:
```bash
nohup python research/drift_v0/runner/run_sweep.py \
  --config /tmp/drift_v0_sweep_config.json \
  --output-root /tmp/drift_v0_sweep \
  --resume > /tmp/drift_v0_sweep.log 2>&1 &
```

The sweep writes per-condition reports under `/tmp/drift_v0_sweep/<condition_id>/report/` and an
aggregate manifest at `/tmp/drift_v0_sweep/sweep_manifest.csv`.

## Weekend run infrastructure

First generate a local config from whatever models are actually present:

```bash
.venv/bin/python scripts/prepare_drift_weekend_config.py \
  --models-dir mlx_models \
  --output research/drift_v0/runner/sweep_config_weekend_local.json
```

Then run a preflight check:

```bash
.venv/bin/python scripts/run_drift_weekend.py \
  --sweep-config research/drift_v0/runner/sweep_config_weekend_local.json \
  --output-root artifacts/drift_v0/weekend \
  --preflight-only
```

For repo-local runs that include tests, sweeps, failure-cause tables, and paper assets:

```bash
.venv/bin/python scripts/run_drift_weekend.py \
  --sweep-config research/drift_v0/runner/sweep_config_weekend_local.json \
  --output-root artifacts/drift_v0/weekend \
  --assets-output-dir artifacts/drift_v0/weekend/paper_assets \
  --resume
```

For a fast smoke test that does not require MLX models:

```bash
.venv/bin/python scripts/run_drift_weekend.py \
  --sweep-config research/drift_v0/runner/sweep_config_mock.json \
  --output-root artifacts/drift_v0/mock_smoke
```
