# drift_v0: Auditable Reliability Stress Testing for Local LLM Agentic Workflows

**Author:** Alejandro Beltran  
**Affiliation:** The Alan Turing Institute  
**Document type:** Technical report / working paper  
**Version:** v2 (consolidated draft)  
**Date:** 2026-03-02

## Abstract
Operational LLM risk in deployment is often driven by workflow breakage rather than isolated task errors. This paper presents `drift_v0`, a reproducible local benchmark for measuring when model outputs stop being machine-actionable under short-horizon agentic stress. We evaluate five MLX-hosted model families across 45 decoding conditions (temperature `0.0/0.2/0.6`; top-p `0.8/0.95/1.0`) on three experiments: `E1` single-turn contract tasks, `E2` three-turn state-carrying tasks, and `E3` `E2` variants under `1k` versus `4k` context-budget arms. Across conditions, failure rates are high (`E1`: `0.8889-1.0`, `E2`: `0.9-1.0`, `E3`: `0.925-1.0`). Mistral-7B-Instruct-v0.3 is best in this setup (composite `0.9130`), while within-family decoding sensitivity is weak relative to across-family differences. Intervention policy is detection/escalation-heavy: retry effectiveness is `0.0` in E2/E3 and escalation-after-retry is `1.0`. Post-hoc failure artifacts show dominant near-token-cap and non-extractable schema failures. We interpret these results as evidence that accountable intervention signaling can be implemented reproducibly on local hardware, but recovery capability and hard-versus-soft failure separation remain open requirements.

## 1. Introduction
A common failure mode in applied LLM systems is not a single wrong answer, but a chain reaction in which one malformed output propagates through an automated workflow. For deployment settings where downstream components require strict parseability, semantically plausible text is insufficient if it violates schema or control constraints.

`drift_v0` was designed around this operational reality. The project reframes evaluation away from pure task intelligence and toward machine-actionability under stress: contract adherence, short-horizon state consistency, repetition resistance, and intervention behavior. The accountability question is central: when breakage occurs, does the system emit auditable signals that support clear ownership and intervention policy?

The work also addresses methodological credibility for AI-assisted research workflows. Instead of ad hoc prompting, implementation was organized into constrained agent roles with boundary controls and contract checks. This paper treats that orchestration discipline as part of methodological rigor.

This report answers four questions:

1. Can the harness measure reliability differences across local model families?
2. How sensitive are outcomes to temperature/top-p under the current task design?
3. Does the intervention policy recover failures or primarily escalate them?
4. What failure taxonomy emerges from post-hoc artifact inspection?

## 2. Method
### 2.1 Pipeline and components
`drift_v0` uses a staged pipeline:

1. raw generation: `research/drift_v0/runner/run_experiments.py`
2. event evaluation: `research/drift_v0/runner/evaluate_events.py`
3. trigger logic: `research/drift_v0/runner/verifiers.py`
4. intervention policy: `research/drift_v0/runner/interventions.py`
5. analysis/reporting: `research/drift_v0/analysis/summarize.py`
6. parameter sweep orchestration: `research/drift_v0/runner/run_sweep.py`

Pre-registered triggers are `schema_failure`, `repetition_loop`, and `state_contradiction`. Intervention remains a fixed two-step policy: one retry attempt, then reset/escalate if unresolved.

### 2.2 Experimental setup
Models evaluated:

- Meta-Llama-3.1-8B-Instruct-3bit
- Mistral-7B-Instruct-v0.3
- Phi-3-mini-4k-instruct-4bit
- Phi-4-mini-instruct-8bit
- SmolLM-1.7B-Instruct-4bit

Decoding grid:

- temperature: `0.0`, `0.2`, `0.6`
- top-p: `0.8`, `0.95`, `1.0`

Total conditions: `45` (`5 x 3 x 3`).

Task packs:

- `E1`: single-turn contract adherence baseline
- `E2`: 3-turn short-horizon state-carrying episodes
- `E3`: `E2` tasks under `1k` and `4k` context-budget arms

