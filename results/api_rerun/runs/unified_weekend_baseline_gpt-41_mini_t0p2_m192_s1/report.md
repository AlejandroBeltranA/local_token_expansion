# LTE Unified Report

- Overall recommendation: `retry`
- Records: 44 total, 20 benchmark, 24 stress, 0 errors

## Trigger Summary

### GPT-4.1 mini
- Recommendation: `retry`
- Rationale: budget or cap pressure trigger fired
- over_expansion: status=fired threshold=>=2 budget-tagged benchmark misses with ER>=1.25 or contract failure, or any max_tokens<=56 row with LORR=1 evidence={"bounded_lorr_failures": ["ledger_carry_forward_json"], "budget_control_failures": ["incident_brief_one_sentence"]} action=retry
- latency_cliff: status=clear threshold=API backends: hard trigger only when 2 of last 3 stress steps exceed latency gate (latency_ms>2500 after input_tokens>=1500) evidence={"backend_mode": "api-hard-only", "gated_latency_steps": [], "hard_trigger_last_three": false} action=retry
- near_cap_pressure: status=clear threshold=benchmark LORR mean across structured_contracts+failure_escalation >=0.20, or stress LORR=1 on any 2 steps within 5-step window evidence={"stress_window_hit": false, "structured_lorr_mean": 0} action=repair
- repetition_loop: status=clear threshold=stress RCS>=0.30 on 2 consecutive steps, or last 5 stress steps mean RCS>=0.22 evidence={"high_rcs_steps": [], "last_five_mean_rcs": 0.0, "two_consecutive": false} action=escalate
- context_decay: status=clear threshold=>=2 context_pressure benchmark contract failures, or gated stress failure dominated by repetition/near-cap reasons evidence={"context_benchmark_failures": ["ledger_carry_forward_json"], "dominant_gated_failure_reasons": [], "first_gated_failure_step": null, "stress_contract_break_steps": []} action=escalate
- persistent_failure: status=clear threshold=stress reaches 3 consecutive failed steps, or both failure_escalation benchmark cases fail contract evidence={"failure_escalation_contract_failures": [], "stress_reasons": [], "stress_step": null} action=abort

## Aggregated Generation Report

# LTE Report

- Records: 44 (generations: 44)
- Models: 1
- Approx token counting present: no

## Stress cliff (persistent failure)

- GPT-4.1 mini: cliff_reached=no step=23 reasons=[] context_fraction=0.0013

## Per-model summary

| model | ER(mean) | LORR(mean) | RCS(mean) | VD(mean, paired) |
| --- | ---: | ---: | ---: | ---: |
| GPT-4.1 mini | 0.2058 | 0.0227 | 0.0000 | 0.7576 |

## Per-suite breakdown

### adversarial_pressure — GPT-4.1 mini
- ER(mean): 0.2463
- RCS(mean): 0.0000

### bounded_determination — GPT-4.1 mini
- ER(mean): 0.2032
- RCS(mean): 0.0000

### core_conciseness — GPT-4.1 mini
- ER(mean): 0.3866
- RCS(mean): 0.0000

### long_context_stability — GPT-4.1 mini
- ER(mean): 0.3068
- RCS(mean): 0.0000

### persistent_failure_probe — GPT-4.1 mini
- ER(mean): 0.5484
- RCS(mean): 0.0000

### stress — GPT-4.1 mini
- ER(mean): 0.0868
- RCS(mean): 0.0000

### structured_extraction — GPT-4.1 mini
- ER(mean): 0.4380
- RCS(mean): 0.0000

## Worst prompts (by metric)

- RCS=0.0000 model=GPT-4.1 mini suite=core_conciseness prompt_id=incident_brief_one_sentence
- RCS=0.0000 model=GPT-4.1 mini suite=core_conciseness prompt_id=policy_delta_two_bullets
- RCS=0.0000 model=GPT-4.1 mini suite=core_conciseness prompt_id=handoff_delta_concise
- RCS=0.0000 model=GPT-4.1 mini suite=core_conciseness prompt_id=handoff_delta_detailed
- RCS=0.0000 model=GPT-4.1 mini suite=structured_extraction prompt_id=extract_ticket_json

## Notes

- VD is computed using `output_tokens` for paired `variant: concise|detailed` cases with the same `pair_id`.
- If any records use approximate token counting, treat ER/LORR/VD as approximate as well.
