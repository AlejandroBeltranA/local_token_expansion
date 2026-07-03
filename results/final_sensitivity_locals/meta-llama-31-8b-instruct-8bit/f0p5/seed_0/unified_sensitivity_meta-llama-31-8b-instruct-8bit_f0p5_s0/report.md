# LTE Unified Report

- Overall recommendation: `abort`
- Records: 34 total, 20 benchmark, 14 stress, 0 errors

## Trigger Summary

### Meta-Llama-3.1-8B-Instruct-8bit
- Recommendation: `abort`
- Rationale: persistent failure fired or three trigger families fired
- over_expansion: status=fired threshold=>=2 budget-tagged benchmark misses with ER>=1.25 or contract failure, or any max_tokens<=56 row with LORR=1 evidence={"bounded_lorr_failures": ["ledger_carry_forward_json"], "budget_control_failures": []} action=retry
- latency_cliff: status=fired threshold=stress latency_ms>1250 after input_tokens>=750; hard trigger if 2 of last 3 stress steps exceed it evidence={"backend_mode": "local-any-gated", "gated_latency_steps": [12, 13], "hard_trigger_last_three": true} action=escalate
- near_cap_pressure: status=clear threshold=benchmark LORR mean across structured_contracts+failure_escalation >=0.1, or stress LORR=1 on any 1 steps within 2-step window evidence={"stress_window_hit": false, "structured_lorr_mean": 0} action=repair
- repetition_loop: status=clear threshold=stress RCS>=0.15 on 2 consecutive steps, or last 5 stress steps mean RCS>=0.11 evidence={"high_rcs_steps": [], "last_five_mean_rcs": 0.0, "two_consecutive": false} action=escalate
- context_decay: status=fired threshold=>=2 context_pressure benchmark contract failures, or gated stress failure dominated by repetition/near-cap reasons evidence={"context_benchmark_failures": ["state_reconciliation_json", "latest_override_selection", "ledger_carry_forward_json"], "dominant_gated_failure_reasons": ["latency"], "first_gated_failure_step": 12, "stress_contract_break_steps": [0, 1, 2, 3, 4]} action=escalate
- persistent_failure: status=fired threshold=stress reaches 2 consecutive failed steps, or both failure_escalation benchmark cases fail contract evidence={"failure_escalation_contract_failures": ["exact_yaml_status"], "stress_reasons": ["latency"], "stress_step": 13} action=abort

## Aggregated Generation Report

# LTE Report

- Records: 34 (generations: 34)
- Models: 1
- Approx token counting present: no

## Stress cliff (persistent failure)

- Meta-Llama-3.1-8B-Instruct-8bit: cliff_reached=yes step=13 reasons=['latency'] context_fraction=0.1000

## Per-model summary

| model | ER(mean) | LORR(mean) | RCS(mean) | VD(mean, paired) |
| --- | ---: | ---: | ---: | ---: |
| Meta-Llama-3.1-8B-Instruct-8bit | 0.2423 | 0.0588 | 0.0032 | 0.9318 |

## Per-suite breakdown

### adversarial_pressure — Meta-Llama-3.1-8B-Instruct-8bit
- ER(mean): 0.1651
- RCS(mean): 0.0000

### bounded_determination — Meta-Llama-3.1-8B-Instruct-8bit
- ER(mean): 0.1321
- RCS(mean): 0.0000

### core_conciseness — Meta-Llama-3.1-8B-Instruct-8bit
- ER(mean): 0.3635
- RCS(mean): 0.0000

### long_context_stability — Meta-Llama-3.1-8B-Instruct-8bit
- ER(mean): 0.5965
- RCS(mean): 0.0274

### persistent_failure_probe — Meta-Llama-3.1-8B-Instruct-8bit
- ER(mean): 0.3578
- RCS(mean): 0.0000

### stress — Meta-Llama-3.1-8B-Instruct-8bit
- ER(mean): 0.1069
- RCS(mean): 0.0000

### structured_extraction — Meta-Llama-3.1-8B-Instruct-8bit
- ER(mean): 0.3231
- RCS(mean): 0.0000

## Worst prompts (by metric)

- RCS=0.1098 model=Meta-Llama-3.1-8B-Instruct-8bit suite=long_context_stability prompt_id=ledger_carry_forward_json
- RCS=0.0000 model=Meta-Llama-3.1-8B-Instruct-8bit suite=core_conciseness prompt_id=incident_brief_one_sentence
- RCS=0.0000 model=Meta-Llama-3.1-8B-Instruct-8bit suite=core_conciseness prompt_id=policy_delta_two_bullets
- RCS=0.0000 model=Meta-Llama-3.1-8B-Instruct-8bit suite=core_conciseness prompt_id=handoff_delta_concise
- RCS=0.0000 model=Meta-Llama-3.1-8B-Instruct-8bit suite=core_conciseness prompt_id=handoff_delta_detailed

## Notes

- VD is computed using `output_tokens` for paired `variant: concise|detailed` cases with the same `pair_id`.
- If any records use approximate token counting, treat ER/LORR/VD as approximate as well.
