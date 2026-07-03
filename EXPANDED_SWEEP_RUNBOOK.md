# Expanded Sweep — Overnight Runbook

## POST-MORTEM OF THE 2026-06-04 OVERNIGHT RUN — READ FIRST

The first overnight run completed all 42 local runs but had two defects:

1. **All 24 API runs failed in 0s** — "Missing required environment variable:
   ANTHROPIC_API_KEY". The keys were in `.env.local` but nothing exported them
   into the process. FIXED: the runner now auto-loads `.env.local` (existing
   env vars win; `--env-file` to change or disable) and **refuses to start** a
   real sweep if a required key for any configured backend is missing.
   Preflight prints a warning instead.
2. **The local runs only executed the 4 old suites.** The runner copied
   `suites:` from `--base-config` (configs/default.yaml) and ignored the
   models-config's suites block — so `adversarial_pressure` and
   `bounded_determination` never ran. FIXED: a `suites:` list in the
   models-config now OVERRIDES the base config (stderr prints which suites are
   in effect). Also added per-model `max_latency_ms` override in the
   models-config (API models need 8000 ms; local stays 2500).

Consequences for the data:
- The **API rerun** uses `configs/api_only_sweep.yaml` →
  `results/api_rerun/` (see "API rerun" below). 6 suites, 8000 ms cap.
- The completed **local** results in `results/expanded_sweep/` are valid for
  the 4 old suites but are MISSING the two new probe families. To get new-probe
  coverage on locals, rerun locals with the fixed runner into a fresh dir
  (suites now flow through), or report new-probe results for API models only —
  decide explicitly, don't let the asymmetry slip into the paper unmarked.
- Results from the two dirs must be merged before building paper tables; the
  per-run `summary.json` files are per-model, so merging the
  `baseline_phase_summary.json` model lists is sufficient.

### API rerun (the immediate next step)

```bash
cd ~/Documents/GitHub/local_threshold_evaluation
source .venv/bin/activate
rm -f results/api_rerun/manifest.json

# Preflight — expect 4 models / 24 runs, anthropic+openai, 6 suites,
# max_latency_ms 8000 in generated configs, and NO missing-key warning:
python scripts/run_unified_weekend.py --base-config configs/default.yaml \
  --models-config configs/api_only_sweep.yaml \
  --output-dir results/api_rerun --skip-expansion --preflight-only --progress

# Launch:
python scripts/run_unified_weekend.py --base-config configs/default.yaml \
  --models-config configs/api_only_sweep.yaml \
  --output-dir results/api_rerun --skip-expansion \
  --resume --progress 2>&1 | tee results/api_rerun/run.log
```

The runner loads `.env.local` itself now, but `set -a; source .env.local;
set +a` beforehand is harmless if you prefer belt and braces.

---

This is the step-by-step for running the expanded evidence collection on your Mac.
Everything here was built and mock-tested in a Linux sandbox that cannot run MLX
or hold your API keys, so the real runs happen on your machine. Follow the order;
the preflight steps exist to stop you wasting a night on a misconfigured run.

## What this run produces

Three things the revised paper needs:

1. **Wider scale range** — within-provider ladders (Haiku→Sonnet→Opus,
   GPT-4o-mini→4.1-mini→4.1) plus the existing local models, so the result is
   about the scaffold and scale, not "small quantised models fall over."
2. **Two new probe families** — `adversarial_pressure` and
   `bounded_determination`, which answer "the tasks are too simple."
3. **Threshold-sensitivity** — fresh runs at perturbed thresholds, the
   load-bearing result for the artifact-as-evidence claim.

## Critical: which command to use

Run the expanded sweep through `scripts/run_unified_weekend.py`, NOT through
`python -m lte run` or `python -m lte unified` directly.

Reason: the per-model `backend:` field (which routes Claude models to Anthropic,
GPT models to OpenAI, local models to MLX) is only read by the weekend sweep
driver. The single-shot `lte run` path ignores it and would send every call to
the default backend — i.e. every OpenAI call would hit the Anthropic endpoint
and fail. The weekend driver generates one correctly-routed sub-config per model.

## Step 0 — Environment

```bash
cd ~/Documents/GitHub/local_threshold_evaluation
source .venv/bin/activate
pip install -e . --quiet            # ensure package is importable
python -m pytest -q                 # expect: all pass (48+)
```

Keys: confirm `.env.local` has `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`. Do not
move keys anywhere else.

## Step 1 — Decide your model list

Open `configs/expanded_sweep.yaml`. Comment out any model you cannot run:

- No Opus/Sonnet access → comment those lines.
- Larger local models (Qwen-14B, Mistral-Small-24B) are commented out by
  default. To include them, download first (Step 1a), then uncomment.

### Step 1a — Download the two new local models

Both are pre-quantised MLX community repos, so no conversion is needed — just
download into `mlx_models/`. Both fit in 16GB real RAM (no swap), which keeps
the latency signal clean.

