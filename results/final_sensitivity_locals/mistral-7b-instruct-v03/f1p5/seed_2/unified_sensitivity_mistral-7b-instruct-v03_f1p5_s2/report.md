# LTE Unified Report

- Overall recommendation: `retry`
- Records: 42 total, 20 benchmark, 22 stress, 0 errors

## Trigger Summary

### Mistral-7B-Instruct-v0.3
- Recommendation: `retry`
- Rationale: budget or cap pressure trigger fired
- over_expansion: status=fired threshold=>=2 budget-tagged benchmark misses with ER>=1.25 or contract failure, or any max_tokens<=56 row with LORR=1 evidence={"bounded_lorr_failures": ["policy_delta_two_bullets", "ledger_carry_forward_json"], "budget_control_failures": ["incident_brief_one_sentence", "policy_delta_two_bullets"]} action=retry
- latency_cliff: status=clear threshold=stress latency_ms>3750 after input_tokens>=2250; hard trigger if 2 of last 3 stress steps exceed it evidence={"backend_mode": "local-any-gated", "gated_latency_steps": [], "hard_trigger_last_three": false} action=retry
- near_cap_pressure: status=clear threshold=benchmark LORR mean across structured_contracts+failure_escalation >=0.30000000000000004, or stress LORR=1 on any 3 steps within 8-step window evidence={"stress_window_hit": false, "structured_lorr_mean": 0} action=repair
- repetition_loop: status=clear threshold=stress RCS>=0.44999999999999996 on 2 consecutive steps, or last 5 stress steps mean RCS>=0.33 evidence={"high_rcs_steps": [], "last_five_mean_rcs": 0.0, "two_consecutive": false} action=escalate
- context_decay: status=clear threshold=>=2 context_pressure benchmark contract failures, or gated stress failure dominated by repetition/near-cap reasons evidence={"context_benchmark_failures": ["ledger_carry_forward_json"], "dominant_gated_failure_reasons": [], "first_gated_failure_step": null, "stress_contract_break_steps": [0, 1, 2, 3, 4]} action=escalate
- persistent_failure: status=clear threshold=stress reaches 4 consecutive failed steps, or both failure_escalation benchmark cases fail contract evidence={"failure_escalation_contract_failures": [], "stress_reasons": [], "stress_step": null} action=abort

## Aggregated Generation Report

# LTE Report

- Records: 42 (generations: 42)
- Models: 1
- Approx token counting present: no

## Stress cliff (persistent failure)

- Mistral-7B-Instruct-v0.3: cliff_reached=no step=21 reasons=[] context_fraction=0.2504

## Per-model summary

| model | ER(mean) | LORR(mean) | RCS(mean) | VD(mean, paired) |
| --- | ---: | ---: | ---: | ---: |
| Mistral-7B-Instruct-v0.3 | 0.2740 | 0.0952 | 0.0000 | 0.6349 |

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
- ER(mean): 0.1146
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
