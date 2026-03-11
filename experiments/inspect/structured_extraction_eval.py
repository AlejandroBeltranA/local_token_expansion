from __future__ import annotations

from pathlib import Path


try:
    from inspect_ai import Task, task
    from inspect_ai.dataset import json_dataset
    from inspect_ai.solver import generate, system_message
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Inspect is not installed. Install it before running the Inspect spike."
    ) from exc

from scorers import structured_reliability


DATASET = Path(__file__).resolve().parent / "datasets" / "structured_extraction.jsonl"


@task
def structured_extraction_spike(max_tokens: int = 128):
    return Task(
        dataset=json_dataset(str(DATASET)),
        solver=[
            system_message("Return only valid JSON that matches the requested schema."),
            generate(),
        ],
        scorer=structured_reliability(max_tokens=max_tokens),
        message_limit=4,
        token_limit=max_tokens * 4,
        metadata={
            "project": "lte-inspect-spike",
            "suite": "structured_extraction",
        },
    )
