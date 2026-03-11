# Paper Agent Handoff Brief (for next drafting agent)

## Role

You are drafting a short research paper from an already executed project (`drift_v0`) on local LLM operational reliability under short-horizon agentic stress.

This brief captures:

- project intent,
- principal investigator intuition and doubts,
- what was implemented,
- what was observed,
- and how to write the paper so it demonstrates credible AI-assisted research leadership and reproducible handoff.

---

## 1) Research narrative to preserve

The original project started as a test of model propensity to break/repeat under long runs.  
It was intentionally reframed toward a stronger and more publishable research question:

> Can we build an auditable, scalable pipeline for detecting operational breakage/drift and triggering accountable intervention in agentic LLM workflows?

Key framing constraints from PI:

- Must run on a MacBook with local models.
- Must be relevant to AI safety/accountability and deployment governance.
- Must be credible for job applications and conference-style submission.
- Must show the PI can orchestrate multi-agent implementation reliably.

---

## 2) PI intuitions and concerns (must appear in paper voice)

Use these as motivation and reflection points in Introduction/Discussion:

1. **Intuition:** real deployment risk is less about one-off bad outputs and more about breakage points in chained/agentic workflows.
2. **Concern:** strict evaluators may over-penalize wrappers/formatting and hide meaningful model behavior.
3. **Concern:** current runs showed low variation in some dimensions; unclear if due to model weakness, prompt rigidity, or evaluator harshness.
4. **Goal:** separate true hard failures from soft formatting failures to make evaluation objective.
5. **Expectation:** robust method should compare across models and within-model configs (temperature/top_p), not only one base model.
6. **Operational question:** when should humans intervene, and can that intervention be tied to accountable ownership?

Keep the PI’s tone pragmatic and self-critical: results are valuable, but limitations are explicitly surfaced.

---

## 3) What was built (implementation provenance)

Pipeline components:

- `research/drift_v0/runner/run_experiments.py`
- `research/drift_v0/runner/evaluate_events.py`
- `research/drift_v0/runner/verifiers.py`
- `research/drift_v0/runner/interventions.py`
- `research/drift_v0/analysis/summarize.py`
- `research/drift_v0/runner/run_sweep.py`

Design:

- `E1`: single-turn baseline contract adherence.
- `E2`: 3-turn state-carrying short-horizon episodes.
- `E3`: E2 tasks with `1k` vs `4k` context-budget arms.
- Triggers: `schema_failure`, `repetition_loop`, `state_contradiction`.
- Intervention policy: one retry attempt, then reset/escalate.

Multi-agent implementation orchestration was deliberate:

- Agent A: tasks/freeze packs
- Agent B: runner/verifier/intervention logic
- Agent C: analysis/reporting
- orchestrator audited boundaries and contracts.

This must be acknowledged as a contribution in reproducible AI-assisted research operations.

---

## 4) Core empirical outputs to use

Primary sweep:

- 5 models x 3 temperatures x 3 top_p = 45 conditions.
- Manifest: `/tmp/drift_v0_sweep/sweep_manifest.csv`.

Observed ranges (primary failure rates):

- E1: 0.8889 to 1.0
- E2: 0.9 to 1.0
- E3: 0.925 to 1.0

Top-ranked model family in this setup:

- `Mistral-7B-Instruct-v0.3` consistently best among tested options.

Cross-setting behavior:

- Limited within-model sensitivity to temp/top_p in current setup.
- More variation across model families than decoding settings.

Intervention:

- Retry effectiveness remained near zero in current policy.
- Escalation was common after retries.

Post-hoc failure-cause artifacts:

- `/tmp/drift_v0_failure_cause_by_model.csv`
- `/tmp/drift_v0_failure_cause_overall.csv`

Important post-hoc insight:

- Many E2/E3 failures are near token-cap and non-extractable schema failures.
- Some “failures” are soft wrapper/compliance issues rather than semantic failure.

---

## 5) Required paper stance

The paper should **not** overclaim.

It should claim:

- a practical, reproducible operational reliability harness was built and executed at scale on local hardware,
- meaningful cross-model differences were measurable,
- accountability-oriented intervention signals are feasible and auditable,
- current intervention implementation is detection/escalation-heavy and not yet recovery-effective.

It should explicitly state limitations:

- strict contract penalties,
- output-budget pressure (`max_tokens`),
- weak E2/E3 separability under current task+policy setup,
- confounding between prompt rigidity and model behavior.

---

## 6) Writing requirements for the next agent

Produce:

1. `PAPER_DRAFT_v1.md` (main paper draft)
2. `ABSTRACT_v1.md` (150–250 words)
3. `FIGURE_TABLE_PLAN.md` (what to plot from existing artifacts)
4. `LIMITATIONS_AND_NEXT_STEPS.md` (frank, technical, actionable)

Suggested paper structure:

1. Introduction (motivation + accountability context)
2. Method (E1/E2/E3, triggers, interventions, sweep)
3. Results (cross-model and within-model findings)
4. Failure Taxonomy (hard vs soft, wrapper effects, token-cap effects)
5. Accountability Implications (what intervention signals mean operationally)
6. Limitations
7. Next Iteration Design

Style constraints:

- technical but concise,
- transparent about null/weak findings,
- emphasizes reproducibility and orchestration quality,
- avoids hype.

---

## 7) Non-negotiables for credibility

- Include exact artifact paths used.
- Distinguish measured facts from interpretation.
- Do not hide low variation or weak recovery outcomes.
- Frame “negative” findings as design-learning and evaluation-maturity, not failure.
- Show that AI assistance was supervised, structured, and auditable (not ad hoc prompting).

---

## 8) Optional strong positioning paragraph (can adapt)

> This project demonstrates a practical pattern for AI-assisted empirical safety research: the principal investigator defines risk framing and evaluation policy, delegates modular implementation to constrained agents, and audits integration against pre-registered contracts. The resulting workflow is reproducible, inspectable, and fast enough for iterative policy-relevant experimentation on local infrastructure.

