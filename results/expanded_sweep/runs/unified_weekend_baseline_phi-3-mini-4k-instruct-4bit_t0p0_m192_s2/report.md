# LTE Unified Report

- Overall recommendation: `abort`
- Records: 32 total, 14 benchmark, 18 stress, 0 errors

## Trigger Summary

### Phi-3-mini-4k-instruct-4bit
- Recommendation: `abort`
- Rationale: persistent failure fired or three trigger families fired
- over_expansion: status=fired threshold=>=2 budget-tagged benchmark misses with ER>=1.25 or contract failure, or any max_tokens<=56 row with LORR=1 evidence={"bounded_lorr_failures": ["ledger_carry_forward_json"], "budget_control_failures": ["incident_brief_one_sentence", "policy_delta_two_bullets"]} action=retry
- latency_cliff: status=fired threshold=stress latency_ms>2500 after input_tokens>=1500; hard trigger if 2 of last 3 stress steps exceed it evidence={"backend_mode": "local-any-gated", "gated_latency_steps": [15, 16, 17], "hard_trigger_last_three": true} action=escalate
- near_cap_pressure: status=fired threshold=benchmark LORR mean across structured_contracts+failure_escalation >=0.20, or stress LORR=1 on any 2 steps within 5-step window evidence={"stress_window_hit": true, "structured_lorr_mean": 0.5} action=repair
- repetition_loop: status=clear threshold=stress RCS>=0.30 on 2 consecutive steps, or last 5 stress steps mean RCS>=0.22 evidence={"high_rcs_steps": [], "last_five_mean_rcs": 0.0, "two_consecutive": false} action=escalate
- context_decay: status=fired threshold=>=2 context_pressure benchmark contract failures, or gated stress failure dominated by repetition/near-cap reasons evidence={"context_benchmark_failures": ["state_reconciliation_json", "ledger_carry_forward_json"], "dominant_gated_failure_reasons": ["latency"], "first_gated_failure_step": 15, "stress_contract_break_steps": [0, 1, 2, 3, 4]} action=escalate
- persistent_failure: status=fired threshold=stress reaches 3 consecutive failed steps, or both failure_escalation benchmark cases fail contract evidence={"failure_escalation_contract_failures": ["exact_yaml_status"], "stress_reasons": ["latency"], "stress_step": 17} action=abort

## Aggregated Generation Report

# LTE Report

- Records: 32 (generations: 32)
- Models: 1
- Approx token counting present: no

## Stress cliff (persistent failure)

- Phi-3-mini-4k-instruct-4bit: cliff_reached=yes step=17 reasons=['latency'] context_fraction=0.3958

## Per-model summary

| model | ER(mean) | LORR(mean) | RCS(mean) | VD(mean, paired) |
| --- | ---: | ---: | ---: | ---: |
| Phi-3-mini-4k-instruct-4bit | 0.5492 | 0.2188 | 0.0075 | 0.6863 |

## Per-suite breakdown

### core_conciseness — Phi-3-mini-4k-instruct-4bit
- ER(mean): 0.4418
- RCS(mean): 0.0000

### long_context_stability — Phi-3-mini-4k-instruct-4bit
- ER(mean): 0.7137
- RCS(mean): 0.0475

### persistent_failure_probe — Phi-3-mini-4k-instruct-4bit
- ER(mean): 2.2586
- RCS(mean): 0.0000

### stress — Phi-3-mini-4k-instruct-4bit
- ER(mean): 0.1518
- RCS(mean): 0.0023

### structured_extraction — Phi-3-mini-4k-instruct-4bit
- ER(mean): 1.4260
- RCS(mean): 0.0023

## Worst prompts (by metric)

- RCS=0.1053 model=Phi-3-mini-4k-instruct-4bit suite=long_context_stability prompt_id=ledger_carry_forward_json
- RCS=0.0847 model=Phi-3-mini-4k-instruct-4bit suite=long_context_stability prompt_id=latest_override_selection
- RCS=0.0327 model=Phi-3-mini-4k-instruct-4bit suite=stress prompt_id=step_0000
- RCS=0.0093 model=Phi-3-mini-4k-instruct-4bit suite=structured_extraction prompt_id=extract_ticket_json
- RCS=0.0081 model=Phi-3-mini-4k-instruct-4bit suite=stress prompt_id=step_0001

## Notes

- VD is computed using `output_tokens` for paired `variant: concise|detailed` cases with the same `pair_id`.
- If any records use approximate token counting, treat ER/LORR/VD as approximate as well.
