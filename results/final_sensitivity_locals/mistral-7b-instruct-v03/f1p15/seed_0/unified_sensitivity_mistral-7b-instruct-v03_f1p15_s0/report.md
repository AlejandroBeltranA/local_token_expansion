# LTE Unified Report

- Overall recommendation: `abort`
- Records: 41 total, 20 benchmark, 21 stress, 0 errors

## Trigger Summary

### Mistral-7B-Instruct-v0.3
- Recommendation: `abort`
- Rationale: persistent failure fired or three trigger families fired
- over_expansion: status=fired threshold=>=2 budget-tagged benchmark misses with ER>=1.25 or contract failure, or any max_tokens<=56 row with LORR=1 evidence={"bounded_lorr_failures": ["policy_delta_two_bullets", "ledger_carry_forward_json"], "budget_control_failures": ["incident_brief_one_sentence", "policy_delta_two_bullets"]} action=retry
- latency_cliff: status=fired threshold=stress latency_ms>2875 after input_tokens>=1725; hard trigger if 2 of last 3 stress steps exceed it evidence={"backend_mode": "local-any-gated", "gated_latency_steps": [18, 19, 20], "hard_trigger_last_three": true} action=escalate
- near_cap_pressure: status=clear threshold=benchmark LORR mean across structured_contracts+failure_escalation >=0.22999999999999998, or stress LORR=1 on any 2 steps within 6-step window evidence={"stress_window_hit": false, "structured_lorr_mean": 0} action=repair
- repetition_loop: status=clear threshold=stress RCS>=0.345 on 2 consecutive steps, or last 5 stress steps mean RCS>=0.253 evidence={"high_rcs_steps": [], "last_five_mean_rcs": 0.0, "two_consecutive": false} action=escalate
- context_decay: status=clear threshold=>=2 context_pressure benchmark contract failures, or gated stress failure dominated by repetition/near-cap reasons evidence={"context_benchmark_failures": ["ledger_carry_forward_json"], "dominant_gated_failure_reasons": ["latency"], "first_gated_failure_step": 18, "stress_contract_break_steps": [0, 1, 2, 3, 4]} action=escalate
- persistent_failure: status=fired threshold=stress reaches 3 consecutive failed steps, or both failure_escalation benchmark cases fail contract evidence={"failure_escalation_contract_failures": [], "stress_reasons": ["latency"], "stress_step": 20} action=abort

## Aggregated Generation Report

# LTE Report

- Records: 41 (generations: 41)
- Models: 1
- Approx token counting present: no

## Stress cliff (persistent failure)

- Mistral-7B-Instruct-v0.3: cliff_reached=yes step=20 reasons=['latency'] context_fraction=0.2397

## Per-model summary

| model | ER(mean) | LORR(mean) | RCS(mean) | VD(mean, paired) |
| --- | ---: | ---: | ---: | ---: |
| Mistral-7B-Instruct-v0.3 | 0.2797 | 0.0976 | 0.0000 | 0.6349 |

## Per-suite breakdown

### adversarial_pressure — Mistral-7B-Instruct-v0.3
- ER(mean): 0.2939
- RCS(mean): 0.0000

### bounded_determination — Mistral-7B-Instruct-v0.3
- ER(mean): 0.3266
- RCS(mean): 0.0000

### core_conciseness — Mistral-7B-Instruct-v0.3
- ER(mean): 0.6229
- RCS(mean): 0.0000

### long_context_stability — Mistral-7B-Instruct-v0.3
- ER(mean): 0.3784
- RCS(mean): 0.0000

### persistent_failure_probe — Mistral-7B-Instruct-v0.3
- ER(mean): 0.6020
- RCS(mean): 0.0000

### stress — Mistral-7B-Instruct-v0.3
- ER(mean): 0.1181
- RCS(mean): 0.0000

### structured_extraction — Mistral-7B-Instruct-v0.3
- ER(mean): 0.4792
- RCS(mean): 0.0000

## Worst prompts (by metric)

- RCS=0.0000 model=Mistral-7B-Instruct-v0.3 suite=core_conciseness prompt_id=incident_brief_one_sentence
- RCS=0.0000 model=Mistral-7B-Instruct-v0.3 suite=core_conciseness prompt_id=policy_delta_two_bullets
- RCS=0.0000 model=Mistral-7B-Instruct-v0.3 suite=core_conciseness prompt_id=handoff_delta_concise
- RCS=0.0000 model=Mistral-7B-Instruct-v0.3 suite=core_conciseness prompt_id=handoff_delta_detailed
- RCS=0.0000 model=Mistral-7B-Instruct-v0.3 suite=structured_extraction prompt_id=extract_ticket_json

## Notes

- VD is computed using `output_tokens` for paired `variant: concise|detailed` cases with the same `pair_id`.
- If any records use approximate token counting, treat ER/LORR/VD as approximate as well.
