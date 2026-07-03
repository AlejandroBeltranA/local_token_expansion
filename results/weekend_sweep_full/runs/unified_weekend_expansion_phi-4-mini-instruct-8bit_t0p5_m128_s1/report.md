# LTE Unified Report

- Overall recommendation: `escalate`
- Records: 38 total, 14 benchmark, 24 stress, 0 errors

## Trigger Summary

### Phi-4-mini-instruct-8bit
- Recommendation: `escalate`
- Rationale: context decay, repetition loop, or latency cliff fired without persistent failure
- over_expansion: status=fired threshold=>=2 budget-tagged benchmark misses with ER>=1.25 or contract failure, or any max_tokens<=56 row with LORR=1 evidence={"bounded_lorr_failures": ["ledger_carry_forward_json"], "budget_control_failures": ["policy_delta_two_bullets"]} action=retry
- latency_cliff: status=clear threshold=stress latency_ms>2500 after input_tokens>=1500; hard trigger if 2 of last 3 stress steps exceed it evidence={"gated_latency_steps": [], "hard_trigger_last_three": false} action=retry
- near_cap_pressure: status=clear threshold=benchmark LORR mean across structured_contracts+failure_escalation >=0.20, or stress LORR=1 on any 2 steps within 5-step window evidence={"stress_window_hit": false, "structured_lorr_mean": 0} action=repair
- repetition_loop: status=clear threshold=stress RCS>=0.30 on 2 consecutive steps, or last 5 stress steps mean RCS>=0.22 evidence={"high_rcs_steps": [], "last_five_mean_rcs": 0.0, "two_consecutive": false} action=escalate
- context_decay: status=fired threshold=>=2 context_pressure benchmark contract failures, or gated stress failure dominated by repetition/near-cap reasons evidence={"context_benchmark_failures": ["state_reconciliation_json", "ledger_carry_forward_json"], "dominant_gated_failure_reasons": [], "first_gated_failure_step": null, "stress_contract_break_steps": [1, 2, 3, 4, 5]} action=escalate
- persistent_failure: status=clear threshold=stress reaches 3 consecutive failed steps, or both failure_escalation benchmark cases fail contract evidence={"failure_escalation_contract_failures": ["exact_yaml_status"], "stress_reasons": [], "stress_step": null} action=abort

## Aggregated Generation Report

# LTE Report

- Records: 38 (generations: 38)
- Models: 1
- Approx token counting present: no

## Stress cliff (persistent failure)

- Phi-4-mini-instruct-8bit: cliff_reached=no step=23 reasons=[] context_fraction=0.1561

## Per-model summary

| model | ER(mean) | LORR(mean) | RCS(mean) | VD(mean, paired) |
| --- | ---: | ---: | ---: | ---: |
| Phi-4-mini-instruct-8bit | 0.2167 | 0.0263 | 0.0000 | 1.1316 |

## Per-suite breakdown

### core_conciseness — Phi-4-mini-instruct-8bit
- ER(mean): 0.4441
- RCS(mean): 0.0000

### long_context_stability — Phi-4-mini-instruct-8bit
- ER(mean): 0.3332
- RCS(mean): 0.0000

### persistent_failure_probe — Phi-4-mini-instruct-8bit
- ER(mean): 0.5766
- RCS(mean): 0.0000

### stress — Phi-4-mini-instruct-8bit
- ER(mean): 0.0817
- RCS(mean): 0.0000

### structured_extraction — Phi-4-mini-instruct-8bit
- ER(mean): 0.5024
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
