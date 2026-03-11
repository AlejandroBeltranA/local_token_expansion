#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from interventions import choose_action
from verifiers import TaskSpec, evaluate_triggers

PROTOCOL_FIELDS = [
    "run_id",
    "experiment_id",
    "task_id",
    "model",
    "seed",
    "turn",
    "prompt",
    "response",
    "tokens_in",
    "tokens_out",
    "latency_ms",
    "schema_failure",
    "repetition_loop",
    "state_contradiction",
    "intervention_action",
    "recovered",
    "escalated",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate drift-v0 trigger flags and interventions.")
    parser.add_argument("--input", required=True, help="Input JSONL with model turn events.")
    parser.add_argument("--output", required=True, help="Output JSONL with evaluated events.")
    parser.add_argument(
        "--task-pack",
        action="append",
        default=[],
        help="Task JSONL file(s) for verifier metadata lookup. Can be passed multiple times.",
    )
    default_registry = Path(__file__).resolve().parents[1] / "tasks" / "schema_registry.json"
    parser.add_argument(
        "--schema-registry",
        default=str(default_registry),
        help="Path to schema registry JSON.",
    )
    return parser.parse_args()


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as infile:
        return json.load(infile)


def _load_task_index(task_pack_paths: list[str]) -> dict[tuple[str, str | None, int | None], dict[str, Any]]:
    index: dict[tuple[str, str | None, int | None], dict[str, Any]] = {}
    for raw_path in task_pack_paths:
        path = Path(raw_path)
        with path.open("r", encoding="utf-8") as infile:
            for line in infile:
                if not line.strip():
                    continue
                row = json.loads(line)
                key = (
                    str(row.get("task_id", "")),
                    row.get("experiment_id"),
                    int(row["turn"]) if row.get("turn") is not None else None,
                )
                index[key] = row
    return index


def _lookup_task_meta(event: dict[str, Any], task_index: dict[tuple[str, str | None, int | None], dict[str, Any]]) -> dict[str, Any] | None:
    task_id = str(event.get("task_id", ""))
    experiment_id = event.get("experiment_id")
    turn_value = event.get("turn")
    turn = int(turn_value) if turn_value is not None else None
    keys = [
        (task_id, experiment_id, turn),
        (task_id, experiment_id, None),
        (task_id, None, turn),
        (task_id, None, None),
    ]
    for key in keys:
        row = task_index.get(key)
        if row is not None:
            return row
    return None


def _task_spec_from(event: dict[str, Any], task_meta: dict[str, Any] | None) -> TaskSpec:
    def _pick(field: str) -> Any:
        if field in event:
            return event.get(field)
        if task_meta:
            return task_meta.get(field)
        return None

    max_words = _pick("max_words")
    sentences = _pick("sentences")
    return TaskSpec(
        verifier=_pick("verifier"),
        expected_schema=_pick("expected_schema"),
        max_words=int(max_words) if max_words is not None else None,
        sentences=int(sentences) if sentences is not None else None,
    )


def _build_output_row(event: dict[str, Any], computed: dict[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {}
    merged = dict(event)
    merged.update(computed)
    for field in PROTOCOL_FIELDS:
        if field in {"schema_failure", "repetition_loop", "state_contradiction", "recovered", "escalated"}:
            row[field] = bool(merged.get(field, False))
        else:
            row[field] = merged.get(field)
    for key, value in merged.items():
        if key not in row:
            row[key] = value
    return row


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    schema_registry = _load_json(Path(args.schema_registry))
    task_index = _load_task_index(args.task_pack)

    previous_by_episode: dict[str, str] = {}
    previous_payload_by_episode: dict[str, Any] = {}
    recovery_attempted_by_episode: dict[str, bool] = {}

    with input_path.open("r", encoding="utf-8") as infile, output_path.open(
        "w", encoding="utf-8"
    ) as outfile:
        for line in infile:
            if not line.strip():
                continue
            event = json.loads(line)
            episode = event.get("episode_id") or f"{event.get('run_id','run')}:{event.get('task_id','task')}"
            response = event.get("response", "")

            task_meta = _lookup_task_meta(event, task_index)
            task_spec = _task_spec_from(event, task_meta)
            evaluation = evaluate_triggers(
                response_text=response,
                previous_response=previous_by_episode.get(episode),
                previous_payload=previous_payload_by_episode.get(episode),
                task_spec=task_spec,
                schema_registry=schema_registry,
                event=event,
            )
            decision = choose_action(evaluation.flags, recovery_attempted_by_episode.get(episode, False))
            output_row = _build_output_row(
                event=event,
                computed={
                    "schema_failure": evaluation.flags.schema_failure,
                    "repetition_loop": evaluation.flags.repetition_loop,
                    "state_contradiction": evaluation.flags.state_contradiction,
                    "intervention_action": decision.intervention_action,
                    "recovered": decision.recovered,
                    "escalated": decision.escalated,
                },
            )

            has_failure = (
                evaluation.flags.schema_failure
                or evaluation.flags.repetition_loop
                or evaluation.flags.state_contradiction
            )
            if not has_failure:
                recovery_attempted_by_episode[episode] = False
            elif decision.intervention_action.startswith("retry_"):
                recovery_attempted_by_episode[episode] = True
            elif decision.escalated:
                recovery_attempted_by_episode[episode] = True
            else:
                recovery_attempted_by_episode[episode] = False

            previous_by_episode[episode] = response
            previous_payload_by_episode[episode] = evaluation.parsed_payload

            outfile.write(json.dumps(output_row) + "\n")


if __name__ == "__main__":
    main()
