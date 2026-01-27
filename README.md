# Local Token Expansion – Propensity Experiment

This repo contains a reproducible pipeline to stress‑test local MLX LLMs and measure when outputs become repetitive, truncated, or otherwise less useful.

---

## Motivation
We want to understand the **usefulness → repetition cliff** in local models.  
Instead of “trying to break” a model, we measure **when it stops adding meaningful new content** by tracking novelty, repetition, format adherence, and truncation across many steps.

---

## What It Does
The pipeline runs a **rolling, step‑by‑step prompt loop** and logs:
- **Novelty** (new tokens vs all prior steps)
- **Repetition** (n‑gram overlap)
- **Similarity to previous response**
- **Truncation** (hit max tokens)
- **Refusal / stall / already‑answered signals**
- **Format adherence** (if enabled)

Current mode is **feature accretion** for an NLP pipeline:
each step adds exactly **one new feature** and outputs only the **delta**.

---

## What We’re Testing
We’re testing **when a local LLM stops being useful under sustained, repetitive pressure**.  
Specifically:
- Can it keep adding **new, meaningful features** over many steps?
- Does it **remember recent context** when probed (short‑term memory)?
- At what point does it **repeat itself**, **stall**, or **drift** from the required format?
- How quickly does **latency balloon** as the run continues?

This is not about “breaking” the model in a security sense — it’s about **detecting the usefulness → repetition cliff**.

---

## What “Degradation” Looks Like (Evidence)
We treat the following as signals that the model is entering a **response degradation phase**:

1) **Novelty collapse**
   - `novelty_score` stays below threshold for multiple steps.

2) **Repetition / similarity spikes**
   - `repetition_rate` climbs and `similarity_to_prev` stays high.

3) **Format drift**
   - Missing required sections (Feature/Motivation/Patch/Test).
   - `format_ok` falls consistently.

4) **Memory failure**
   - Incorrect answers to memory probes (wrong language).
   - `memory_match` drops and `memory_distance` rises.

5) **Stalling / refusal**
   - `stall_flag` or `refusal_flag` becomes common.

6) **Latency blow‑up**
   - Response time jumps far above baseline for multiple steps
   - Stops when `latency_threshold_reached` is triggered.

When multiple signals align, we consider that a **true degradation event**.

---

## Project Layout
```
experiments/
  run_propensity.py        # main experiment runner
  run_all_models.py        # batch runner (multiple models)
  download_models.py       # download MLX models from HF
  analysis.ipynb           # analysis + plots
  configs/
    local_llm_propensity.json
  outputs/
    *.jsonl
mlx_models/
  Mistral-7B-Instruct-v0.3
```

---

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Download Models
```bash
python experiments/download_models.py
```
This pulls MLX‑formatted models from Hugging Face and symlinks them into `mlx_models/`.  
Use `--copy` if you prefer to duplicate files instead of symlinks.

---

## Run a Single Model
```bash
python experiments/run_propensity.py --config experiments/configs/local_llm_propensity.json
```

Output is written to `experiments/outputs/<run_name>.jsonl`.

---

## Run All Models (Same Grid)
```bash
python experiments/run_all_models.py --config experiments/configs/local_llm_propensity.json
```
Outputs are grouped by model name in the JSONL filename.

---

## Analyze Results
```bash
jupyter lab experiments/analysis.ipynb
```
The notebook visualizes:
- Novelty over time
- Repetition and similarity
- Breakdown score and truncation
- Feature ledger growth
- Format adherence rates

---

## Key Config Knobs
Edit `experiments/configs/local_llm_propensity.json` to tune behavior:
- `mode`: `"feature_accretion"` (recommended)
- `prompt_template`: controls the task + format
- `feature_categories`: soft pool for rotating additions
- `novelty_threshold`, `novelty_consecutive`: stop when novelty collapses
- `max_steps_per_run`, `max_gen_tokens`, `safety_margin_tokens`
- `models`: list of model paths for batch runs

---

## Expected Outputs
Each JSONL record contains:
- prompt, response, tokens, timing
- novelty, repetition, similarity
- truncation, refusal, stall, already‑answered
- breakdown score + flag
- feature ledger info + format adherence

These metrics help pinpoint when the model stops adding useful content.

---

## Next Steps (Optional)
- Add external evaluation using ChatGPT’s API for richer scoring of tone, structure, and coherence.
- Compare “cliff step” across multiple model families.
- Add retry-on-format‑failure to enforce deltas.

---