### 2.3 Multi-agent orchestration and reproducibility controls
Implementation followed explicit role partitioning:

- Agent A: task packs/freeze management
- Agent B: runtime/verifier/intervention logic
- Agent C: analysis/reporting outputs
- Orchestrator: scope compliance, protocol checks, merge-order gating

Controls included boundary enforcement, trigger immutability, merge sequence (A -> B -> C), and command-level reproducibility checks. This structure was intended to make AI-assisted execution inspectable and auditable.

### 2.4 Data sources
All reported numbers are taken from existing run artifacts only:

- `/tmp/drift_v0_sweep/sweep_manifest.csv`
- `/tmp/drift_v0_sweep/<condition_id>/report/metrics_summary.json`
- `/tmp/drift_v0_failure_cause_by_model.csv`
- `/tmp/drift_v0_failure_cause_overall.csv`

No new experiments were executed for this manuscript.

### 2.5 Event contract and evaluator flow
Raw generation emits per-turn JSONL events keyed by stable identifiers (`run_id`, `experiment_id`, `task_id`, `turn`) and runtime metadata (model, decoding settings, token counts, latency, response text). The evaluator consumes these events and applies deterministic verifiers in fixed order:

1. schema/contract check,
2. repetition-loop check,
3. state-contradiction check.

Trigger outputs are materialized into evaluated rows rather than post-hoc inferred, which allows downstream analysis to distinguish primary-failure behavior from intervention behavior using the same row contract. This design reduces analyst degrees of freedom and improves reproducibility across reruns.

### 2.6 Intervention accounting
Intervention logic is explicitly logged as closed-loop state transitions. For each eligible failure, the system records whether retry was attempted, whether retry resolved the issue, and whether escalation followed. This supports operational questions directly: not only “how often did models fail,” but “how often did policy recover versus hand off.”

In this framing, escalation is not treated as model success; it is treated as governance output. The benchmark therefore evaluates both model reliability and intervention-policy effectiveness.

### 2.7 Aggregation strategy and artifact production
`run_sweep.py` executes the full model x decoding grid and writes condition directories with standardized reports. `summarize.py` computes experiment-level rates, first-failure summaries, retry effectiveness, escalation metrics, and E3 deltas from evaluated rows. The sweep manifest then exposes condition-level comparables used for ranking and cross-family analysis.

Post-hoc failure-cause tables were derived from evaluated artifacts and are used here as secondary diagnostic evidence, not as replacement for pre-registered primary metrics.

### 2.8 Author-agent interaction protocol (guidance)
**Measured process facts**

The workflow was executed as supervised multi-agent implementation, not freeform prompt programming. The author defined research framing, risk assumptions, non-negotiable trigger set, and reporting requirements before implementation proceeded. Delivery then followed a staged protocol:

1. problem framing and risk-policy definition (author-owned),
2. specification freeze for tasks, triggers, and output contracts,
3. parallel implementation by ownership boundary (tasks vs runtime vs analysis),
4. orchestrator contract audit and merge-order gate (`A -> B -> C`),
5. artifact validation and report handoff.

Control mechanisms were explicit and auditable: directory ownership boundaries, trigger immutability (`schema_failure`, `repetition_loop`, `state_contradiction`), merge-sequence constraints, command-level reproducibility trails, and separation of post-hoc diagnostics from primary metric generation. Contamination prevention was operationalized by scope restrictions (no task edits by runtime agent; no runtime edits by analysis agent). Ambiguities were resolved by protocol-first decisions at interface boundaries rather than ad hoc prompt drift.

#### 2.8.1 Objective contribution attribution

