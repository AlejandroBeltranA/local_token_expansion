# Paper Discussion And Limitations Draft

## Discussion

The central result of this work is that intervention-oriented model evaluation can be made empirical. The scaffold developed here does not ask whether a model is generally good or bad. It asks whether observed behavior provides enough evidence to justify continued reliance, constrained recovery, stronger oversight, or termination. The completed experiments show that this question can be operationalized through compact probes, explicit trigger families, and repeatable artifact generation.

The most important finding is that intervention regimes are stable across seeds and modest parameter changes. This matters because an accountability scaffold is only useful if it produces reliable signals rather than arbitrary labels. In the completed sweep, each tested model remained within the same modal intervention regime across all baseline runs, and those regimes were preserved in the downstream parameter sweeps. This suggests that the scaffold is identifying persistent behavioral pathways rather than transient prompt artifacts.

The second important finding is that different models cross intervention boundaries through different mechanisms. Some models fail primarily through latency-driven operational collapse, while others remain semantically coherent but repeatedly mishandle carried state or exceed bounded-output constraints. This distinction is critical for accountability. A system that becomes too slow under growing context does not present the same risk as a system that silently corrupts state while still sounding plausible. The scaffold makes those differences legible by mapping them to different trigger families and intervention outcomes.

The split between recoverable and unrecoverable failures also proved useful. This distinction is necessary for any framework that aims to justify different intervention intensities. A recoverable failure, such as bounded-output drift or a structured-output miss, may justify retry or repair. An unrecoverable failure, such as repeated state-integrity breakdown or persistent failure under stress, justifies escalation or abort. The present artifact layer makes that distinction explicit, which helps keep intervention logic tied to observable evidence rather than vague intuitions about model trustworthiness.

These findings support a broader claim about language-model accountability. In many deployments, what matters most is not absolute capability but intervention legitimacy. Users and downstream systems need to know when continued reliance is still defensible and when it is no longer justified. The scaffold offers one way of grounding that judgment in measurable behavior.

The current local-model experiments should be understood as a substrate for this broader accountability program. Local models were used because they provide a cheap and controllable environment for refining probes, scorers, trigger thresholds, and reporting logic. The goal is not to privilege local models as the most important deployment setting. The goal is to establish an intervention scaffold that can later be applied to API-hosted models under the same behavioral criteria. The long-term value of the scaffold comes from that portability.

The scaffold also helps sharpen what counts as a meaningful failure. Standard benchmark framing often collapses many qualitatively different errors into a single score. By contrast, the present framework treats failure as structured. Over-expansion, context decay, latency cliffs, near-cap pressure, and persistent failure are different accountability events, even when they all reduce trust. Treating them separately makes it possible to justify different responses and to compare models in terms of intervention pathways rather than generic performance rankings.

The strongest use of this scaffold is therefore not leaderboard construction. It is intervention-sensitive workflow evaluation. The framework is most informative when it reveals where a model can still be used safely with bounded recovery, where stronger oversight is required, and where continued reliance should stop altogether.

## Limitations

This work has several limitations.

First, the scaffold depends on evaluator design. Although the probe contracts and trigger logic are explicit, they still encode normative assumptions about what kinds of behavior should count as recoverable or unrecoverable. Some intervention boundaries may need further calibration against human judgment. This is particularly important for edge cases where output content is semantically close to correct but violates a strict structural contract.

Second, the current probe set is compact by design. That is a strength for iteration speed and interpretability, but it also limits coverage. The scaffold does not yet test all classes of failure that may matter in deployed systems. It emphasizes bounded output, structured outputs, state integrity, and rolling context stress. Other workflow risks may require additional probe families.

Third, the local setting introduces deployment-specific effects. Latency measurements, context behavior, and failure profiles depend in part on local hardware and inference conditions. This does not invalidate the scaffold, but it means that the present experiments should not be read as universal statements about the tested model families independent of deployment substrate.

Fourth, the current work does not yet validate the scaffold against API-hosted models. That extension is central to the broader research agenda. The present contribution is therefore a scaffold instantiation and validation in one setting, not a final cross-deployment intervention framework.

Fifth, some trigger families remain easier to study than others. Over-expansion, near-cap pressure, and latency cliffs are relatively straightforward to operationalize. Context decay is more difficult because it depends on whether state preservation and stale-versus-current instruction use are being scored in the right way. The current state-integrity probes are stronger than earlier versions of the experiment, but further refinement is still possible.

Sixth, a stable intervention regime should not be confused with a correct one. Stability is evidence that the scaffold is measuring something repeatable. It is not yet evidence that the trigger thresholds are fully calibrated to what users ought to do in every deployment setting. Further work should test whether the intervention mapping aligns with human judgments of justified reliance and intervention.

## Implications For Future Work

The next step is to hold the scaffold fixed while changing the deployment substrate. Applying the same probes, trigger logic, and intervention mapping to API-based models would allow direct comparison of intervention profiles across local and hosted systems. That comparison would clarify which intervention signals are robust across settings and which are deployment-specific.

A second priority is threshold calibration. The present work shows that the trigger families are measurable and stable enough to structure intervention decisions. Future work should examine whether the chosen thresholds best match human judgments of when retry, repair, escalation, or abort are warranted.

A third priority is workflow grounding. The scaffold already uses operationally motivated probes, but future work could test domain-specific adaptations in settings such as coding agents, document processing pipelines, or incident-response systems. The important constraint is that those adaptations should remain intervention-centered rather than drifting back into broad capability benchmarking.

## Closing Claim

This work argues that accountability for language-model deployment can be studied empirically by focusing on intervention thresholds rather than generic performance. A compact scaffold of probes, trigger rules, and intervention mappings is enough to reveal stable behavioral pathways that justify different forms of response. That is the main claim supported by the present experiments, and it is the foundation for extending the scaffold beyond local models in future work.
