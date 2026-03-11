# drift_v0: Auditable Reliability Evaluation for Local LLM Agentic Workflows

## Abstract
This paper presents `drift_v0`, a reproducible evaluation harness for operational reliability in local LLM workflows under short-horizon agentic stress. The objective is not benchmark capability in isolation, but identify when model behavior stops being machine-actionable and should trigger accountable intervention. We evaluate five local MLX model families across a 45-condition grid (temperature `0.0/0.2/0.6`, top-p `0.8/0.95/1.0`) over three experiments: `E1` single-turn contract tasks, `E2` three-turn state-carrying tasks, and `E3` `E2` variants under `1k` versus `4k` context budgets. Across conditions, failure rates are high (`E1`: `0.8889-1.0`, `E2`: `0.9-1.0`, `E3`: `0.925-1.0`). The best observed family in this setup is Mistral-7B-Instruct-v0.3. Within-family decoding variation is limited relative to across-family variation. Intervention traces show detection/escalation behavior but low recovery (retry effectiveness `0.0` in E2/E3). Post-hoc analysis indicates many failures are near token-cap and non-extractable schema violations. We interpret these findings as evidence that auditable intervention signaling is feasible at scale on local hardware, while recovery and hard-versus-soft failure separation remain open design requirements.

## 1. Introduction
Operational risk in LLM systems is often not a single wrong answer, but breakage in chained workflows where one malformed output contaminates downstream steps. `drift_v0` was designed around this concern: detect breakage early, classify failure types, and emit intervention actions that are auditable and attributable.

The project was constrained intentionally to local execution on a MacBook and to artifacts that support governance use-cases: explicit triggers, deterministic intervention rules, and reproducible reports. This work therefore sits at the boundary of reliability engineering and deployment accountability rather than pure model capability benchmarking.

A second motivation was methodological. The pipeline was built as a supervised multi-agent workflow with strict boundaries (tasks, runtime, analysis) and contract checks. The goal was to show that AI-assisted research implementation can be fast without becoming ad hoc, provided orchestration is explicit and auditable.

This draft reports one completed sweep and focuses on four questions:

1. Can the harness measure cross-model operational reliability differences under fixed tasks?
2. Does it capture within-model decoding sensitivity (temperature/top-p) in the current setup?
3. Do intervention policies recover failures or only route them?
4. What failure taxonomy emerges once evaluated events are inspected post hoc?

## 2. Method
### 2.1 System architecture
The pipeline comprises six core components:

- generation runner: `research/drift_v0/runner/run_experiments.py`
- event evaluator: `research/drift_v0/runner/evaluate_events.py`
- trigger verifiers: `research/drift_v0/runner/verifiers.py`
- intervention policy: `research/drift_v0/runner/interventions.py`
- summary/metrics: `research/drift_v0/analysis/summarize.py`
- sweep orchestrator: `research/drift_v0/runner/run_sweep.py`

The evaluator applies three pre-registered triggers: `schema_failure`, `repetition_loop`, and `state_contradiction`. Intervention remains a two-step policy: one retry attempt, then reset/escalate if unresolved.

### 2.2 Experimental design
The sweep executes 45 conditions:

- models (5): Meta-Llama-3.1-8B-Instruct-3bit, Mistral-7B-Instruct-v0.3, Phi-3-mini-4k-instruct-4bit, Phi-4-mini-instruct-8bit, SmolLM-1.7B-Instruct-4bit
- temperature (3): `0.0`, `0.2`, `0.6`
- top-p (3): `0.8`, `0.95`, `1.0`

Task packs:

- `E1`: single-turn contract adherence baseline
- `E2`: 3-turn short-horizon state-carrying episodes
- `E3`: `E2` tasks under `1k` and `4k` context-budget arms

### 2.3 AI-assisted orchestration and reproducibility rigor
Implementation followed an explicit multi-agent split:

- Agent A: task packs and freeze controls
- Agent B: runtime, verifiers, interventions
- Agent C: analysis and reporting
- Orchestrator: scope, contract, and merge-order audits

Rigor controls included ownership boundaries, trigger-name immutability, merge sequencing (A -> B -> C), and command-level reproducibility checks. We treat this orchestration design as part of method quality, not only project management.

### 2.4 Data sources used in this paper
All results in this draft are from existing artifacts only:

- sweep manifest: `/tmp/drift_v0_sweep/sweep_manifest.csv`
- per-condition reports: `/tmp/drift_v0_sweep/<condition_id>/report/metrics_summary.json`
- post-hoc failure causes by model: `/tmp/drift_v0_failure_cause_by_model.csv`
- post-hoc failure causes overall: `/tmp/drift_v0_failure_cause_overall.csv`

No additional experiments were run for this paper package.

## 3. Results
### 3.1 Reliability ranges and model-family differences
**Measured facts**

