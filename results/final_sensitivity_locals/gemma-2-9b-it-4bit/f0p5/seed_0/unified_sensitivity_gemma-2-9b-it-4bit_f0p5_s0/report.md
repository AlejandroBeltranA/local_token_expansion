# LTE Unified Report

- Overall recommendation: `abort`
- Records: 38 total, 20 benchmark, 18 stress, 0 errors

## Trigger Summary

### Gemma-2-9b-it-4bit
- Recommendation: `abort`
- Rationale: persistent failure fired or three trigger families fired
- over_expansion: status=fired threshold=>=2 budget-tagged benchmark misses with ER>=1.25 or contract failure, or any max_tokens<=56 row with LORR=1 evidence={"bounded_lorr_failures": ["ledger_carry_forward_json"], "budget_control_failures": ["incident_brief_one_sentence", "policy_delta_two_bullets"]} action=retry
- latency_cliff: status=fired threshold=stress latency_ms>1250 after input_tokens>=750; hard trigger if 2 of last 3 stress steps exceed it evidence={"backend_mode": "local-any-gated", "gated_latency_steps": [16, 17], "hard_trigger_last_three": true} action=escalate
- near_cap_pressure: status=fired threshold=benchmark LORR mean across structured_contracts+failure_escalation >=0.1, or stress LORR=1 on any 1 steps within 2-step window evidence={"stress_window_hit": false, "structured_lorr_mean": 0.166667} action=repair
- repetition_loop: status=clear threshold=stress RCS>=0.15 on 2 consecutive steps, or last 5 stress steps mean RCS>=0.11 evidence={"high_rcs_steps": [], "last_five_mean_rcs": 0.0, "two_consecutive": false} action=escalate
- context_decay: status=fired threshold=>=2 context_pressure benchmark contract failures, or gated stress failure dominated by repetition/near-cap reasons evidence={"context_benchmark_failures": ["state_reconciliation_json", "latest_override_selection", "reference_selection_triples", "ledger_carry_forward_json"], "dominant_gated_failure_reasons": ["latency"], "first_gated_failure_step": 16, "stress_contract_break_steps": [0, 13, 14, 15, 16]} action=escalate
- persistent_failure: status=fired threshold=stress reaches 2 consecutive failed steps, or both failure_escalation benchmark cases fail contract evidence={"failure_escalation_contract_failures": ["exact_yaml_status", "two_line_recovery_plan"], "stress_reasons": ["latency"], "stress_step": 17} action=abort

## Aggregated Generation Report

# LTE Report

- Records: 38 (generations: 38)
- Models: 1
- Approx token counting present: no

## Stress cliff (persistent failure)

- Gemma-2-9b-it-4bit: cliff_reached=yes step=17 reasons=['latency'] context_fraction=0.0962

## Per-model summary

| model | ER(mean) | LORR(mean) | RCS(mean) | VD(mean, paired) |
| --- | ---: | ---: | ---: | ---: |
| Gemma-2-9b-it-4bit | 0.3444 | 0.1316 | 0.0255 | 1.1818 |

## Per-suite breakdown

### adversarial_pressure — Gemma-2-9b-it-4bit
- ER(mean): 1.2267
- RCS(mean): 0.2432

### bounded_determination — Gemma-2-9b-it-4bit
- ER(mean): 0.4652
- RCS(mean): 0.0179

### core_conciseness — Gemma-2-9b-it-4bit
- ER(mean): 0.2811
- RCS(mean): 0.0312

### long_context_stability — Gemma-2-9b-it-4bit
- ER(mean): 0.3712
- RCS(mean): 0.0000

### persistent_failure_probe — Gemma-2-9b-it-4bit
- ER(mean): 0.5035
- RCS(mean): 0.0000

### stress — Gemma-2-9b-it-4bit
- ER(mean): 0.0813
- RCS(mean): 0.0000

### structured_extraction — Gemma-2-9b-it-4bit
- ER(mean): 0.7325
- RCS(mean): 0.0149

## Worst prompts (by metric)

- RCS=0.7095 model=Gemma-2-9b-it-4bit suite=adversarial_pressure prompt_id=injected_override_ignore
- RCS=0.1250 model=Gemma-2-9b-it-4bit suite=core_conciseness prompt_id=policy_delta_two_bullets
- RCS=0.0597 model=Gemma-2-9b-it-4bit suite=structured_extraction prompt_id=emit_action_lines
- RCS=0.0536 model=Gemma-2-9b-it-4bit suite=bounded_determination prompt_id=abort_threshold_lines
- RCS=0.0200 model=Gemma-2-9b-it-4bit suite=adversarial_pressure prompt_id=contradictory_owner_injection

## Notes

- VD is computed using `output_tokens` for paired `variant: concise|detailed` cases with the same `pair_id`.
- If any records use approximate token counting, treat ER/LORR/VD as approximate as well.
