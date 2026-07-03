# LTE Unified Report

- Overall recommendation: `retry`
- Records: 44 total, 20 benchmark, 24 stress, 0 errors

## Trigger Summary

### Phi-4-mini-instruct-8bit
- Recommendation: `retry`
- Rationale: budget or cap pressure trigger fired
- over_expansion: status=fired threshold=>=2 budget-tagged benchmark misses with ER>=1.25 or contract failure, or any max_tokens<=56 row with LORR=1 evidence={"bounded_lorr_failures": ["ledger_carry_forward_json"], "budget_control_failures": ["incident_brief_one_sentence", "policy_delta_two_bullets"]} action=retry
- latency_cliff: status=clear threshold=stress latency_ms>2125 after input_tokens>=1275; hard trigger if 2 of last 3 stress steps exceed it evidence={"backend_mode": "local-any-gated", "gated_latency_steps": [], "hard_trigger_last_three": false} action=retry
- near_cap_pressure: status=clear threshold=benchmark LORR mean across structured_contracts+failure_escalation >=0.17, or stress LORR=1 on any 2 steps within 4-step window evidence={"stress_window_hit": false, "structured_lorr_mean": 0} action=repair
- repetition_loop: status=clear threshold=stress RCS>=0.255 on 2 consecutive steps, or last 5 stress steps mean RCS>=0.187 evidence={"high_rcs_steps": [], "last_five_mean_rcs": 0.0, "two_consecutive": false} action=escalate
- context_decay: status=clear threshold=>=2 context_pressure benchmark contract failures, or gated stress failure dominated by repetition/near-cap reasons evidence={"context_benchmark_failures": [], "dominant_gated_failure_reasons": [], "first_gated_failure_step": null, "stress_contract_break_steps": [1, 2, 3, 4, 5]} action=escalate
- persistent_failure: status=clear threshold=stress reaches 3 consecutive failed steps, or both failure_escalation benchmark cases fail contract evidence={"failure_escalation_contract_failures": ["exact_yaml_status"], "stress_reasons": [], "stress_step": null} action=abort

## Aggregated Generation Report

# LTE Report

- Records: 44 (generations: 44)
- Models: 1
- Approx token counting present: no

## Stress cliff (persistent failure)

- Phi-4-mini-instruct-8bit: cliff_reached=no step=23 reasons=[] context_fraction=0.1295

## Per-model summary

| model | ER(mean) | LORR(mean) | RCS(mean) | VD(mean, paired) |
| --- | ---: | ---: | ---: | ---: |
| Phi-4-mini-instruct-8bit | 0.2579 | 0.0455 | 0.0000 | 0.8205 |

## Per-suite breakdown

### adversarial_pressure — Phi-4-mini-instruct-8bit
- ER(mean): 0.6586
- RCS(mean): 0.0000

### bounded_determination — Phi-4-mini-instruct-8bit
- ER(mean): 0.3323
- RCS(mean): 0.0000

### core_conciseness — Phi-4-mini-instruct-8bit
- ER(mean): 0.4972
- RCS(mean): 0.0000

### long_context_stability — Phi-4-mini-instruct-8bit
- ER(mean): 0.3356
- RCS(mean): 0.0000

### persistent_failure_probe — Phi-4-mini-instruct-8bit
- ER(mean): 0.5725
- RCS(mean): 0.0000

### stress — Phi-4-mini-instruct-8bit
- ER(mean): 0.0808
- RCS(mean): 0.0000

### structured_extraction — Phi-4-mini-instruct-8bit
- ER(mean): 0.4894
- RCS(mean): 0.0000

## Worst prompts (by metric)

- RCS=0.0000 model=Phi-4-mini-instruct-8bit suite=core_conciseness prompt_id=incident_brief_one_sentence
- RCS=0.0000 model=Phi-4-mini-instruct-8bit suite=core_conciseness prompt_id=policy_delta_two_bullets
- RCS=0.0000 model=Phi-4-mini-instruct-8bit suite=core_conciseness prompt_id=handoff_delta_concise
- RCS=0.0000 model=Phi-4-mini-instruct-8bit suite=core_conciseness prompt_id=handoff_delta_detailed
- RCS=0.0000 model=Phi-4-mini-instruct-8bit suite=structured_extraction prompt_id=extract_ticket_json

## Notes

- VD is computed using `output_tokens` for paired `variant: concise|detailed` cases with the same `pair_id`.
- If any records use approximate token counting, treat ER/LORR/VD as approximate as well.
