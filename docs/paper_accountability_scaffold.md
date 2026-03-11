# Paper Framing: Accountability Scaffold

## Abstract

We present an empirical accountability scaffold for language-model deployment. The scaffold is designed to identify observable behaviors that justify user or system intervention during real workflows, and to map those behaviors to explicit actions: `retry`, `repair`, `escalate`, or `abort`. Rather than centering task accuracy or model ranking, the framework probes intervention-relevant failure modes including over-expansion, near-cap pressure, context decay, latency cliffs, and persistent failure. We instantiate the scaffold on local language models using compact, machine-checkable probes and a rolling stress protocol, showing that different models cross intervention thresholds through distinct behavioral pathways. The local setup serves as an experimental substrate for refining triggers, scorers, and intervention policy; the same scaffold is intended to extend to API-hosted models in future work, enabling cross-deployment comparisons under a shared accountability framework.

## Thesis

This work presents an intervention-centered empirical scaffold for language-model accountability. The scaffold uses compact, machine-checkable probes and rolling stress tests to identify behaviors that justify `retry`, `repair`, `escalate`, or `abort` decisions in live workflows. Local models provide the first substrate for developing and validating the scaffold because they are cheap and fast to iterate on. The broader aim is to carry the same intervention framework into API-based model evaluation so that deployment decisions can be made using shared behavioral criteria rather than ad hoc impressions of model quality.

## Core Question

Which observable behaviors in a language-model workflow are strong enough to justify intervention, and what intervention should follow?

## Intervention States

- `continue`: no meaningful trust degradation observed
- `retry`: bounded failure likely recoverable with another constrained attempt
- `repair`: deterministic cleanup or schema correction is justified
- `escalate`: behavior has undermined trust enough to require higher-assurance oversight
- `abort`: continued reliance is unjustified

## Trigger Families

- `over_expansion`
  The model stops respecting bounded communication constraints.
- `near_cap_pressure`
  The model repeatedly approaches generation limits and risks truncation or parse collapse.
- `context_decay`
  The model stops preserving or correctly applying carried state.
- `latency_cliff`
  The model remains semantically functional but becomes operationally unusable.
- `persistent_failure`
  The model enters a repeated, non-recovering failure state.

## Experimental Scaffold

The maintained scaffold has four probe families:

- bounded-output probes
- structured-output probes
- state-integrity probes
- rolling stress probes

These are not capability benchmarks. They are intervention probes designed to elicit accountability-relevant behavior.

## Current Local Role

Local models are the current substrate for iterating on:

- trigger validity
- scorer design
- intervention policy
- artifact structure

The point of the local experiments is to validate the scaffold, not to optimize for local-model leaderboard performance.

## Next Deployment Substrate

The next step is to run the same scaffold against API-based models. The intervention logic should remain fixed while the deployment substrate changes. That allows comparison across local and hosted models using shared behavioral criteria.

## Paper Outline

### 1. Introduction

Introduce intervention as the unit of analysis and define the scaffold as an empirical method for deciding when continued reliance is no longer justified.

### 2. Accountability Framework

Define the trigger families and intervention states.

### 3. Experimental Scaffold

Describe the compact probe battery, contract evaluation, rolling stress protocol, and unified artifacts.

### 4. Probe Families

Present bounded-output, structured-output, state-integrity, and rolling-stress probes as intervention probes.

### 5. Methods

Document the maintained implementation under `lte/`, `suites/`, and `configs/`, along with trigger rules and contract evaluation.

### 6. Results

Report trigger pathways, intervention frequencies, and representative outputs. Emphasize different behavioral pathways to intervention rather than model ranking.

### 7. Discussion

Argue that intervention thresholds can be studied empirically using compact, repeatable probes.

### 8. Limitations

Discuss evaluator brittleness, deployment-specific latency effects, and current local-only scope.

### 9. Future Work

Apply the same scaffold to API models and compare intervention signatures across deployment settings.
