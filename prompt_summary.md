# Prompt Summary (Chat Handoff)

This file summarizes the conversation with the assistant so another LLM can reproduce the pipeline with minimal intervention.  
It is intentionally verbose and includes **examples of our interactions** so a future LLM can see *how* the pipeline evolved.

---

## Goal
Design a **stress‑test pipeline** for local MLX models to measure when responses become repetitive or lose usefulness.  
We moved from simple prompts to a **feature‑accretion task** that forces novelty and makes “usefulness → repetition” measurable.

Example interaction:
> **User:** “how else can i strain test this llm, the responses it gave are all very generic.”  
> **Assistant:** Suggested tradeoff prompts, debugging prompts, and tracked truncation + repetition.

---

## What We Built

### 1) `experiments/run_propensity.py`
Single‑model experiment runner with a rolling loop that:
- Builds prompts
  - **Mode 1 (legacy):** language‑specific prompts  
  - **Mode 2 (current):** **feature_accretion** mode for an NLP pipeline
- Generates responses via `mlx_lm.generate`
- Logs metrics per step:
  - `repetition_rate`, `similarity_to_prev`
  - `novelty_score` (new tokens vs all prior)
  - `hit_max_gen_tokens`
  - `refusal_flag`, `stall_flag`, `already_answered_flag`
  - `breakdown_score` and `breakdown_flag`
  - `feature_name`, `feature_ledger_count`
  - `format_ok`, `format_missing`
- Stops on breakdown conditions:
  - repetition streak
  - novelty collapse for N steps
  - format adherence failure
  - context exhaustion

Key changes we made (with context):
- Removed `prev_response` echoing.  
  **Why:** It caused context bloat and didn’t improve novelty.  
  **User prompt:** “regiving it the previous response did very little, i'd rather leave the token window open.”
- Added **truncation** tracking (`hit_max_gen_tokens`).  
  **User:** “i think tracking truncation rate is good.”
- Added **already‑answered** and **stall** detection.  
  **User:** “what kind of response would we expect if it was breaking?”
- Added **breakdown score** combining these signals.  
  **User:** “yeah that would be useful, because it feels like it's just repeating the same answer.”
- Added **feature accretion mode** with:
  - feature ledger + spec summary injected into prompt
  - novelty score tracking
  - format adherence checks
- Fixed `extract_feature_name()` regex to correctly detect `Feature: ...`.

### 2) `experiments/configs/mistral_propensity.json`
Config now includes:
- `mode: "feature_accretion"`
- `prompt_template` for NLP pipeline feature deltas
- `feature_categories` (soft pool)
- `spec_summary_max_chars`
- `novelty_threshold`, `novelty_consecutive`
- `format_adherence_required`
- `models` list for multi‑model runs

### 3) `experiments/download_models.py`
Downloads MLX models from HF using `mlx_lm.utils._download`.  
Default list includes:
```
mlx-community/Meta-Llama-3.1-8B-Instruct-3bit
mlx-community/Phi-3-mini-4k-instruct-4bit
mlx-community/SmolLM-1.7B-Instruct-4bit
mlx-community/Phi-4-mini-instruct-8bit
```
Symlinks into `mlx_models/` by default (use `--copy` to duplicate).

### 4) `experiments/run_all_models.py`
Batch runner that:
- Iterates the model list
- Creates temp config per model
- Runs `run_propensity.py` sequentially
- Logs progress + elapsed time
Outputs grouped by model name.

### 5) `experiments/analysis.ipynb`
Notebook to visualize:
- Novelty over time
- Repetition + similarity
- Breakdown score + truncation
- Feature ledger growth
- Format adherence rates

---

## Current Mode: Feature Accretion (NLP pipeline)
Prompt format (from the config):
```
Feature: <short name>
Motivation: <1-2 sentences>
Behavior change: <what changes>
Patch: <pseudo-diff or step list>
Test: <one concrete test>
```
Model must **add exactly one new feature**, output **delta only**, and avoid restating prior content.

Example interaction:
> **User:** “let's build something i can actually evaluate. build an nlp pipeline or something more research/less IT.”  
> **Assistant:** Implemented feature‑accretion mode and NLP‑focused prompt.

Spec summary + feature ledger are injected each step (short and bounded).

---

## Known Issues & Fixes
1) `feature_name` was always `None` — fixed regex to `^\s*Feature:\s*(.+)$`.  
   This broke the ledger/spec summary and made novelty stops misleading.  
   The user asked: “have a look through the results and tell me what went wrong.”
