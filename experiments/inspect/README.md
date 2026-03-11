# Inspect Spike

This directory is for a contained Inspect framework prototype.

The goal is not to replace LTE. The goal is to test whether Inspect is useful as an optional orchestration, scoring, logging, and early-stopping layer for local reliability evaluation.

## Initial Scope

The first prototype should:

- evaluate one small LTE task,
- run on one local model or mock backend,
- log at least one custom reliability scorer,
- demonstrate one early-stopping rule,
- produce Inspect-native logs that can be compared against current LTE outputs.

## Recommended First Target

Use the `structured_extraction` task surface first.

Reason:

- the task is narrow,
- parseability criteria are explicit,
- it exercises structured reliability rather than open-ended text generation,
- it avoids prematurely porting the full rolling-context stress logic.

## Success Criteria

The spike is worth continuing only if it shows that Inspect adds clear value in at least one of:

- better task abstraction,
- better logging and replay,
- cleaner scorer composition,
- useful early stopping for persistent failure.

If it does not add clear value, keep it isolated and do not let it distort the core LTE codebase.

## Current Scaffold

The initial scaffold is now present:

- [structured_extraction_eval.py](structured_extraction_eval.py)
- [scorers.py](scorers.py)
- [datasets/structured_extraction.jsonl](datasets/structured_extraction.jsonl)

This is intentionally minimal. It is a spike for task/scorer/log structure, not a replacement runtime.

## Running It

With Inspect installed, the intended starting point is:

```bash
inspect eval experiments/inspect/structured_extraction_eval.py
```

The next real decision should come from inspecting the resulting logs and deciding whether the logging and early-stopping affordances are worth the dependency.
