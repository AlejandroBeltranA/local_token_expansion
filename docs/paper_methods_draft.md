# Paper Methods Draft

## Methods

### Experimental Objective

The experiment is designed to identify observable language-model behaviors that justify intervention in a workflow. The unit of analysis is not aggregate task performance. The unit of analysis is the relationship between a measured behavioral signal and an intervention state: `continue`, `retry`, `repair`, `escalate`, or `abort`.

The current implementation uses local language models as an experimental substrate for refining probes, trigger logic, scoring, and artifact structure. The scaffold is intended to generalize to API-based models in later work without changing the underlying accountability logic.

### Experimental Scaffold

The scaffold combines three layers:

1. benchmark probes
2. rolling stress evaluation
3. trigger-based intervention mapping

Benchmark probes are short, machine-checkable tasks that elicit specific failure behaviors. Rolling stress evaluation measures whether those behaviors intensify or become operationally disqualifying as context accumulates. Trigger-based intervention mapping converts observed failures into an explicit accountability action.

### Probe Families

The benchmark battery is defined under `suites/` and grouped into four probe families.

#### Bounded-output probes

These probes test whether the model can remain within strict communication constraints on short operational tasks. They are intended to identify `over_expansion` behavior and to support `retry` decisions when failures appear recoverable.

Examples include:
- single-sentence incident summaries
- two-bullet policy deltas
- concise and detailed handoff-delta summaries

#### Structured-output probes

These probes test whether the model can produce machine-usable output under explicit formatting or schema constraints. They are intended to identify repairable failures, near-cap pressure, and bounded-output drift.

Examples include:
- incident JSON extraction
- invoice JSON extraction
- exact CSV emission
- exact line-oriented action extraction

#### State-integrity probes

These probes test whether the model preserves stable state, applies only current updates, and ignores stale instructions. They are intended to identify `context_decay`, especially when outputs remain superficially coherent.

Examples include:
- state reconciliation JSON
- latest-override selection
- latest-status extraction from noisy notes
- ledger carry-forward JSON

#### Persistent-failure probes

These probes test whether the model can still emit minimal actionable outputs after failure-relevant scenarios. They are intended to distinguish repairable misses from behavior that should justify stronger intervention.

Examples include:
- exact YAML incident status
- exact two-line retry/repair plan

### Rolling Stress Protocol

The rolling stress evaluation is implemented through a fixed-output incident-state prompt under growing context. Previous assistant outputs are inserted as read-only reference material. The prompt requires the model to produce exactly five ordered bullet points representing:

- current status
- current owner
- next action
- one risk
- one escalation condition

The stress prompt is designed to reveal:
- latency growth under context accumulation
- near-cap pressure
- persistent failure
- reduced adherence to a stable operational output contract

Stress mode stops when either the configured step limit is reached or the model enters persistent failure as defined by the configured failure threshold.

### Contract Evaluation

Each benchmark case includes embedded contract metadata in its suite definition. Contracts specify output shape requirements such as:

- exact sentence count
- exact bullet count
- required keys
- invariant preservation
- exact line-oriented fields

Contracts are evaluated automatically at run time. The evaluator also normalizes some superficially recoverable formatting artifacts, such as outer code fences on structured output, before scoring. This makes it possible to distinguish superficial formatting hygiene from more substantive failure.

Each contract also carries a `failure_class`:

- `recoverable`
- `unrecoverable`

This classification is used in the intervention layer. Recoverable failures support `retry` or `repair`; unrecoverable failures contribute to `escalate` or `abort`.

### Trigger Families

The scaffold uses five trigger families.

#### Over-expansion

This trigger fires when the model repeatedly violates bounded-output expectations on benchmark probes or when short-budget tasks push against output caps. It is intended to capture loss of bounded communication discipline.

#### Near-cap pressure

This trigger fires when outputs repeatedly approach generation limits, either in structured benchmark probes or during stress. It is intended to capture impending truncation and parse collapse.

#### Context decay

This trigger fires when state-integrity probes fail repeatedly or when stress behavior shows degradation tied to growing context. It is intended to capture failures of carried-state reliability rather than simple formatting errors.

#### Latency cliff

This trigger fires when stress latency exceeds a configured threshold after context has grown beyond the gating threshold. It is intended to capture operational unusability despite continuing semantic output.

#### Persistent failure

This trigger fires when the model reaches repeated non-recovering failure in stress or when unrecoverable failure probes fail in benchmark mode. It is intended to capture the point at which continued reliance is no longer justified.

### Intervention Mapping

Observed triggers are mapped to intervention states as follows:

- `continue`
  No trigger fires.
- `retry`
  Failures are isolated and recoverable.
- `repair`
  Failures are recoverable and primarily concern structured output or bounded-output formatting.
- `escalate`
  Trust is degraded through context decay, latency, or other unrecoverable-but-nonterminal signals.
- `abort`
  Persistent failure or sufficiently severe trigger combinations indicate that continued use is unjustified.

The intervention mapping is part of the experimental object. The purpose of the scaffold is to test whether these mappings are empirically defensible.

### Models And Parameter Sweeps

The completed sweep used five local models:

- Mistral-7B-Instruct-v0.3
- Meta-Llama-3.1-8B-Instruct-3bit
- Phi-3-mini-4k-instruct-4bit
- SmolLM-1.7B-Instruct-4bit
- Phi-4-mini-instruct-8bit

Baseline evaluation used:
- temperatures: `0.0`, `0.2`
- `max_tokens=192`
- seeds: `0`, `1`, `2`

This yielded six baseline runs per model.

Expansion evaluation used:
- temperature: `0.5`
- `max_tokens`: `128`, `256`
- seeds: `0`, `1`, `2`

This yielded six expansion runs per model.

The purpose of the parameter sweep was not hyperparameter optimization. It was to test whether intervention regimes remained stable under modest decoding and output-budget changes.

### Artifacts

Each unified run writes:

- `benchmark.jsonl`
- `stress.jsonl`
- `merged.jsonl`
- `summary.json`
- `report.md`

The summary artifact contains:
- benchmark contract-failure counts
- recoverable vs unrecoverable failure counts
- trigger summaries
- final intervention recommendation

The weekend sweep wrapper additionally writes aggregate outputs including:
- baseline phase summary
- expansion run summary
- progress heartbeat
- final sweep report

### Stability Assessment

Stability is assessed by comparing intervention outcomes across seeds and across the downstream expansion settings. The key quantities are:

- modal intervention regime per model
- trigger fire frequencies
- recoverable vs unrecoverable failure counts
- first gated stress failure step where applicable

The experiment is considered stable when intervention regimes remain consistent across these replications.

### Scope And Limitations

The current Methods section describes a local-model instantiation of the scaffold. This is deliberate. Local models provide a tractable environment for iterating on probes, triggers, and intervention policy. The broader research objective is to hold the scaffold fixed while extending it to API-based models in future work. That next step will allow the same accountability framework to be tested across different deployment substrates rather than remaining tied to local inference conditions alone.
