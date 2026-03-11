# Figure and Table Plan (from Existing Artifacts Only)

## Artifact Inputs
- `/tmp/drift_v0_sweep/sweep_manifest.csv`
- `/tmp/drift_v0_sweep/<condition_id>/report/metrics_summary.json`
- `/tmp/drift_v0_failure_cause_by_model.csv`
- `/tmp/drift_v0_failure_cause_overall.csv`

## Figure 1: Primary Failure Rates by Model Family
- **Type:** grouped bar chart
- **Source:** `sweep_manifest.csv`
- **Fields:** `model_name`, `e1_primary_failure_rate`, `e2_primary_failure_rate`, `e3_primary_failure_rate`
- **Measured fact to show:** family-level means and high-failure regime ranges.
- **Interpretation to support:** cross-family variation exceeds within-family decoding variation in this run.

## Figure 2: E3 Context Delta (`4k - 1k`) by Model Family
- **Type:** bar chart with zero baseline
- **Source:** `sweep_manifest.csv`
- **Field:** `e3_delta_turn_failure_rate`
- **Measured fact to show:** near-zero deltas for most families; one notable positive delta for Phi-3-mini.
- **Interpretation to support:** weak E2/E3 separability under current stress design.

## Figure 3: Failure Taxonomy Composition
- **Type:** stacked bar chart by model
- **Source:** `drift_v0_failure_cause_by_model.csv`
- **Fields:** `schema_non_extractable`, `schema_extractable`, `repetition_only`, `near_cap`
- **Measured fact to show:** dominant near-cap and non-extractable schema failures.
- **Interpretation to support:** contractability and budget pressure are key contributors.

## Figure 4: Intervention Outcome Funnel
- **Type:** flow/funnel diagram
- **Source:** per-condition `metrics_summary.json` (`closed_loop_primary_vs_retry`)
- **Fields:** `primary_failures`, `retries_attempted`, `retries_success`, `retries_escalated`
- **Measured fact to show:** retries attempted but no observed recovery; escalation-after-retry at 1.0.
- **Interpretation to support:** intervention is currently detection/escalation-heavy, not recovery-effective.

## Table 1: Sweep Design and Coverage
- **Source:** `sweep_manifest.csv`
- **Content:** model list, temperature values, top-p values, total conditions (`45`).
- **Role:** reproducibility and scope clarity.

## Table 2: Per-Model Summary Metrics
- **Source:** `sweep_manifest.csv`
- **Content:** mean E1/E2/E3 failure rates and composite.
- **Role:** compact empirical ranking and cross-family comparison.

## Table 3: Best-Observed Conditions
- **Source:** `sweep_manifest.csv`
- **Content:** top-N conditions by composite score with model, temperature, top-p.
- **Role:** identify best observed operating region and stability across decoding settings.

## Table 4: Intervention Effectiveness Summary
- **Source:** per-condition `metrics_summary.json`
- **Content:** E2/E3 retry effectiveness and escalation-after-retry distributions.
- **Role:** transparent reporting of weak recovery outcomes.

## Table 5: Failure Cause Summary (Overall and by Model)
- **Source:** failure-cause CSV artifacts
- **Content:** failed rows, near-cap share, non-extractable share, extractable share, repetition-only counts.
- **Role:** hard-vs-soft failure discussion support.

## Notes on Facts vs Interpretation
- **Measured facts:** numeric values directly computed from listed artifacts.
- **Interpretation:** causal/mechanistic claims (e.g., prompt rigidity vs model weakness) must be labeled as hypotheses, not established conclusions.

## Handoff Note
### What I changed
- Produced a publication-oriented figure/table plan mapped to concrete artifact paths and fields.
- Added intended interpretation role per visual/table while preserving fact/interpretation separation.

### Assumptions
- Per-condition report JSON structure is stable across all 45 conditions.

### Open questions
- Should Figure 4 be included in main paper or appendix if space-constrained?