```bash
# (1) Llama-3.1-8B at 8-bit — the quantisation-axis comparison vs your 3-bit.
huggingface-cli download mlx-community/Meta-Llama-3.1-8B-Instruct-8bit \
  --local-dir mlx_models/Meta-Llama-3.1-8B-Instruct-8bit

# (2) Gemma-2-9B at 4-bit — architecture diversity, ~5GB.
# VERIFY this repo ID resolves. If it 404s, use one of the fallbacks below.
huggingface-cli download mlx-community/gemma-2-9b-it-4bit \
  --local-dir mlx_models/gemma-2-9b-it-4bit

# Fallbacks if the 4bit instruct repo does not exist:
#   mlx-community/gemma-2-9b-it-8bit   (instruct, larger, ~9GB)
#   mlx-community/gemma-2-9b-8bit      (base, confirmed present in the catalog)
# If you use a fallback, update both the `path` and `name` in
# configs/expanded_sweep.yaml to match the directory you downloaded into.
```

Sanity-check each downloaded model runs before the full sweep:

```bash
python -m mlx_lm.generate \
  --model mlx_models/Meta-Llama-3.1-8B-Instruct-8bit \
  --prompt "Reply with the single word: ok" --max-tokens 5
```

If that errors with an out-of-memory or returns gibberish, stop — do not include
the model, since a swapping or broken model will contaminate the latency signal.

Note on the 24B/27B models: deliberately excluded. On 16GB RAM they would page to
SSD, and because LTE measures latency as a primary signal, a swap-induced latency
spike is indistinguishable from genuine model degradation. The frontier end of the
scale range is covered by the API ladders (Haiku→Sonnet→Opus, GPT-4o-mini→4.1)
instead. Flag larger-local validation as future work requiring more RAM.

## Step 2 — Preflight (no tokens spent)

```bash
python scripts/run_unified_weekend.py \
  --base-config configs/default.yaml \
  --models-config configs/expanded_sweep.yaml \
  --output-dir results/expanded_sweep \
  --preflight-only --progress
```

This writes the generated per-model configs and the run plan without calling any
model. Open a couple of the generated configs under
`results/expanded_sweep/generated_configs/` and confirm each model's `backend`
is correct (claude→anthropic, gpt→openai, local→mlx). If any GPT model shows
`backend: anthropic`, stop and fix before spending tokens.

## Step 3 — Run the main sweep (overnight)

```bash
python scripts/run_unified_weekend.py \
  --base-config configs/default.yaml \
  --models-config configs/expanded_sweep.yaml \
  --output-dir results/expanded_sweep \
  --baseline-temps 0.0,0.2 \
  --baseline-seeds 0,1,2 \
  --skip-expansion \
  --resume --progress 2>&1 | tee results/expanded_sweep/run.log
```

Notes:
- `--skip-expansion` runs the baseline matrix only (2 temps × 3 seeds = 6 runs
  per model). Drop it if you also want the expansion phase.
- `--resume` skips any run whose `summary.json` already exists, so if the run
  dies overnight you re-issue the same command and it continues.
- API latency caps: the local cap is 2500 ms. For API models the committed
  results used 8000 ms to account for network round-trips. If you want the API
  models judged on the same latency logic as before, set their cap via the
  generated config or note that latency-cliff comparisons across local vs API
  are confounded (discuss this in the paper rather than hiding it).

## Step 4 — Threshold-sensitivity (separate, also overnight-able)

This is the result that licenses the audit artifact to function as evidence: it
shows each model's regime is a property of the model, not of where the threshold
sits. Run it against the local models (fast, deterministic) and at least the
API ladder:

```bash
# Dry run first (mock, no tokens) to confirm it executes:
python scripts/run_threshold_sensitivity.py \
  --base-config configs/stress_all_models.yaml \
  --out results/threshold_sensitivity_dry \
  --grid 0.8,1.0,1.2 --backend mock

# Real run, finer grid around the regime boundaries:
python scripts/run_threshold_sensitivity.py \
  --base-config configs/stress_all_models.yaml \
  --out results/threshold_sensitivity \
  --grid 0.7,0.85,0.9,1.0,1.1,1.15,1.3
```

Output: `results/threshold_sensitivity/stability_report.json` plus a printed
table marking each model STABLE or FLIPS. Interpretation:
- **All STABLE** → the headline validity claim holds: the artifact's verdict is
  robust, so it is admissible as evidence. This is the result you want.
- **Some FLIP** → the regimes near those models are threshold-sensitive. That is
  not fatal but it must be reported honestly, and the paper's claim narrows to
  the models whose regimes are stable. Tell me which flip and we adjust the
  argument; do NOT bury it.

To run sensitivity on API models, point `--base-config` at a config whose model
list is the API ladder (e.g. a copy of `configs/api_baseline_models.yaml` with
the stress block from `stress_all_models.yaml` appended).

## Step 5 — When it's done

Send me (or just re-open here):
- `results/expanded_sweep/` baseline_phase_summary.json
- `results/threshold_sensitivity/stability_report.json`
- the `run.log` tail if anything errored

I'll build the new results tables and figures from those, and we'll see whether
the wider scale range changes the story — in particular whether any *frontier*
model lands in escalate/abort, which would be a much stronger result than the
current "small models abort" framing.

## Rough cost / time

- API: ~6 models × 6 baseline runs × ~20 probes × stress steps. Mostly cheap
  models; Opus/4.1 are the cost drivers. Expect a few dollars, not hundreds.
  Watch the first model's run in the log to calibrate before walking away.
- Local: bounded by your Mac. The existing five ran fine overnight; 14B–24B
  models are slower and may not finish all seeds — use `--resume`.
