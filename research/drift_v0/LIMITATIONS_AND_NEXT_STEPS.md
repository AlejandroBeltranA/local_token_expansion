# Limitations and Next Steps

## 1) Limitations (Observed)
### Measured facts
- Primary failure rates remained high across all 45 conditions:
  - `E1`: `0.8889-1.0`
  - `E2`: `0.9-1.0`
  - `E3`: `0.925-1.0`
- E2/E3 retry effectiveness in reports was `0.0`, with escalation-after-retry `1.0`.
- E3 degradation deltas were small for most models (mean delta `~0.0099`, with one larger outlier family).
- Post-hoc failure causes were dominated by near-cap and non-extractable schema failures.

### Interpretation risks
- Strict evaluator behavior may conflate hard semantic failure with soft wrapper/compliance issues.
- Weak within-model variation may be due to prompt-contract rigidity, verifier harshness, model limits, or interaction effects.
- Current setup may under-separate context-stress effects between E2 and E3 for most families.

## 2) PI Concerns to Preserve
1. Breakage in chained workflows is the real deployment risk, not isolated output quality.
2. Strict contracts are useful for accountability but can hide meaningful behavior if no soft-failure channel exists.
3. Current weak variation should not be over-interpreted as "no effect" without redesign.
4. Human intervention thresholds must be explicit and ownership-mapped.

## 3) Next Iteration (Technical)
### A. Hard-vs-soft failure split (highest priority)
- Add dual-path validation:
  - hard failure: non-recoverable schema/semantic violations,
  - soft failure: wrapper/prose contamination with extractable payload.
- Report both rates in summaries and manifests.

### B. Recovery policy upgrade
- Keep current retry for comparability, but add one deterministic repair stage (e.g., strict reformatter).
- Optionally add a second-pass repair model for unresolved cases.
- Track marginal recovery gain per stage.

### C. Stress calibration
- Rebalance tasks and budget to reduce ceiling effects while preserving strictness.
- Revisit `max_tokens` and task verbosity to separate truncation from behavioral failure.
- Strengthen E3 stress gradient to increase discriminative value.

### D. Attribution and accountability metrics
- Add intervention ownership fields and decision provenance in report outputs.
- Define operational thresholds for escalate-to-human triggers.
- Report time-to-detection and unresolved-after-retry rates as first-class governance metrics.

### E. Targeted re-sweep design
- Run smaller targeted sweeps around top family(ies) and one weaker family under revised validators.
- Maintain reproducibility with identical artifact contracts and explicit versioning.

## 4) What We Should Not Claim Yet
### Measured boundary
- Current evidence supports detection/escalation feasibility and cross-family differentiation.

### Claims to avoid
- Do not claim robust autonomous recovery.
- Do not claim temperature/top-p effects are absent in general.
- Do not generalize this run to all task domains or agentic settings.

## 5) Reproducible AI-Assisted Workflow Notes
The implementation model (A: tasks, B: runtime/interventions, C: analysis, orchestrator audits) improved speed and traceability, but must remain contract-driven. Future iterations should keep the same boundary controls and add pre-registered evaluation changes before reruns.

## Handoff Note
### What I changed
- Consolidated observed limitations and next-step design into an actionable technical plan.
- Preserved PI doubts and accountability framing explicitly.
- Separated measured constraints from interpretation/hypothesis statements.

### Assumptions
- Existing failure-cause CSVs are representative of E2/E3 primary-turn behavior for this sweep.

### Open questions
- Should soft-failure extraction be integrated in evaluator stage or analysis stage first?
- Which recovery baseline should be mandatory in v2 (deterministic only vs deterministic + model-based)?
- What escalation threshold is acceptable for deployment piloting?
