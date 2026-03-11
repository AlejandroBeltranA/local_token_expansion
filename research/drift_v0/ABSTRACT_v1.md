`drift_v0` evaluates operational reliability of local LLMs under short-horizon agentic stress, emphasizing machine-actionable outputs and accountable intervention rather than task capability alone. The pipeline executes three experiments: `E1` single-turn contract adherence, `E2` three-turn state-carrying tasks, and `E3` `E2` tasks under `1k` and `4k` context-budget arms. We report results from an already completed 45-condition sweep (`5` model families x `3` temperatures x `3` top-p settings) using existing artifacts only.

**Measured facts:** Across all conditions, failure-rate ranges were `0.8889-1.0` (`E1`), `0.9-1.0` (`E2`), and `0.925-1.0` (`E3`). Mistral-7B-Instruct-v0.3 was consistently best in this setup (composite `0.9130`), while within-model temperature/top-p effects were limited relative to across-model-family differences. Intervention reports showed retry effectiveness `0.0` in E2/E3 and escalation-after-retry `1.0`. Post-hoc failure-cause artifacts indicate near token-cap outputs and non-extractable schema failures dominate, with repetition-only failures rare.

**Interpretation:** The project demonstrates that auditable, scalable reliability monitoring and intervention signaling can be run on local hardware with reproducible AI-assisted orchestration. However, current policy is detection/escalation-heavy and not recovery-effective. We therefore treat this run as a strong baseline for accountability-oriented evaluation, while explicitly identifying next-step requirements: hard-vs-soft failure separation, improved recovery strategies, and rebalanced stress design to increase within-model sensitivity.

## Handoff Note
### What I changed
- Produced a 150-250 word abstract using only measured sweep/report artifacts.
- Explicitly separated facts from interpretation.

### Assumptions
- Artifact files under `/tmp/drift_v0_*` correspond to the reported run.

### Open questions
- Should final submission abstract foreground orchestration novelty or empirical results first?