| Role | Primary responsibilities | Concrete outputs / evidence | Credit boundary |
|---|---|---|---|
| PI / Author | Research framing, risk policy, success criteria, final interpretation | Handoff brief, section-level narrative decisions, limitation framing | Strategic and scientific ownership |
| Agent A (tasks) | Task-pack construction and freeze discipline | Versioned task files and freeze documentation under `research/drift_v0/tasks/` | No runtime/evaluation logic credit |
| Agent B (runtime) | Execution pipeline, verifiers, intervention policy | `runner/run_experiments.py`, `runner/evaluate_events.py`, `runner/verifiers.py`, `runner/interventions.py` | No task-design or analysis-credit |
| Agent C (analysis) | Summaries, metrics aggregation, reporting artifacts | `analysis/summarize.py`, condition reports, manifest-compatible summaries | No runtime logic credit |
| Orchestrator | Protocol enforcement, merge gating, contract checks | Boundary audits, merge-order validation, reproducibility checks | Process integrity credit |
| Tooling stack | Execution substrate and automation utilities | MLX/local runtime, scripts, deterministic artifact generation | Enabling infrastructure, not scientific interpretation |

Credit is assigned by artifact ownership and protocol responsibility, not by narrative prominence.

**Interpretation**

This protocol demonstrates supervised modular execution where accountability remains human-led and artifact-verifiable. The practical implication is that AI assistance can accelerate implementation while preserving methodological traceability when interfaces, boundaries, and audit gates are explicit.

## 3. Results
### 3.1 Primary reliability outcomes
**Measured facts**

- Conditions: `45`
- Failure-rate ranges:
  - `E1`: `0.8889` to `1.0`
  - `E2`: `0.9` to `1.0`
  - `E3`: `0.925` to `1.0`
- Family-level mean composite scores (lower is better):
  - Mistral-7B-Instruct-v0.3: `0.9130`
  - Phi-3-mini-4k-instruct-4bit: `0.9417`
  - SmolLM-1.7B-Instruct-4bit: `0.9752`
  - Meta-Llama-3.1-8B-Instruct-3bit: `1.0`
  - Phi-4-mini-instruct-8bit: `1.0`

**Interpretation**

- The benchmark captures meaningful across-family reliability differences under fixed tasks.
- The run operates in a high-failure stress regime, which is useful for brittleness detection but compresses finer effects.

### 3.2 Decoding sensitivity
**Measured facts**

- Top-ranked manifest conditions are all Mistral-7B variants with identical E1/E2/E3 values.
- Several families show near-constant high failure across all tested temperature/top-p settings.

**Interpretation**

- Within-model decoding effects are weak relative to model-family effects in this setup.
- Weak variation may reflect prompt-contract rigidity, strict verifier behavior, model limitations, or interactions among these factors.

### 3.3 Intervention behavior
**Measured facts**

- In E2/E3 reports, retry effectiveness values are `0.0`.
- Escalation-after-retry values are `1.0`.

**Interpretation**

- Intervention policy is currently effective for detection and accountable routing, but not for recovery.
- Escalation traces are operationally useful, yet they do not constitute resilience on their own.

### 3.4 Failure taxonomy
**Measured facts** (E2/E3 primary turns, overall artifact)

- rows: `8100`
- failed: `7677` (`0.9478`)
- near token-cap among failed: `6804` (`88.63%`)
- schema non-extractable among failed: `6579` (`85.70%`)
- schema extractable among failed: `1080` (`14.07%`)
- repetition-only failures: `18`

Model-level contrasts:

- Mistral fail rate: `0.9`; extractable-schema share among failed: `0.5617`
- Llama fail rate: `1.0`; non-extractable-schema share among failed: `0.9778`
- SmolLM fail rate: `0.95`; non-extractable-schema share among failed: `0.9766`

**Interpretation**

- Dominant failures are consistent with contractability pressure under constrained output budgets.
- A portion of failures is plausibly soft formatting/wrapper non-compliance rather than purely semantic inability.

### 3.5 Figures and tables with interpretation
The following visuals are generated from existing artifacts and are included to make the results readable and auditable.

**Table 1. Sweep design and coverage**

