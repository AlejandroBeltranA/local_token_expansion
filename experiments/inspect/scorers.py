from __future__ import annotations

import json


try:
    from inspect_ai.scorer import Score, Target, mean, scorer
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Inspect is not installed. Install it before running the Inspect spike."
    ) from exc


@scorer(
    metrics={
        "valid_json": [mean()],
        "near_cap": [mean()],
    }
)
def structured_reliability(max_tokens: int = 128, near_cap_fraction: float = 0.95):
    async def score(state, target: Target):
        answer = state.output.completion
        try:
            json.loads(answer)
            valid_json = 1
        except json.JSONDecodeError:
            valid_json = 0

        near_cap = 1 if len(answer.split()) >= int(max_tokens * near_cap_fraction) else 0

        return Score(
            value={
                "valid_json": valid_json,
                "near_cap": near_cap,
            },
            answer=answer,
            metadata={
                "expected_schema": target.text,
                "token_budget": max_tokens,
                "near_cap_fraction": near_cap_fraction,
            },
        )

    return score
