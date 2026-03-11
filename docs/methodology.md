# LTE Methodology

## Why token expansion matters
Local models can “run long” even when you think you’ve constrained them. In practice this shows up as:
- drifting verbosity (answers get longer or more repetitive over time),
- runaway continuations (repeated phrases / looping),
- and higher truncation pressure (hitting `max_tokens` more often).

LTE is a small benchmark harness that makes these behaviors measurable and comparable across local MLX models.

## What LTE measures
LTE records per-prompt generations and computes:
- Expansion Ratio (ER): `output_tokens / max(1, input_tokens)`
- Length Overrun Rate (LORR): `1` if `output_tokens >= 0.95 * max_tokens` else `0`
- Verbosity Drift (VD): paired concise vs detailed prompts
- Runaway Continuation Score (RCS): 4-gram repetition fraction over output text

## What LTE does not measure
- “Truthfulness” or factual accuracy
- Safety or policy compliance
- Semantic task quality (unless you add task-specific checks)

LTE is intentionally lightweight: it focuses on length dynamics, repetition, and constraint pressure.