| Item | Value |
|---|---|
| Models | 5 |
| Temperatures | 0.0, 0.2, 0.6 |
| Top-p values | 0.8, 0.95, 1.0 |
| Total conditions | 45 |
| Primary manifest | `/tmp/drift_v0_sweep/sweep_manifest.csv` |

This table establishes that comparisons are not anecdotal single-run outcomes, but a complete grid under fixed tasks and evaluators.

**Table 2. Per-family mean failure rates**

| Model family | E1 mean | E2 mean | E3 mean | Composite mean |
|---|---:|---:|---:|---:|
| Mistral-7B-Instruct-v0.3 | 0.8889 | 0.9250 | 0.9250 | 0.9130 |
| Phi-3-mini-4k-instruct-4bit | 1.0000 | 0.9000 | 0.9250 | 0.9417 |
| SmolLM-1.7B-Instruct-4bit | 1.0000 | 0.9630 | 0.9627 | 0.9752 |
| Meta-Llama-3.1-8B-Instruct-3bit | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Phi-4-mini-instruct-8bit | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

This table makes the central empirical point explicit: model-family choice dominates observed reliability differences in the current setup.

**Figure 1. Primary failure rates by model family and experiment**

![Figure 1](../papers/drift_v0/figures/figure1_failure_rates_by_model.svg)

Figure 1 shows high absolute failure rates across all families and confirms that Mistral is consistently lower than peers. It also visualizes the ceiling effect for families that saturate near `1.0`.

**Figure 2. E3 context delta (4k - 1k) by family**

![Figure 2](../papers/drift_v0/figures/figure2_e3_delta_by_model.svg)

Figure 2 shows that E3 deltas are near zero for most families, with one notable positive deviation (Phi-3-mini). This supports the claim that current E3 stress is only partially discriminative.

**Table 3. Intervention effectiveness summary (E2/E3)**

| Metric | Observed values across condition reports |
|---|---|
| Retry effectiveness | 0.0 only |
| Escalation-after-retry | 1.0 only |

Table 3 clarifies that intervention policy behavior is deterministic in this run: retries are attempted but do not recover measured failures.

**Figure 3. Failure taxonomy composition by family**

![Figure 3](../papers/drift_v0/figures/figure3_failure_taxonomy_by_model.svg)

Figure 3 shows why “failure” requires decomposition. Non-extractable schema failures and near-cap outputs dominate the distribution, while repetition-only failures are rare. This is the main evidence for separating hard failures from soft formatting failures in the next iteration.

### 3.6 Operational decision rule (deployment guidance)
To make intervention policy actionable, we define a conservative routing rule aligned with current evidence:

1. treat any trigger event (`schema_failure`, `repetition_loop`, `state_contradiction`) as intervention-eligible,
2. allow exactly one retry (current policy),
3. if unresolved after retry, escalate to human review with attached evaluated-row evidence and trigger labels,
4. classify escalated cases as unresolved automation events, not successful completions.

Given observed retry effectiveness (`0.0` in E2/E3), this rule is intentionally strict and prioritizes auditability over autonomous completion rate. It should be revised only after measurable recovery gains are demonstrated under the same reporting contract.

## 4. Discussion
This run supports three conclusions, with important caveats.

First, the harness measures operational reliability differences across model families at useful scale on local infrastructure. This is a non-trivial result for deployment teams that need model triage under strict machine-actionable constraints rather than open-ended quality scoring.

Second, weak within-family sensitivity does not imply decoding settings are irrelevant in general. In this run, failure ceilings and contract strictness likely compressed variance. The correct interpretation is methodological: the current design is strong for exposing brittle regimes, but weak for resolving small parameter effects.

Third, intervention policy is the primary maturity bottleneck. The system is successful at auditable detection/routing, yet unsuccessful at recovery. For operational governance this still has value, because escalation traces make ownership explicit; however, it does not reduce incident volume without a stronger repair stage.

From an accountability perspective, the project demonstrates a practical division of responsibilities:

