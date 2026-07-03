# LTE Unified Report

- Overall recommendation: `abort`
- Records: 23 total, 20 benchmark, 3 stress, 0 errors

## Trigger Summary

### SmolLM-1.7B-Instruct-4bit
- Recommendation: `abort`
- Rationale: persistent failure fired or three trigger families fired
- over_expansion: status=fired threshold=>=2 budget-tagged benchmark misses with ER>=1.25 or contract failure, or any max_tokens<=56 row with LORR=1 evidence={"bounded_lorr_failures": ["policy_delta_two_bullets", "ledger_carry_forward_json", "two_line_recovery_plan"], "budget_control_failures": ["policy_delta_two_bullets"]} action=retry
- latency_cliff: status=clear threshold=stress latency_ms>2250 after input_tokens>=1350; hard trigger if 2 of last 3 stress steps exceed it evidence={"backend_mode": "local-any-gated", "gated_latency_steps": [], "hard_trigger_last_three": false} action=retry
- near_cap_pressure: status=fired threshold=benchmark LORR mean across structured_contracts+failure_escalation >=0.18000000000000002, or stress LORR=1 on any 2 steps within 4-step window evidence={"stress_window_hit": true, "structured_lorr_mean": 0.833333} action=repair
- repetition_loop: status=clear threshold=stress RCS>=0.27 on 2 consecutive steps, or last 5 stress steps mean RCS>=0.198 evidence={"high_rcs_steps": [2], "last_five_mean_rcs": 0.0, "two_consecutive": false} action=escalate
- context_decay: status=fired threshold=>=2 context_pressure benchmark contract failures, or gated stress failure dominated by repetition/near-cap reasons evidence={"context_benchmark_failures": ["state_reconciliation_json", "latest_override_selection", "reference_selection_triples", "ledger_carry_forward_json"], "dominant_gated_failure_reasons": [], "first_gated_failure_step": null, "stress_contract_break_steps": [0, 1, 2]} action=escalate
- persistent_failure: status=fired threshold=stress reaches 3 consecutive failed steps, or both failure_escalation benchmark cases fail contract evidence={"failure_escalation_contract_failures": ["exact_yaml_status", "two_line_recovery_plan"], "stress_reasons": ["rcs", "lorr"], "stress_step": 2} action=abort

## Aggregated Generation Report

# LTE Report

- Records: 23 (generations: 23)
- Models: 1
- Approx token counting present: no

## Stress cliff (persistent failure)

- SmolLM-1.7B-Instruct-4bit: cliff_reached=yes step=2 reasons=['rcs', 'lorr'] context_fraction=0.3618

## Per-model summary

| model | ER(mean) | LORR(mean) | RCS(mean) | VD(mean, paired) |
| --- | ---: | ---: | ---: | ---: |
| SmolLM-1.7B-Instruct-4bit | 1.5476 | 0.8696 | 0.1498 | 0.1905 |

## Per-suite breakdown

### adversarial_pressure — SmolLM-1.7B-Instruct-4bit
- ER(mean): 1.3361
- RCS(mean): 0.0376

### bounded_determination — SmolLM-1.7B-Instruct-4bit
- ER(mean): 2.4337
- RCS(mean): 0.3819

### core_conciseness — SmolLM-1.7B-Instruct-4bit
- ER(mean): 0.6679
- RCS(mean): 0.0131

### long_context_stability — SmolLM-1.7B-Instruct-4bit
- ER(mean): 1.4379
- RCS(mean): 0.1446

### persistent_failure_probe — SmolLM-1.7B-Instruct-4bit
- ER(mean): 3.8551
- RCS(mean): 0.2030

### stress — SmolLM-1.7B-Instruct-4bit
- ER(mean): 0.7712
- RCS(mean): 0.2888

### structured_extraction — SmolLM-1.7B-Instruct-4bit
- ER(mean): 1.4596
- RCS(mean): 0.0709

## Worst prompts (by metric)

- RCS=0.8358 model=SmolLM-1.7B-Instruct-4bit suite=bounded_determination prompt_id=abort_threshold_lines
- RCS=0.5699 model=SmolLM-1.7B-Instruct-4bit suite=stress prompt_id=step_0002
- RCS=0.3700 model=SmolLM-1.7B-Instruct-4bit suite=long_context_stability prompt_id=state_reconciliation_json
- RCS=0.3097 model=SmolLM-1.7B-Instruct-4bit suite=bounded_determination prompt_id=continue_verdict_yaml
- RCS=0.2553 model=SmolLM-1.7B-Instruct-4bit suite=structured_extraction prompt_id=emit_action_lines

## Notes

- VD is computed using `output_tokens` for paired `variant: concise|detailed` cases with the same `pair_id`.
- If any records use approximate token counting, treat ER/LORR/VD as approximate as well.