2) Format adherence gating added; can optionally fail fast.  
   Added `format_ok` + `format_missing` fields.
3) Seaborn install issue in notebook — fix via:
```
!{sys.executable} -m pip install seaborn
```

---

## How to Reproduce
1) Download models:
```
python experiments/download_models.py
```

2) Run one model:
```
python experiments/run_propensity.py --config experiments/configs/mistral_propensity.json
```

3) Run all models:
```
python experiments/run_all_models.py --config experiments/configs/mistral_propensity.json
```

4) Analyze:
```
jupyter lab experiments/analysis.ipynb
```

---

## If you continue this chat
Ask the new LLM to:
1) Verify `run_propensity.py` metrics and stop conditions
2) Confirm config values in `mistral_propensity.json`
3) Regenerate analysis plots if output files are new
4) Adjust novelty/repetition thresholds based on model behavior

---

## What the user cared about most
- Detect **when responses stop being useful** (not just refusal).
- Force **novelty and change over time**.
- Keep the context window open to long outputs.
- Compare multiple models fairly.
- Keep everything measured and reproducible.

---

## Example Conversation Flow (Condensed)

These are paraphrased snippets that show how the system evolved:

1) **Generic outputs problem**
> “responses are all very generic”
→ We added repetition metrics, truncation tracking, and prompt variation.

2) **Breaking point definition**
> “what kind of response would we expect if it was breaking?”
→ We defined refusal, stall, truncation, repetition, context exhaustion.

3) **Adaptive prompt**
> “if it already answered the prompt about a specific language, can we trigger a different prompt?”
→ Added repeat prompt template and `prompt_type` field.

4) **Pivot to feature accretion**
> “what if we pivot to asking it to continue adding features…”
→ Built feature‑accretion mode with ledger + novelty scoring.

5) **Debugging results**
> “have a look through the results and tell me what went wrong”
→ Discovered regex bug, fixed feature extraction, added format adherence.

6) **Multi‑model comparison**
> “generate a new script that downloads 4 more models”
→ Added downloader + batch runner to compare models with same grid.

7) **Documentation**
> “document everything”
→ Added docstrings, analysis notebook, README, and this handoff file.

---

## Concrete File/Code References (So Another LLM Can Act Quickly)

### `experiments/run_propensity.py` (core runner)
Key functional blocks to understand:
- **Prompt creation** (language mode vs feature‑accretion mode)
- **Generation call** (`mlx_lm.generate`) with fallback for argument compatibility
- **Metrics** (novelty, repetition, similarity, refusal, stall, truncation, breakdown)
- **Stop conditions** (novelty collapse, repetition streak, format failure, context exhaustion)

Short code excerpt (logic sketch, not full file):
```
if mode == "feature_accretion":
    prompt = template.format(feature_ledger, spec_summary, categories)
else:
    prompt = template.format(language=language)

response = generate(...)
novelty_score = token_novelty_score(response, seen_tokens)
feature_name = extract_feature_name(response)

if novelty_score < threshold for N steps -> stop
if format missing -> stop
```

### `experiments/configs/mistral_propensity.json` (config knobs)
Key fields to tune:
- `mode`: `"feature_accretion"`
- `prompt_template`: delta‑only NLP pipeline prompt
- `feature_categories`: soft pool to rotate categories
- `novelty_threshold`, `novelty_consecutive`
- `format_adherence_required`
- `max_steps_per_run`, `max_gen_tokens`, `safety_margin_tokens`
- `models`: list of model paths for batch runs

### `experiments/run_all_models.py` (batch runner)
Sequential model loop that:
1) clones config per model
2) sets run_name with model suffix
3) runs `run_propensity.py` sequentially
4) logs elapsed time

### `experiments/download_models.py`
Downloads MLX models from HF and symlinks them into `mlx_models/`.
Use `--copy` if you don’t want symlinks.

---

## Example Config Snippet (Feature Accretion)
```
{
  "mode": "feature_accretion",
  "prompt_template": "You are a research engineer designing an NLP pipeline. Add exactly ONE new feature ...",
  "feature_categories": ["Data ingestion", "Tokenization", "Evaluation", ...],
  "novelty_threshold": 0.25,
  "novelty_consecutive": 3,
  "format_adherence_required": true,
  "max_steps_per_run": 30,
  "max_gen_tokens": 512
}
```

---