1. models generate candidate outputs,
2. verifiers enforce explicit operational contracts,
3. interventions route unresolved failures,
4. humans receive auditable escalation when automation cannot recover.

That separation is preferable to implicit “best effort” behavior because it makes failure legible and assignable. The downside is that strict enforcement can conflate hard semantic errors with soft formatting errors unless hard-vs-soft pathways are modeled explicitly.

Methodologically, the multi-agent orchestration is also part of the contribution. By constraining task design, runtime logic, and analysis to separate owners with protocol checks, the workflow reduces contamination risk and makes AI-assisted implementation more defensible as research practice.

## 5. Limitations
**Measured constraints**

- Failure rates remain high across all tested conditions.
- E2/E3 separability is weak for most families.
- Retry recovery is absent in current policy outputs.

**Interpretation risks (PI concerns preserved)**

- Strict validators may over-penalize wrappers and blur hard vs soft failures.
- `max_tokens` pressure likely contributes to truncation and schema breakage.
- Weak variation should not be interpreted as definitive absence of decoding effects.

### 5.1 Threats to validity
**Internal validity**

- Strict verifier behavior may confound semantic failure with strict formatting non-compliance.
- Ceiling effects can compress variance and mask secondary effects (for example, decoding sensitivity).

**Construct validity**

- “Operational reliability” is proxied through trigger-defined failure and intervention traces; this is appropriate for contract-first deployments but does not capture all notions of model quality.
- Escalation is modeled as governance output, which may differ from product KPIs optimized for completion rate.

**External validity**

- Findings are tied to this task suite, prompt contract, and local runtime setup.
- Generalization to longer-horizon, tool-using, or domain-specific agents should be treated as unverified until replicated under comparable contracts.

## 6. Reproducibility Checklist
Minimal checklist to reproduce this manuscript’s quantitative claims from existing artifacts:

1. Verify artifact presence:
   - `/tmp/drift_v0_sweep/sweep_manifest.csv`
   - `/tmp/drift_v0_sweep/<condition_id>/report/metrics_summary.json`
   - `/tmp/drift_v0_failure_cause_by_model.csv`
   - `/tmp/drift_v0_failure_cause_overall.csv`
2. Regenerate figure/table assets:
   - `python3 research/papers/drift_v0/generate_assets.py`
3. Confirm manifest-level sweep dimensions and ranges:
   - 45 conditions
   - E1/E2/E3 ranges as reported in Section 3
4. Confirm intervention metrics from condition reports:
   - retry effectiveness `0.0` in E2/E3
   - escalation-after-retry `1.0` in E2/E3
5. Confirm failure-cause shares from post-hoc CSVs:
   - near-cap and non-extractable schema dominance

Assumed environment: local MLX-capable setup and existing `/tmp/drift_v0_*` artifacts from the completed sweep.

## 7. Next Iteration Design
1. Add explicit hard-vs-soft failure split in official metrics.
2. Introduce deterministic repair step (and optional second-pass repair model) after retry.
3. Recalibrate token budgets and task contracts to reduce ceiling effects.
4. Re-run targeted sweeps around top and weak families under revised validation.
5. Keep orchestration controls (role boundaries, contracts, merge order) as part of reproducibility protocol.

## 8. Versioned claim boundary
**Claims supported in v2**

- The harness is reproducible, auditable, and scalable on local infrastructure.
- Cross-family reliability differences are measurable under fixed tasks.
- Current policy behavior is detection/escalation-heavy with low recovery.

**Claims deferred to v3**

- Robust autonomous recovery claims.
- Strong causal attribution of weak variation to model vs prompt vs verifier effects.
- Generalized conclusions beyond the present task/stress configuration.

## 9. Conclusion
`drift_v0` provides a credible baseline for accountability-oriented reliability evaluation of local LLM workflows. The system is reproducible, auditable, and scalable on local infrastructure. It distinguishes model families effectively, but currently offers detection/escalation rather than recovery. The next phase should prioritize failure-type separation and intervention effectiveness rather than broader parameter expansion.
