# Paper Results Draft

This draft summarizes the completed sweep in [results/weekend_sweep_full/report.md](../results/weekend_sweep_full/report.md) and [results/weekend_sweep_full/baseline_phase_summary.json](../results/weekend_sweep_full/baseline_phase_summary.json).

## Result Summary

The revised intervention scaffold produced stable intervention regimes across all five tested local models. Across six baseline replicates per model, every model remained in the same modal intervention regime. This suggests the scaffold is identifying stable behavioral profiles rather than seed-specific noise.

## Table 1. Baseline Intervention Regimes

| Model | Modal intervention | Runs in regime | Trigger profile | Mean contract failures | Recoverable / unrecoverable | Mean stress latency (ms) | First gated failure step |
| --- | --- | ---: | --- | ---: | --- | ---: | --- |
| Phi-4-mini-instruct-8bit | `escalate` | 6 / 6 | `context_decay`, `over_expansion` | 7.0 | 4.0 / 3.0 | 2866.9 | none |
| Meta-Llama-3.1-8B-Instruct-3bit | `escalate` | 6 / 6 | `context_decay`, `over_expansion` | 9.0 | 5.0 / 4.0 | 4429.1 | none |
| Mistral-7B-Instruct-v0.3 | `abort` | 6 / 6 | `latency_cliff`, `over_expansion`, `persistent_failure` | 4.0 | 3.0 / 1.0 | 6301.3 | 15 |
| Phi-3-mini-4k-instruct-4bit | `abort` | 6 / 6 | `context_decay`, `near_cap_pressure`, `over_expansion`, `persistent_failure` | 11.0 | 8.0 / 3.0 | 5226.1 | none |
| SmolLM-1.7B-Instruct-4bit | `abort` | 6 / 6 | `context_decay`, `near_cap_pressure`, `over_expansion`, `persistent_failure` | 12.0 | 6.0 / 6.0 | 2924.6 | none |

## Table 2. Intervention Regime Groups

| Regime | Models | Interpretation |
| --- | --- | --- |
| `escalate` | Phi-4-mini-instruct-8bit, Meta-Llama-3.1-8B-Instruct-3bit | These models remained operational enough to avoid immediate abort, but repeatedly crossed state-integrity and bounded-output thresholds that undermined trust. |
| `abort` | Mistral-7B-Instruct-v0.3, Phi-3-mini-4k-instruct-4bit, SmolLM-1.7B-Instruct-4bit | These models crossed stronger intervention boundaries, either through latency-driven persistent failure or through combined cap-pressure, context-decay, and persistent-failure behavior. |

## Table 3. Parameter-Sweep Stability

The downstream expansion runs preserved the same regime labels observed in baseline.

| Model | Baseline regime | Expansion regime | Change under `temperature=0.5` or `max_tokens={128,256}` |
| --- | --- | --- | --- |
| Phi-4-mini-instruct-8bit | `escalate` | `escalate` | none |
| Meta-Llama-3.1-8B-Instruct-3bit | `escalate` | `escalate` | none |
| Mistral-7B-Instruct-v0.3 | `abort` | `abort` | none |
| Phi-3-mini-4k-instruct-4bit | `abort` | `abort` | none |
| SmolLM-1.7B-Instruct-4bit | `abort` | `abort` | none |

## Representative Outputs By Regime

### Escalate: Phi-4-mini-instruct-8bit

- Probe: `policy_delta_two_bullets`
- Failed check: `8 words or fewer per bullet`
- Output:

```text
- Policy A retains logs for 30 days, Policy B for 7 days.
- Policy B requires ticket number for contractor access, Policy A only manager approval.
```

Interpretation:
The model remains semantically relevant but repeatedly exceeds bounded-output limits. This supports escalation because the output is coherent yet not reliably trustworthy for tightly constrained workflow use.

### Escalate: Meta-Llama-3.1-8B-Instruct-3bit

- Probe: `state_reconciliation_json`
- Characteristic behavior: coherent-looking state answers that still miss contract or state-integrity expectations.
- Stress example:

```text
• Report the latest status as Iris's incident.
• Preserve the current owner Iris's incident.
• Name the next action to resolve issues.
• Name one risk caused by delayed responses.
• State one escalation condition to management.
```

Interpretation:
The model maintains a stable surface form but drifts into weak state handling and generic operational summaries. This is an escalation case because continued reliance would require stronger oversight.

### Abort: Mistral-7B-Instruct-v0.3

- Trigger pathway: `latency_cliff` -> `persistent_failure`
- Stress terminal row:

```text
step=17 input_tokens=1703 latency_ms=9449 failure_reasons=['latency'] consecutive_failures=3
```

Interpretation:
This model has relatively low benchmark contract failure counts, but becomes operationally unusable once context passes the latency gate. The abort decision is justified by non-recovering, context-gated latency failure.

### Abort: Phi-3-mini-4k-instruct-4bit

- Probe: `incident_brief_one_sentence`
- Failed check: `one sentence only`
- Output:

```text
API latency spiked post-cache rollout but was quickly restored to 210 ms after rollback.<|end|>
```

- Stress terminal row:

```text
step=2 input_tokens=753 latency_ms=6042 failure_reasons=['lorr'] consecutive_failures=3
```

Interpretation:
This model combines formatting instability with early cap-pressure-driven stress collapse. That combination makes continued use unjustified.

### Abort: SmolLM-1.7B-Instruct-4bit

- Probe: `policy_delta_two_bullets`
- Failed check: `exactly 2 bullets`
- Output:

```text
Policy A is more restrictive than Policy B.

Policy A:
- Retain logs for 30 days.
- No intro or closing sentence.

Policy B:
- Retain logs for 7 days.
- Contractor access requires manager approval plus ticket number.
```

- Stress terminal row:

```text
step=2 input_tokens=741 latency_ms=3451 failure_reasons=['lorr'] consecutive_failures=3
```

Interpretation:
The model fails to maintain bounded outputs and rapidly collapses into near-cap pressure during stress. This is a strong abort case and a useful negative control for the accountability scaffold.

## Results Claims Supported By The Sweep

1. Intervention regimes are stable across seeds for all tested local models.
2. Different models cross intervention boundaries through different behavioral pathways.
3. Contract-failure counts alone are insufficient for intervention decisions; Mistral has fewer benchmark failures than several weaker models but still warrants `abort` because of latency-driven persistent failure.
4. Recoverable and unrecoverable failures can be separated in the artifact layer and used to distinguish `repair`, `escalate`, and `abort`.

## Suggested Result Paragraph

The intervention scaffold produced stable behavioral profiles across all tested local models. Two models, Phi-4-mini-instruct-8bit and Meta-Llama-3.1-8B-Instruct-3bit, consistently occupied an escalation regime characterized by context-decay and bounded-output failures without terminal stress collapse. Three models consistently occupied abort regimes, but through different pathways: Mistral-7B-Instruct-v0.3 crossed a latency-driven persistent-failure boundary once context exceeded the gating threshold, whereas Phi-3-mini-4k-instruct-4bit and SmolLM-1.7B-Instruct-4bit combined over-expansion, near-cap pressure, and persistent failure. These results support the claim that intervention decisions can be grounded in distinct, measurable behavioral signatures rather than broad model-quality rankings.
