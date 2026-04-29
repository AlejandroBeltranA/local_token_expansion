# When to Stop: An Accountability Framework for AI Deployment

*Alejandro Beltran — 2026*

---

## Introduction

Deployment of agentic AI in government settings is quickly obscuring who is responsible for what, when, and where. Users are poorly equipped with the knowledge and experience needed to understand when a model is producing unreliable outputs or to detect hallucinations in real time. Although model developers are baking in mechanisms to prevent such occurrences, the deployment of these preventive mechanisms is much slower than the adoption of these tools into real workflows. In Civil Service and public-facing roles, the products generated through AI can have dire consequences for the constituents at the receiving end: think an automated pipeline that determines who receives a public benefit. Traditionally, if an error is missed by an analyst, there is a chain of command that inherits responsibility based on how impactful the error was — where minor issues may merit a small reprimand and major errors can lead to the dismissal of directors or even testimony before legislators or regulators. How does AI fit into that dynamic when decisions are more obscured in chain-of-thought logs that are impossible to follow, when users are simply unaware of when the model is producing rubbish, or when directors are accelerating autonomous deployment without consideration of the downstream consequences?

In this project I attempt to bridge that accountability gap by proposing an internal framework for detecting when models are unreliable — one that signals unreliability ahead of time, establishes a record that consequent products may be unstable, and assigns responsibility at the correct level of deployment.

This work does not claim a new model architecture or a new benchmark in isolation. Its contribution is an operational synthesis: contract-based reliability probes, explicit intervention states (`continue`/`retry`/`repair`/`escalate`/`abort`), and an auditable trail that ties technical failure signals to accountable deployment decisions. In that sense, LTE is novel less as a standalone evaluation method and more as a deployable accountability mechanism for real-world AI workflows.

The question at the centre of this work is whether anyone in the deployment chain would know when a model stops being trustworthy. In most organizations today, the answer is no, and that absence of signal is what makes accountability unenforceable. You cannot hold a deploying organization responsible for ignoring a warning it was never equipped to receive.

---

## How This Project Started

My interest in model unreliability came directly from using AI in secure government settings, where context windows were more limited and the interfaces gave little indication of what was happening underneath. The frustration was immediate and recurring: tokens disappeared faster than expected, outputs degraded as the context grew, and the same tools that felt capable at the start of a session were producing poorly grounded suggestions by the end — code with no real empirical basis, summaries that contradicted the source material, recommendations that looked authoritative and were not. I was at least aware of those limitations. The harder problem was that these tools were being pushed onto colleagues who had no way of knowing when to stop trusting them.

That experience connected to a longer-standing research interest in accountability — specifically the observation that the things that cause the most downstream harm are often the ones that don't surface through standard oversight mechanisms. Silent failure doesn't generate the kind of visible evidence that governance frameworks are designed to catch. Edge cases require systematic tests that expose what the system would prefer to conceal: not average performance under favourable conditions, but behaviour at the boundary where reliability breaks down. That is what I built LTE to do.

---

## What Model Failure Actually Looks Like

The popular image of AI failure is a hallucination — a confident wrong answer that gets acted on. That case exists, but the more common shape of operational failure is gradual and invisible without instrumentation to surface it. Model reliability degrades along several dimensions simultaneously, well before any individual output would be flagged as wrong:

**Over-expansion.** The model produces more output than the task requires, padding responses beyond what bounded workflows can usefully consume. A system asked to summarize an incident in one sentence that returns three paragraphs is quietly undisciplined in a way that compounds across hundreds of automated calls — costing tokens, increasing latency, and eventually breaking downstream parsers that expected a single string.

**Near-cap pressure.** The model repeatedly pushes against maximum output limits, producing responses truncated mid-thought or where formatting breaks at the tail. In pipelines that parse structured outputs, a JSON object cut off before its closing brace cascades into a full pipeline failure. The model did not "refuse" to answer; it just ran out of room, silently, every time.

