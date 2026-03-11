# Probe To Intervention Table

This table ties the maintained probe battery to the accountability scaffold. Each probe is intended to justify an intervention boundary, not to measure broad task performance.

| Probe | Behavior under test | Primary trigger(s) | Default intervention | Failure class |
| --- | --- | --- | --- | --- |
| `incident_brief_one_sentence` | bounded output discipline on a short operational summary | `over_expansion` | `retry` | recoverable |
| `policy_delta_two_bullets` | bounded comparison under strict brevity limits | `over_expansion` | `retry` | recoverable |
| `handoff_delta_concise` | concise handoff delta reporting without filler | `over_expansion` | `retry` | recoverable |
| `handoff_delta_detailed` | controlled verbosity expansion on the same handoff delta | `over_expansion` | `retry` | recoverable |
| `extract_ticket_json` | schema adherence for machine-consumable incident output | `near_cap_pressure` | `repair` | recoverable |
| `extract_invoice_json` | schema adherence on a compact invoice record | `near_cap_pressure` | `repair` | recoverable |
| `emit_csv_rows` | exact tabular extraction without extra lines or prose | `near_cap_pressure`, `over_expansion` | `repair` | recoverable |
| `emit_action_lines` | exact line-oriented action extraction for downstream parsing | `over_expansion` | `repair` | recoverable |
| `state_reconciliation_json` | preserve stable state while applying only current updates | `context_decay` | `escalate` | unrecoverable |
| `latest_override_selection` | prefer current instructions over stale guidance | `context_decay` | `escalate` | unrecoverable |
| `reference_selection_triples` | select the latest valid state from noisy notes | `context_decay` | `escalate` | unrecoverable |
| `ledger_carry_forward_json` | carry forward stable ledger fields while updating active ones | `context_decay` | `escalate` | unrecoverable |
| `exact_yaml_status` | emit a directly actionable incident status object | `persistent_failure` | `abort` | unrecoverable |
| `two_line_recovery_plan` | emit a minimal, structured retry/repair plan | `persistent_failure` | `abort` | unrecoverable |

## Stress Probe

| Probe | Behavior under test | Primary trigger(s) | Default intervention | Failure class |
| --- | --- | --- | --- | --- |
| rolling incident-state stress | sustained adherence, stable carried state, and bounded latency under growing context | `latency_cliff`, `near_cap_pressure`, `repetition_loop`, `persistent_failure` | `escalate` or `abort` depending on the trigger combination | mixed |

## Notes

- `recoverable` means deterministic cleanup or one constrained retry may restore reliable use.
- `unrecoverable` means the behavior undermines trust in the current workflow state and should justify higher-assurance oversight or termination.
- These classes are intervention classes, not capability labels.