## Example JSONL Record (What to Expect)
```
{
  "record_type": "prompt_response",
  "run_id": "mistral_propensity_features__Mistral-7B-Instruct-v0.3_run_0000",
  "step": 7,
  "mode": "feature_accretion",
  "feature_name": "Bias Audit",
  "novelty_score": 0.31,
  "repetition_rate": 0.07,
  "similarity_to_prev": 0.18,
  "hit_max_gen_tokens": false,
  "format_ok": true,
  "breakdown_score": 0.0
}
```

---

## How to Interpret the Signals (Plain English)
- **Novelty drops** → model is recycling the same concepts.
- **Repetition rate rises** → surface‑level loops, boilerplate recycling.
- **Similarity to previous rises** → responses are close to last step.
- **Hit max tokens** → response is being cut off; not necessarily “breaking,” but output quality is constrained.
- **Format fails** → the model can’t reliably follow simple structure anymore.
These together define the “usefulness → repetition cliff.”

---

## Troubleshooting + Lessons Learned

1) **Feature ledger not working**
- Symptom: `feature_name` is always `null`.
- Cause: regex was incorrectly escaped.
- Fix: `r"^\s*Feature:\s*(.+)$"`

2) **Generations failing with `unexpected keyword argument`**
- MLX version mismatch (temperature vs temp).  
- Solution: `generate_with_fallback()` removes unsupported args or maps `temperature -> temp`.

3) **Template repetition**
- Early prompts were too generic; output was boilerplate.
- Pivoted to “add one new feature” to force novelty.

---

## Suggested Next Improvements (if you continue)

1) **Add “retry on format failure”**
If `format_ok == false`, re‑prompt once with a stricter instruction before stopping.

2) **Novelty vs. window**
Currently novelty is measured against *all* prior tokens.  
Option: measure against last N steps to avoid punishing fixed headers.

3) **Add requirement coverage**
Track whether specific required terms appear (e.g., “bias audit,” “drift detection”).

4) **Compute “usefulness score”**
Combine novelty, format adherence, and test realism into a single score.

5) **Batch analysis**
Compare multiple models with the same grid; plot the “cliff step” for each.

6) **External evaluation (ChatGPT API)**
Feed the raw generated text to ChatGPT’s API for richer, model‑assisted analysis of tone, structure, and writing patterns.  
This adds a second‑opinion evaluator that can detect subtle shifts humans might miss.

### How the API will detect nuances (planned)
We’ll use OpenAI’s **Structured Outputs** so the evaluator must return a fixed JSON schema. This makes evaluation consistent and machine‑readable, and reduces schema drift compared to JSON mode.  
We’ll ask it to score and justify **specific signals** such as:
- **Tone shifts** (e.g., confident → hedged → evasive)
- **Structural drift** (missing required sections, less organized outputs)
- **Novelty vs boilerplate** (does it add new content or repeat templates?)
- **Test quality** (are tests meaningful or placeholder?)
- **Contradictions** (new feature conflicts with earlier spec summary)
- **Placeholders/hand‑waving** (e.g., “implement as needed,” “assume X”)

### Example evaluation schema (to send to ChatGPT)
We’ll pass the generated response + spec summary and require JSON:
```
{
  "tone": {
    "primary": "confident|neutral|hedged|evasive",
    "notes": "short justification"
  },
  "structure": {
    "format_ok": true,
    "missing_sections": ["Feature", "Test"]
  },
  "novelty": {
    "score": 0.0,
    "notes": "what feels new vs repeated"
  },
  "usefulness": {
    "score": 0.0,
    "notes": "is this actionable or boilerplate?"
  },
  "contradictions": {
    "found": false,
    "examples": []
  },
  "placeholders": {
    "found": true,
    "examples": ["implement as needed"]
  }
}
```

This evaluator output becomes a **second layer of metrics** that we can compare across models.  
We’ll send it alongside our local metrics (novelty, repetition, truncation) to see when both lines agree that usefulness collapsed.

Implementation notes:
- Prefer `response_format: {type: "json_schema", ...}` when supported; it enforces schema adherence.  
- If we must use JSON mode (`json_object`), it only guarantees valid JSON, not schema adherence; we’ll validate and retry on mismatches.  
- Structured Outputs can return a `refusal` field when the model declines; we should log that as its own signal.

---

## Why This Design Works
The feature‑accretion task forces the model to **keep inventing new capabilities**.  
If it can’t, it either:
- repeats, or
- gets vague, or
- ignores the format, or
- truncates constantly.

These are exactly the signals we want to capture.



---
