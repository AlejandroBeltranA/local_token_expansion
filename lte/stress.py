from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from lte.backends.base import Backend
from lte.config import ModelConfig, RunConfig, StressConfig
from lte.metrics import length_overrun_rate, runaway_continuation_score
from lte.schema import GenerationRecord


@dataclass(frozen=True)
class StepFailure:
    is_failure: bool
    reasons: list[str]


def evaluate_step_failure(
    *,
    output_text: str,
    output_tokens: int,
    max_tokens: int,
    latency_ms: int,
    input_tokens: int,
    context_fraction: float | None,
    stress: StressConfig,
) -> StepFailure:
    reasons: list[str] = []

    if stress.failure.max_latency_ms is not None and latency_ms > int(stress.failure.max_latency_ms):
        gated = False
        if stress.failure.latency_only_after_input_tokens is not None:
            gated = gated or (input_tokens >= int(stress.failure.latency_only_after_input_tokens))
        if stress.failure.latency_only_after_context_fraction is not None:
            if context_fraction is not None:
                gated = gated or (
                    context_fraction >= float(stress.failure.latency_only_after_context_fraction)
                )
        # If no gating thresholds are set, apply latency failure immediately.
        if (
            stress.failure.latency_only_after_input_tokens is None
            and stress.failure.latency_only_after_context_fraction is None
        ) or gated:
            reasons.append("latency")

    if stress.failure.max_rcs is not None:
        rcs = runaway_continuation_score(output_text)
        if rcs >= float(stress.failure.max_rcs):
            reasons.append("rcs")

    if stress.failure.fail_on_lorr:
        if length_overrun_rate(output_tokens=output_tokens, max_tokens=max_tokens) == 1:
            reasons.append("lorr")

    return StepFailure(is_failure=len(reasons) > 0, reasons=reasons)


def _build_context(*, base_prompt: str, history: list[str], stress: StressConfig) -> str:
    def clip(s: str, n: int) -> str:
        if n <= 0:
            return ""
        if len(s) <= n:
            return s
        # Keep the end; recent tokens tend to be most salient.
        return s[-n:]

    history_clipped = [clip(h, int(stress.history_max_chars_per_step)) for h in history]
    if stress.history_max_chars_total is not None:
        total = "\n\n".join(history_clipped)
        total = clip(total, int(stress.history_max_chars_total))
        history_clipped = [total] if total else []

    if stress.context_growth == "append":
        ref = history_clipped
    elif stress.context_growth == "sliding":
        k = max(0, int(stress.sliding_window_steps))
        ref = history_clipped[-k:] if k else []
    else:
        raise ValueError("stress.context_growth must be one of: append, sliding")

    if not ref:
        return (
            "TASK:\n"
            f"{base_prompt}\n\n"
            "CONSTRAINTS:\n"
            "- Do not quote or copy from any previous outputs.\n"
            "- If prior outputs exist, treat them as read-only reference.\n"
        )

    reference = "\n\n---\n\n".join(ref)
    # Put reference earlier and end with constraints so the model is less likely to continue the reference text.
    return (
        "READ-ONLY REFERENCE (previous assistant outputs; do NOT quote, copy, or continue these):\n"
        "-----BEGIN REFERENCE-----\n"
        f"{reference}\n"
        "-----END REFERENCE-----\n\n"
        "TASK:\n"
        f"{base_prompt}\n\n"
        "CONSTRAINTS:\n"
        "- Do not quote or copy any text from the REFERENCE.\n"
        "- Do not include the reference markers in your output.\n"
        "- Answer the TASK only.\n"
    )

    raise ValueError("unreachable")


def run_stress(
    *,
    cfg: RunConfig,
    backend: Backend,
    model: ModelConfig,
    run_id: str,
    progress: bool = False,
) -> list[dict[str, Any]]:
    """
    Runs a rolling prompt loop until:
    - max_steps reached, OR
    - max_runtime_sec exceeded, OR
    - sustained failure (N consecutive failed steps) is observed.

    Returns generation-record-like rows (safe for JSONL + reporting).
    """
    stress = cfg.stress
    if not stress.enabled:
        return []

    t0 = time.time()
    history: list[str] = []
    consecutive_failures = 0
    rows: list[dict[str, Any]] = []

    for step in range(int(stress.max_steps)):
        if (time.time() - t0) > float(stress.max_runtime_sec):
            break

        prompt_text = _build_context(base_prompt=stress.prompt, history=history, stress=stress)
        max_tokens = cfg.generation.max_tokens

        result = backend.generate(
            model_path=model.path,
            model_name=model.name,
            prompt_text=prompt_text,
            system_text=stress.system,
            max_tokens=max_tokens,
            temperature=cfg.generation.temperature,
            top_p=cfg.generation.top_p,
            seed=cfg.generation.seed,
        )

        failure = evaluate_step_failure(
            output_text=result.output_text,
            output_tokens=result.output_tokens,
            max_tokens=max_tokens,
            latency_ms=result.latency_ms,
            input_tokens=result.input_tokens,
            context_fraction=(
                (result.input_tokens / max(1, int(model.context_limit_tokens)))
                if model.context_limit_tokens
                else None
            ),
            stress=stress,
        )
        consecutive_failures = consecutive_failures + 1 if failure.is_failure else 0

        history.append(result.output_text)

        row: dict[str, Any] = {
            **GenerationRecord(
                run_id=run_id,
                timestamp=GenerationRecord.now_timestamp(),
                model_name=model.name,
                backend=backend.name,
                model_revision=model.revision,
                suite_name="stress",
                prompt_id=f"step_{step:04d}",
                prompt_text=prompt_text,
                system_text=None,
                max_tokens=max_tokens,
                temperature=cfg.generation.temperature,
                top_p=cfg.generation.top_p,
                seed=cfg.generation.seed,
                output_text=result.output_text,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                token_count_method=result.token_count_method,
                stop_reason=result.stop_reason,
                latency_ms=result.latency_ms,
            ).to_dict(),
            "mode": "stress",
            "step": step,
            "is_failure": failure.is_failure,
            "failure_reasons": failure.reasons,
            "consecutive_failures": consecutive_failures,
            "failure_consecutive_required": int(stress.failure.consecutive),
        }
        if model.context_limit_tokens:
            row["context_limit_tokens"] = model.context_limit_tokens
            row["context_fraction"] = result.input_tokens / max(1, int(model.context_limit_tokens))

        rows.append(row)

        if progress:
            print(
                f"{model.name}\tstress\tstep={step}\tin={result.input_tokens}\tout={result.output_tokens}"
                f"\tfail={failure.is_failure}\tconsec={consecutive_failures}"
            )

        if consecutive_failures >= int(stress.failure.consecutive):
            break

    return rows