- Total conditions: `45`.
- Failure-rate ranges across conditions:
  - `E1`: `0.8889` to `1.0`
  - `E2`: `0.9` to `1.0`
  - `E3`: `0.925` to `1.0`
- Mean by model family (composite = mean of E1/E2/E3 means):
  - Mistral-7B-Instruct-v0.3: `0.9130`
  - Phi-3-mini-4k-instruct-4bit: `0.9417`
  - SmolLM-1.7B-Instruct-4bit: `0.9752`
  - Meta-Llama-3.1-8B-Instruct-3bit: `1.0`
  - Phi-4-mini-instruct-8bit: `1.0`
- Top-ranked conditions in manifest are all Mistral-7B variants with identical E1/E2/E3 values.

**Interpretation**

- In this configuration, across-family differences are measurable and larger than within-family decoding effects.
- The setup currently behaves as a high-failure stress regime rather than a fine-grained optimization surface.

### 3.2 Within-model decoding sensitivity
**Measured facts**

- For Mistral-7B, E1/E2/E3 outcomes are invariant across all tested temperature/top-p combinations in the sweep manifest.
- Several families show near-constant high failure across decoding settings.

**Interpretation**

- Weak variation may reflect model robustness plateaus, prompt/task rigidity, evaluator strictness, or a combination.
- The current run does not justify strong claims about temperature/top-p as primary levers for reliability improvement.

### 3.3 Intervention outcomes
**Measured facts**

- Across all condition reports, E2/E3 retry effectiveness values are `0.0`.
- Escalation-after-retry values are `1.0`.

**Interpretation**

- Current intervention policy functions as detection + escalation routing, not recovery.
- This supports accountability objectives but does not yet deliver resilience through autonomous repair.

### 3.4 Failure taxonomy from post-hoc artifacts
**Measured facts**

From `/tmp/drift_v0_failure_cause_overall.csv` on E2/E3 primary turns:

- rows: `8100`, failed: `7677`, fail rate: `0.9478`
- near token-cap among failed: `6804` (`88.63%`)
- schema non-extractable among failed: `6579` (`85.70%`)
- schema extractable among failed: `1080` (`14.07%`)
- repetition-only failures: `18`

Model-specific contrasts from `/tmp/drift_v0_failure_cause_by_model.csv`:

- Mistral fail rate: `0.9`, schema extractable share among failed: `0.5617`
- Llama fail rate: `1.0`, schema non-extractable share among failed: `0.9778`
- SmolLM fail rate: `0.95`, schema non-extractable share among failed: `0.9766`

**Interpretation**

- A substantial share of failures appears tied to contractability under output-budget pressure.
- Some observed failures are likely soft formatting/wrapper failures rather than purely semantic inability.

## 4. Accountability Implications
The pipeline demonstrates that intervention signaling can be generated in a reproducible and auditable manner, including explicit retry/escalation pathways. This is useful for deployment governance because it supports ownership assignment when workflows fail.

At the same time, low retry recovery means accountability currently arrives after failure rather than through prevention/recovery. For operational settings, this distinction matters: escalation traces are necessary, but not sufficient.

## 5. Limitations
**Measured facts**

- High failure ranges persisted across all tested conditions.
- E2/E3 separation is limited in many settings.
- Retry recovery in current policy is effectively absent.

**Interpretation and PI concerns preserved**

- Strict evaluators likely over-penalize wrappers and can hide meaningful behavior.
- `max_tokens` pressure likely inflates truncation-related schema failures.
- Weak variation may be confounded between model behavior and prompt-contract rigidity.
- Current metrics need hard-vs-soft failure separation to improve objectivity.

## 6. Conclusion
`drift_v0` achieved its core systems objective: a local, scalable, auditable reliability harness for agentic workflow breakage detection with accountable intervention traces. The results provide measurable cross-family comparisons and a concrete failure taxonomy. They also expose clear maturity gaps: low retry recovery, strict-penalty confounds, and limited decoding sensitivity in this configuration.

The main contribution is therefore twofold: an empirical reliability baseline and a reproducible AI-assisted orchestration pattern that can be re-run, audited, and improved without changing hardware assumptions.

## Handoff Note
### What I changed
- Drafted a full paper-style narrative from existing drift_v0 artifacts only.
- Separated empirical statements into explicit **Measured facts** and **Interpretation** blocks.
- Incorporated PI concerns/doubts and accountability framing directly in Introduction, Results, and Limitations.
- Added explicit method-rigor subsection on multi-agent orchestration and reproducible AI-assisted workflow.

### Assumptions
- Sweep manifest and report artifacts in `/tmp/...` are the canonical outputs for this run.
- Composite comparison across models uses mean of E1/E2/E3 means from the manifest.

### Open questions
- Should hard-vs-soft failure separation be added as a required headline metric in v2?
- Should E3 pressure design be adjusted (task mix, budget, or verifier tolerance) before next sweep?
- What minimum retry success threshold is acceptable before calling intervention policy recovery-capable?