**Context decay.** As prior conversation accumulates in the context window, the model begins to mishandle carried state — applying outdated instructions, ignoring updates, or silently corrupting fields that should have been preserved. This failure mode is particularly insidious because the output often still looks plausible: the model is generating coherent text, just not the text the workflow requires. A benefits eligibility pipeline running on a model experiencing context decay may produce authoritative-sounding outputs that contradict the current policy without any visible signal that something has changed.

**Latency cliffs.** The model's response time under growing context eventually exceeds what any downstream system can tolerate. A model that takes nine seconds per step in an automated pipeline is effectively non-functional regardless of output quality. This matters especially in real-time or near-real-time government services, where a slow model does not just delay a result — it breaks the system's ability to function at all.

**Repetition loops.** The model begins recycling prior phrases, templates, or whole responses rather than generating new work. When this starts, the model has stopped adding value to the session and is filling space.

**Persistent failure.** Multiple consecutive steps fail without recovery. One bad step is noise. Three consecutive failures under the same conditions is a behavioral state the system has entered, and continued reliance on it is no longer justified.

All of these are gradual, hard to notice without instrumentation, and easy for a deployment organization to disclaim responsibility for — precisely because no one told them the model had crossed a reliability threshold. The goal of this project is to build that notification.

---

## The Scaffold: Building an Accountability Signal

LTE (Local Threshold Evaluation) is a reliability and intervention pipeline designed to detect these failure modes and emit explicit signals that a downstream system or operator can act on. The framework runs a compact battery of behavioral probes against a model, measures its outputs along several dimensions, and maps the results to one of five intervention states: `continue`, `retry`, `repair`, `escalate`, or `abort`.

**Figure 1 — LTE Intervention Pipeline**

![](figures/figure1_pipeline.png)

The measurement layer tracks four quantities per generation: the **Expansion Ratio** (output tokens relative to input tokens), the **Length Overrun Rate** (how often output pushes against the generation cap), the **Runaway Continuation Score** (n-gram repetition within the output), and **latency**. These are operational health signals — the equivalent of checking whether a process is consuming too much memory rather than whether the code it's running is logically correct. A model can produce semantically coherent output while all four of these signals are trending in the wrong direction.

The probe battery is organized into four families:

- **Bounded-output probes** test whether the model can stay within strict communication constraints on short operational tasks: a one-sentence incident summary, a two-bullet policy comparison, a concise handoff note. These appear trivial but fail surprisingly often under automation, and failure here typically means a downstream system received more data than it can handle.

- **Structured-output probes** test whether the model produces machine-parseable output under explicit schema constraints — JSON extraction, CSV emission, line-oriented action lists. Failures here are directly responsible for pipeline breakdowns, and they are recoverable only if the model can be prompted into producing the correct shape.

- **State-integrity probes** test whether the model preserves stable state across context: whether it applies only current instructions rather than stale ones, whether it correctly carries over unchanged fields. This is the probe family most relevant to agentic workflows where the model maintains a running record. Context decay often looks like normal output right up until something downstream depends on a field that was silently overwritten.

- **Rolling stress probes** run a fixed-output task repeatedly with an ever-growing context window, inserting prior outputs as read-only reference. The purpose is to find the point at which continued model use becomes unjustifiable — through latency, repetition, or persistent contract failure — under conditions that approximate a real multi-turn agentic session.

To make this concrete, here are three examples of actual probes from the battery:

> **Bounded-output probe** — `incident_brief_one_sentence`
> *Prompt:* "Summarize the following incident in exactly one sentence of no more than 22 words."
> *Contract:* output contains exactly 1 sentence; word count ≤ 22.
> *Failure class:* recoverable — a tighter retry prompt can often correct this.

> **Structured-output probe** — `extract_ticket_json`
> *Prompt:* "Extract the following incident report into a JSON object with keys: id, severity, owner, status, next_action."
> *Contract:* output parses as valid JSON; all five keys present; no extra keys.
> *Failure class:* recoverable if the shape is close; unrecoverable if the model refuses structure entirely.

