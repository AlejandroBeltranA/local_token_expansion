# Evaluation Positioning

Local Token Expansion (LTE) is a local-first evaluation harness for operational degradation. It is designed to measure when an LLM stops being useful in a constrained workflow, especially under prompt growth, output caps, repetition pressure, latency pressure, and persistent failure states.

LTE complements standard evaluations. It is not a substitute for capability, factuality, safety, alignment, or preference evaluation.

## LTE vs Static Benchmarks

Static benchmarks usually ask whether a model can solve a fixed task. They are useful for capability measurement, regression testing, and broad comparison.

LTE asks a narrower operational question: does the model continue to behave usefully when workflow pressure increases? It measures output expansion, cap pressure, verbosity drift, repetition, latency, and sustained failure. A model can score well on a static task while still becoming unusable in a workflow because it runs long, repeats itself, violates a contract, or triggers repeated repair attempts.

LTE should therefore be read as a complement to static benchmarks, not as a replacement.

## LTE vs Human Preference Evaluation

Human preference evaluation usually captures which outputs people prefer along dimensions such as helpfulness, clarity, style, or perceived quality.

LTE does not ask which answer is preferred. It asks whether an answer remains inside an operational envelope. A verbose answer might be preferred by a human reviewer and still be a failure for a workflow that requires five short bullets, a fixed schema, or a bounded latency budget.

This makes LTE relevant to deployment monitoring and routing decisions, but it does not measure broad user satisfaction.

## LTE vs Agent Task Evaluation

Agent task evaluations often measure whether a system completes a multi-step task in an environment. Those evaluations are important for end-to-end autonomy and tool-use reliability.

LTE is lower-level. It focuses on degradation signals that can cause agent workflows to fail: output contract violations, runaway continuation, near-cap completions, latency cliffs, and persistent failure states. These signals can be used inside agent systems to decide when to retry, repair, escalate, or abort.

LTE does not currently evaluate full agent planning, tool correctness, environment interaction, or task completion.

## Where LTE Fits

LTE is useful for:

- comparing local models under the same workflow pressure;
- detecting verbosity drift and repetition before downstream systems fail;
- defining retry, repair, escalation, and abort policies;
- supporting local model routing decisions;
- monitoring operational degradation in constrained deployments;
- preserving reproducible artifacts for model behavior analysis.

The best use case is not "which model is best overall?" but "when does this model stop being usable for this workflow?"

## Limitations

- LTE currently measures operational degradation, not broad model capability.
- Metrics do not establish semantic correctness unless task-specific checks are added.
- The current probes may not cover reasoning, truthfulness, safety, or alignment.
- Local hardware affects latency measurements and can change stress behavior.
- Prompt suites and stress policies are workflow-specific.
- Mock outputs are useful for pipeline verification, not model-quality evidence.
- Checked-in artifacts should not be interpreted as universal model rankings.

## Near-Term Extensions

- Add task-correctness probes next to operational metrics.
- Stabilize result schemas for easier longitudinal comparison.
- Add richer model-routing and escalation-policy examples.
- Expand Inspect integration for teams that already use eval tooling.
- Add hardware and runtime metadata to make latency comparisons easier to interpret.
- Improve separation between maintained harness paths and exploratory research tracks.
