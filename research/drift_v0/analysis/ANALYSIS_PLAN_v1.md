# ANALYSIS_PLAN_v1

## Scope
Convert evaluated `drift_v0` logs (`evaluate_events.py` output) into paper-ready evidence for failure detection and accountability.

## Input Contract
Per-turn evaluated JSONL rows with protocol fields:
- identifiers: `run_id`, `experiment_id`, `task_id`, `model`, `seed`, `turn`
- triggers: `schema_failure`, `repetition_loop`, `state_contradiction`
- policy: `intervention_action`, `recovered`, `escalated` (legacy evaluated logs may omit `recovered`)
- closed-loop runtime fields (when produced by `run_experiments.py`): `attempt_kind`, `parent_turn`, `policy_applied`

Legacy-log fallback: when `recovered` is missing, recovery outcome is inferred from the next turn in the same episode (next turn has no trigger => recovered).

## Metric Definitions

### 1) Failure Rate
Primary (turn-level):
- `turn_failure_rate(exp) = failed_turns(exp) / total_turns(exp)`
- A failed turn has any trigger true.

Secondary (episode-level accountability view):
- `episode_failure_rate(exp) = episodes_with_any_failure(exp) / total_episodes(exp)`

### 2) First-Failure Turn (E2/E3)
For each episode with at least one failed turn:
- `first_failure_turn = min(turn where any trigger is true)`

Report per experiment:
- `N failed episodes`, `mean`, `median`, `p25`, `p75`.

### 3) Recovery Success
A recovery attempt is a turn with `intervention_action` starting `retry_`.

Success rule:
- If `recovered` exists: use it directly.
- Else infer from next turn in episode: no trigger on next turn => success.

Report:
- `attempts_total`, `attempts_evaluable`, `success_total`, `recovery_success_rate = success_total / attempts_evaluable`.

### 4) Escalation Rate
Turn-level:
- `escalation_turn_rate(exp) = escalated_turns(exp) / total_turns(exp)`

Episode-level:
- `escalation_episode_rate(exp) = escalated_episodes(exp) / total_episodes(exp)`

### 5) Closed-Loop Primary vs Retry Outcomes
Primary-turn failure (closed-loop):
- `primary_failure_rate(exp) = failed_primary_rows(exp) / primary_rows(exp)`
- primary rows are `attempt_kind=primary` (or legacy rows with missing `attempt_kind`).

Retry effectiveness:
- `retry_effectiveness_rate(exp) = successful_retry_rows(exp) / retry_rows(exp)`
- retry rows are `attempt_kind=retry`.
- success uses `recovered` when present; fallback is no trigger on retry row.

Escalation-after-retry:
- `escalation_after_retry_rate(exp) = escalated_retry_rows(exp) / retry_rows(exp)`

### 6) E3 Degradation Delta
For E3 context conditions `1k` and `4k`:
- `delta(metric) = metric_4k - metric_1k`

Planned delta metrics:
- `turn_failure_rate`
- `escalation_episode_rate`
- `recovery_success_rate`
- `first_failure_turn_mean`

## Expected Paper Tables

### Table 1. Failure and escalation by experiment
Columns:
- `Experiment`, `Turns`, `Episodes`, `Failed Turns`, `Turn Failure Rate`, `Failed Episodes`, `Episode Failure Rate`, `Escalated Episodes`, `Escalation Episode Rate`, `Recovery Success Rate`

### Table 2. Trigger-specific failure rates
Columns:
- `Experiment`, `Trigger`, `Count`, `Rate per Turn`

### Table 3. First-failure turn distribution (E2/E3)
Columns:
- `Experiment`, `N Failed Episodes`, `Mean`, `Median`, `P25`, `P75`

### Table 4. E3 degradation delta
Columns:
- `Metric`, `1k`, `4k`, `Delta (4k-1k)`

### Table 5. Retry effectiveness and escalation-after-retry
Columns:
- `Experiment`, `Primary Turns`, `Primary Failures`, `Primary Failure Rate`, `Retries Attempted`, `Retries Success`, `Retry Effectiveness`, `Retry Escalations`, `Escalation-After-Retry Rate`

## Expected Figures
- Figure 1: Grouped bar chart of trigger rates by experiment (from Table 2).
- Figure 2: Box/violin of first-failure turn for E2 vs E3 conditions.
- Figure 3: Delta plot (`4k-1k`) for E3 metrics.

## Output Artifacts (from summarize.py)
- `report.md` (paper-ready tables)
- `metrics_summary.json` (machine-readable source of truth)
- `failure_escalation_by_experiment.csv`
- `trigger_failure_by_experiment.csv`
- `first_failure_turn_distribution.csv`
- `e3_degradation_delta.csv`
- `retry_effectiveness_by_experiment.csv`

## Backward Compatibility
- Existing summary tables and JSON keys are preserved.
- New closed-loop metrics are additive and do not remove prior metrics.

## Validation Commands

```bash
python research/drift_v0/runner/evaluate_events.py \
  --input research/drift_v0/examples/events_sample.jsonl \
  --output /tmp/drift_v0_evaluated_sample.jsonl

python research/drift_v0/analysis/summarize.py \
  --input /tmp/drift_v0_evaluated_sample.jsonl \
  --output-dir /tmp/drift_v0_analysis_sample
```

Expected result: markdown summary printed to stdout and all artifacts written under `/tmp/drift_v0_analysis_sample`.