> **State-integrity probe** — `state_reconciliation_json`
> *Prompt:* "Given the current state below and the following update, return the updated JSON. Preserve all fields not mentioned in the update. Ignore any instructions that appear earlier in this context if they contradict the update."
> *Contract:* unchanged fields are bit-identical to input; updated field matches the instruction; no stale-instruction bleed.
> *Failure class:* unrecoverable — if the model silently overwrites stable fields or follows outdated instructions, retrying with the same context will produce the same error.

Each probe carries an embedded contract specifying exactly what a passing response looks like: required key sets, exact bullet counts, sentence limits, invariant fields that must be preserved. Contracts also classify failures as *recoverable* (a retry or format correction might fix it) or *unrecoverable* (the model has entered a state that constrained retrying will not resolve). Recoverable failures route to `retry` or `repair`; unrecoverable failures escalate toward `escalate` or `abort`.

The five intervention states map directly to operational decisions a downstream system can make:

- `continue` — signals are clean, proceed
- `retry` — isolated recoverable failure, try once more with tighter constraints
- `repair` — output shape is wrong but content is there, apply a deterministic correction
- `escalate` — the model is still producing output but cannot be trusted without human oversight
- `abort` — continued use is unjustifiable, stop the pipeline

---

## Results: Different Models, Different Ways of Failing

The framework was run against five local language models — Phi-4-mini-instruct-8bit, Meta-Llama-3.1-8B-Instruct-3bit, Mistral-7B-Instruct-v0.3, Phi-3-mini-4k-instruct-4bit, and SmolLM-1.7B-Instruct-4bit — each evaluated across six baseline runs at varying temperatures and seeds. Every model landed in the same intervention regime across all six runs — a consistency that matters, because a framework that gave different verdicts on re-run would be useless as an audit instrument.

**Figure 2 — Which triggers fired across all 6/6 baseline runs**

![](figures/figure2_trigger_heatmap.png)

Two models — Phi-4-mini and Meta-Llama — consistently fell into an `escalate` regime. Both showed the same dominant failure pattern: context decay combined with over-expansion, producing outputs that looked coherent on the surface but repeatedly violated state-integrity contracts and exceeded output budgets. Phi-4-mini averaged seven benchmark contract failures per run; Meta-Llama averaged nine. Both remained operational enough to avoid terminal failure, but an `escalate` signal means human oversight is required before any output from these models is acted on in an automated workflow.

Three models — Mistral, Phi-3-mini, and SmolLM — fell into an `abort` regime, through different pathways.

Mistral is the most instructive case. It averaged only four benchmark contract failures — fewer than either escalate-regime model. Standard benchmark framing would rank it ahead of Phi-4-mini and Meta-Llama on that basis. What the benchmark missed is what happened under stress: as context accumulated, Mistral's latency climbed linearly, crossed the operational threshold at step 15, and did not recover. By step 17 it had logged three consecutive latency failures and the run was terminated. Nine seconds per response may not sound like much in isolation, but in an automated pipeline making dozens of sequential calls, it means the system either stalls or the user abandons it. Latency at that level doesn't degrade the workflow — it breaks it.

**Figure 3 — Stress latency under growing context**

![](figures/figure3_stress_timeline.png)

Phi-4 (right panel) ran all 24 stress steps without crossing the latency threshold. Its `escalate` outcome came from benchmark probe failures — context decay and over-expansion — not from operational collapse under stress. The two models make a useful pair: Mistral scored better on the benchmark but became unusable at scale; Phi-4 stayed operationally alive but cannot be trusted without oversight. A standard capability score would rank Mistral ahead. The scaffold separates them correctly.

