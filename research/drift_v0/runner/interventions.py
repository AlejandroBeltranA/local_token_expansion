from __future__ import annotations

from dataclasses import dataclass

from verifiers import TriggerFlags


@dataclass
class InterventionDecision:
    intervention_action: str
    recovered: bool
    escalated: bool


def choose_action(flags: TriggerFlags, attempted_recovery: bool) -> InterventionDecision:
    if not (flags.schema_failure or flags.repetition_loop or flags.state_contradiction):
        return InterventionDecision(intervention_action="none", recovered=attempted_recovery, escalated=False)

    if not attempted_recovery:
        if flags.schema_failure:
            return InterventionDecision("retry_schema_constrained", recovered=False, escalated=False)
        if flags.repetition_loop:
            return InterventionDecision("retry_loop_break", recovered=False, escalated=False)
        if flags.state_contradiction:
            return InterventionDecision("retry_state_reconcile", recovered=False, escalated=False)

    if flags.state_contradiction:
        return InterventionDecision("escalate_human_review", recovered=False, escalated=True)
    return InterventionDecision("reset_session_minimal_context", recovered=False, escalated=True)