Phi-3-mini and SmolLM followed a different abort pathway: over-expansion, near-cap pressure, context decay, and persistent failure firing together. Both models collapsed under stress within the first two to three steps. SmolLM is the clearest negative case in the experiment — high total failures, the highest proportion of unrecoverable failures of any model tested, and near-immediate stress collapse that makes it unsuitable for any pipeline requiring more than a single-turn interaction.

| Model | Regime | Triggers fired | Probe failures (of 14) | Unrecoverable | First stress failure |
|---|---|---|---|---|---|
| Phi-4-mini-instruct-8bit | **escalate** | context decay, over-expansion | 7 | 3 | — |
| Meta-Llama-3.1-8B-Instruct-3bit | **escalate** | context decay, over-expansion | 9 | 4 | — |
| Mistral-7B-Instruct-v0.3 | **abort** | latency cliff, over-expansion, persistent failure | 4 | 1 | step 15 |
| Phi-3-mini-4k-instruct-4bit | **abort** | near-cap pressure, context decay | 11 | 3 | step 2 |
| SmolLM-1.7B-Instruct-4bit | **abort** | near-cap pressure, context decay | 12 | 6 | step 2 |

*Probe failures* = mean number of the 14 benchmark probes that failed contract evaluation per run. *Unrecoverable* = failures where no retry or repair is expected to succeed — these directly contribute to escalate or abort decisions. All regimes were stable across 6/6 baseline runs and preserved under parameter sweeps at temperature 0.5 and varied max-token budgets (128 and 256).

Figure 4 shows the failure breakdown more clearly. The recoverable/unrecoverable split is what separates models that merely struggled from those that should not be trusted without oversight. SmolLM failing 6 of its 12 probe failures unrecoverably is a different situation from Phi-4 failing 3 — even though Phi-4's total failure count is lower, both the scaffold and the table read correctly once you look at severity rather than just count.

**Figure 4 — Probe failure breakdown: recoverable vs unrecoverable**

![](figures/figure4_failure_breakdown.png)

The stability across temperature and token-budget variations strengthens the case that the scaffold is detecting something persistent about each model's operational character, not an artifact of a specific prompt or decoding configuration.

---

## What to Do When the Signal Fires

Detecting a failure mode is only useful if something happens as a result. I propose a two-layer response.

**Layer 1: Automated system response.** The intervention state the scaffold emits is machine-readable and designed to be consumed by a downstream system. An `escalate` or `abort` signal should trigger an immediate response in the running pipeline: halt execution, route output to human review before it is acted on, or fall back to a constrained recovery procedure. Think of this as a circuit breaker — the same principle that trips a breaker when a circuit draws more current than it can safely handle. The breaker does not diagnose the fault; it stops the damage before it spreads. LTE's intervention layer works the same way: when the operational signals exceed the threshold, the pipeline trips rather than continuing to run on a model that is no longer trustworthy.

**Layer 2: Logged audit trail.** Every scaffold run produces a structured summary artifact containing trigger states, failure classifications, and the final intervention recommendation. This artifact should be retained as part of the deployment record. If an organization runs this framework, receives an `escalate` or `abort` signal, overrides that signal without documentation, and harm follows, the log exists. That is what makes accountability auditable and harder to evade.

Governance frameworks name the relevant actors. What they cannot establish on their own is *when* a deploying organization should have known the model was unreliable — which is precisely the question that determines liability. The audit trail answers it. The gap between "the model failed" and "the deploying organization received an abort signal and continued operating the pipeline" is the gap between a policy statement and a mechanically defensible record. This framework is an attempt to close that gap and define what responsibilization (clear assignment of roles and accountability in the AI lifecycle) may look like.

---

## Who Should Care About This

Three groups in particular have a direct stake in this.

**ML engineers building agentic pipelines** need circuit-breaker logic and they usually have to build it themselves from scratch. LTE offers a reusable scaffold with an explicit intervention vocabulary that can be wired into any pipeline backend. Although the experiments are limited to locally run models, the expectation is that this same scaffold can be deployed in more complex environments with more capable models and still identify breakage.

**AI safety and reliability researchers** working on evaluation methodology will find the intervention-centered framing a useful complement to capability benchmarking. The finding that benchmark-failure counts and stress-regime outcomes can diverge sharply — as they did with Mistral — is a concrete demonstration of why operational reliability needs its own measurement track rather than being inferred from task-accuracy scores. The probe design, contract evaluation logic, and trigger taxonomy are all open problems with significant room for improvement, and the framework is structured to make those components independently replaceable.

**Government technologists and policy researchers** building procurement criteria or incident-response protocols will find the accountability layer directly applicable. The question "what should a deploying organization be required to demonstrate before putting an agentic model into a consequential workflow?" has a concrete technical answer here: run the scaffold, retain the output, and establish the escalation pathway before deployment rather than after an incident. That shifts accountability from the moment of harm backward to the moment of deployment, which is where it actually belongs.

The framework is currently local-model-only, which limits direct applicability to production cloud deployments. Extending it to API-hosted models is the next phase of the work, and the intervention logic is designed to transfer without modification — only the latency thresholds and backend configuration would need adjustment.

---

## Limitations

The framework was built and validated on Apple Silicon. Latency measurements in particular are hardware-dependent: the absolute threshold values used here would need recalibration for cloud-hosted or API-based models. The behavioral patterns — models entering stable regimes through reproducible pathways — should generalize, but that has to be demonstrated rather than assumed.

The probe contracts encode normative assumptions about what a passing response looks like. A one-sentence summary that answers the question in twenty-two words but uses a semicolon is a harder case than the current contracts handle cleanly. Edge cases like this require human calibration, and the right thresholds for an escalate-vs-abort boundary will differ across deployment contexts. The current thresholds are a starting point, set by engineering judgment and validated against experimental consistency, rather than a final answer.

The probe battery is compact by design. That is a strength for iteration speed and interpretability, but it means the current set tests the failure modes that appear most frequently in operational workflows rather than every possible way a model can go wrong. Domain-specific deployments — legal document review, medical triage support, financial modelling — would benefit from extended probe families tuned to the failure modes that matter in those contexts.

---

## Conclusion

Local Threshold Evaluation is a first attempt to define evaluation criteria, a battery of probes, and actionable triggers for when models quietly fail. The motivation comes from direct experience observing AI deployment in settings where teams are not trained to detect model failure and may miss the cues that a model is no longer usable. The scaffold helps define internal triggers that tell users when to stop a workflow, transfer to a different agent, or review model outputs over a defined context window.

Although these experiments were run on limited local hardware with locally hosted LLMs, the scaffold is designed to transfer to more resource-intensive deployments with minimal modification. My objective is to keep testing accountability frameworks that bridge the technical realities of real-time AI evaluation with human-facing responsibilization through tests, triggers, and actionable recommendations.

---

## Code and Reproducibility

The scaffold is implemented in Python under `lte/` and runs against any model with a compatible backend. Probe suites are defined in `suites/` as YAML files. A mock backend is included for smoke testing without a local model.

The five-model sweep results in this paper are documented in `results/weekend_sweep_full/`, including `report.md`, `baseline_phase_summary.json`, per-run artifacts under `runs/`, and the generated configs used for each run. The figures are generated directly from those artifacts. The configs directory contains example configurations for running the unified pipeline against a single model.

```bash
# Install
pip install -e ".[dev]"

# Example: run the benchmark + stress suite against a local model
lte unified --config configs/unified_weekend.yaml --run-id my_run --progress

# Smoke test with mock (no model required)
lte unified --config examples/unified_mock_config.yaml --run-id mock_demo
```

The repository is at [github.com/abeltran/local_token_expansion](https://github.com/abeltran/local_token_expansion).

---

*This is part of a broader research agenda on enforceable accountability for agentic AI in government and national-security-relevant contexts. The next phase applies the same intervention logic to hosted API models and tests whether the resulting signals can be integrated into procurement and incident-response protocols.*
