#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lte.backends.base import Backend
from lte.backends.mlx_backend import MLXBackend
from lte.backends.mock_backend import MockBackend

from interventions import choose_action
from verifiers import TaskSpec, evaluate_triggers


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run drift_v0 tasks and emit raw events JSONL.")
    parser.add_argument("--task-pack", action="append", required=True, help="Task JSONL files.")
    parser.add_argument("--output", required=True, help="Raw events output JSONL.")
    parser.add_argument("--model-name", required=True, help="Model display name.")
    parser.add_argument("--model-path", required=True, help="Model path for backend loading.")
    parser.add_argument("--backend", choices=("mlx", "mock"), default="mlx")
    parser.add_argument("--experiment-id", default=None, help="Override experiment_id in emitted rows.")
    parser.add_argument("--run-id", default=None, help="Optional run_id. Defaults to timestamped value.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument(
        "--history-max-chars",
        type=int,
        default=0,
        help="Optional max chars of prior turns to include in prompt context.",
    )
    parser.add_argument(
        "--e3-condition",
        choices=("1k", "4k"),
        default=None,
        help="Optional E3 condition label to emit (for degradation delta).",
    )
    default_registry = Path(__file__).resolve().parents[1] / "tasks" / "schema_registry.json"
    parser.add_argument(
        "--schema-registry",
        default=str(default_registry),
        help="Path to schema registry JSON for in-loop trigger checks.",
    )
    return parser.parse_args()


def load_tasks(task_packs: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_path in task_packs:
        path = Path(raw_path)
        with path.open("r", encoding="utf-8") as infile:
            for line in infile:
                if not line.strip():
                    continue
                rows.append(json.loads(line))
    return rows


def get_backend(name: str) -> Backend:
    if name == "mlx":
        return MLXBackend()
    return MockBackend()


def load_schema_registry(path: str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as infile:
        return json.load(infile)


def build_prompt(base_prompt: str, history: list[dict[str, str]], history_max_chars: int) -> str:
    if not history:
        return base_prompt
    history_parts = []
    for item in history:
        history_parts.append(f"Previous prompt:\n{item['prompt']}\nPrevious response:\n{item['response']}")
    history_text = "\n\n".join(history_parts)
    if history_max_chars and len(history_text) > history_max_chars:
        history_text = history_text[-history_max_chars:]
    return (
        "You are continuing a multi-turn task. Keep outputs consistent with prior state.\n\n"
        f"{history_text}\n\nCurrent prompt:\n{base_prompt}"
    )


def build_retry_prompt(action: str, original_prompt: str, prior_response: str) -> str:
    common = (
        "You must repair the prior answer and return only the corrected final answer.\n\n"
        f"Original instruction:\n{original_prompt}\n\n"
        f"Prior answer to repair:\n{prior_response}\n\n"
    )
    if action == "retry_schema_constrained":
        return (
            common
            + "Repair goal: strictly satisfy the requested format/schema. Output valid JSON only when JSON is requested."
        )
    if action == "retry_loop_break":
        return (
            common
            + "Repair goal: avoid repetition. Do not reuse repeated sentences/phrases from the prior answer."
        )
    if action == "retry_state_reconcile":
        return (
            common
            + "Repair goal: reconcile with prior state. Ensure fields are internally consistent with requested updates."
        )
    return common + "Repair goal: provide a corrected answer."


def _task_spec(row: dict[str, Any]) -> TaskSpec:
    max_words = row.get("max_words")
    sentences = row.get("sentences")
    return TaskSpec(
        verifier=row.get("verifier"),
        expected_schema=row.get("expected_schema"),
        max_words=int(max_words) if max_words is not None else None,
        sentences=int(sentences) if sentences is not None else None,
    )


def _has_failure(flags: Any) -> bool:
    return bool(flags.schema_failure or flags.repetition_loop or flags.state_contradiction)


def _apply_reset(history: list[dict[str, str]], snapshot_prompt: str, snapshot_response: str) -> list[dict[str, str]]:
    # Minimal snapshot keeps only the latest interaction to limit context carryover after reset.
    return [{"prompt": snapshot_prompt, "response": snapshot_response}]


def emit_events(args: argparse.Namespace) -> int:
    rows = load_tasks(args.task_pack)
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_task[str(row.get("task_id", ""))].append(row)
    for task_rows in by_task.values():
        task_rows.sort(key=lambda item: int(item.get("turn", 1)))

    backend = get_backend(args.backend)
    schema_registry = load_schema_registry(args.schema_registry)
    run_id = args.run_id or f"drift_v0_{int(time.time())}"
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    event_count = 0
    attempted_recovery_by_episode: dict[str, bool] = {}
    previous_response_by_episode: dict[str, str] = {}
    previous_payload_by_episode: dict[str, Any] = {}

    with output_path.open("w", encoding="utf-8") as outfile:
        for task_id in sorted(by_task):
            task_rows = by_task[task_id]
            episode_id = f"{run_id}:{task_id}"
            history: list[dict[str, str]] = []
            for row in task_rows:
                prompt = str(row.get("prompt", ""))
                prompt_with_history = build_prompt(prompt, history, args.history_max_chars)
                experiment_id = args.experiment_id or str(row.get("experiment_id", "unknown"))
                turn = int(row.get("turn", 1))
                task_spec = _task_spec(row)
                result = backend.generate(
                    model_path=args.model_path,
                    model_name=args.model_name,
                    prompt_text=prompt_with_history,
                    system_text=None,
                    max_tokens=args.max_tokens,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    seed=args.seed,
                )

                evaluation = evaluate_triggers(
                    response_text=result.output_text,
                    previous_response=previous_response_by_episode.get(episode_id),
                    previous_payload=previous_payload_by_episode.get(episode_id),
                    task_spec=task_spec,
                    schema_registry=schema_registry,
                    event=row,
                )
                decision = choose_action(
                    evaluation.flags,
                    attempted_recovery_by_episode.get(episode_id, False),
                )

                event = {
                    "run_id": run_id,
                    "experiment_id": experiment_id,
                    "task_id": task_id,
                    "episode_id": episode_id,
                    "model": args.model_name,
                    "seed": args.seed,
                    "turn": turn,
                    "prompt": prompt,
                    "response": result.output_text,
                    "max_tokens": args.max_tokens,
                    "tokens_in": result.input_tokens,
                    "tokens_out": result.output_tokens,
                    "latency_ms": result.latency_ms,
                    "verifier": row.get("verifier"),
                    "expected_schema": row.get("expected_schema"),
                    "max_words": row.get("max_words"),
                    "sentences": row.get("sentences"),
                    "family": row.get("family"),
                    "schema_failure": evaluation.flags.schema_failure,
                    "repetition_loop": evaluation.flags.repetition_loop,
                    "state_contradiction": evaluation.flags.state_contradiction,
                    "intervention_action": decision.intervention_action,
                    "recovered": decision.recovered,
                    "escalated": decision.escalated,
                    "attempt_kind": "primary",
                    "parent_turn": None,
                    "policy_applied": decision.intervention_action,
                }
                if args.e3_condition is not None:
                    event["e3_condition"] = args.e3_condition
                if row.get("expected_state") is not None:
                    event["expected_state"] = row.get("expected_state")

                outfile.write(json.dumps(event) + "\n")
                event_count += 1

                has_failure = _has_failure(evaluation.flags)
                retry_written = False

                if decision.intervention_action.startswith("retry_"):
                    attempted_recovery_by_episode[episode_id] = True
                    retry_prompt = build_retry_prompt(
                        action=decision.intervention_action,
                        original_prompt=prompt,
                        prior_response=result.output_text,
                    )
                    retry_result = backend.generate(
                        model_path=args.model_path,
                        model_name=args.model_name,
                        prompt_text=retry_prompt,
                        system_text=None,
                        max_tokens=args.max_tokens,
                        temperature=args.temperature,
                        top_p=args.top_p,
                        seed=args.seed,
                    )
                    retry_eval = evaluate_triggers(
                        response_text=retry_result.output_text,
                        previous_response=result.output_text,
                        previous_payload=previous_payload_by_episode.get(episode_id),
                        task_spec=task_spec,
                        schema_registry=schema_registry,
                        event=row,
                    )
                    retry_decision = choose_action(retry_eval.flags, attempted_recovery=True)
                    retry_event = {
                        "run_id": run_id,
                        "experiment_id": experiment_id,
                        "task_id": task_id,
                        "episode_id": episode_id,
                        "model": args.model_name,
                        "seed": args.seed,
                        "turn": turn,
                        "prompt": retry_prompt,
                        "response": retry_result.output_text,
                        "max_tokens": args.max_tokens,
                        "tokens_in": retry_result.input_tokens,
                        "tokens_out": retry_result.output_tokens,
                        "latency_ms": retry_result.latency_ms,
                        "verifier": row.get("verifier"),
                        "expected_schema": row.get("expected_schema"),
                        "max_words": row.get("max_words"),
                        "sentences": row.get("sentences"),
                        "family": row.get("family"),
                        "schema_failure": retry_eval.flags.schema_failure,
                        "repetition_loop": retry_eval.flags.repetition_loop,
                        "state_contradiction": retry_eval.flags.state_contradiction,
                        "intervention_action": retry_decision.intervention_action,
                        "recovered": retry_decision.recovered,
                        "escalated": retry_decision.escalated,
                        "attempt_kind": "retry",
                        "parent_turn": turn,
                        "policy_applied": retry_decision.intervention_action,
                    }
                    if args.e3_condition is not None:
                        retry_event["e3_condition"] = args.e3_condition
                    if row.get("expected_state") is not None:
                        retry_event["expected_state"] = row.get("expected_state")
                    outfile.write(json.dumps(retry_event) + "\n")
                    event_count += 1
                    retry_written = True

                    retry_has_failure = _has_failure(retry_eval.flags)
                    if retry_has_failure and retry_decision.intervention_action == "reset_session_minimal_context":
                        history = _apply_reset(history, prompt, retry_result.output_text)
                    else:
                        history.append({"prompt": prompt, "response": retry_result.output_text})

                    previous_response_by_episode[episode_id] = retry_result.output_text
                    previous_payload_by_episode[episode_id] = retry_eval.parsed_payload
                    if retry_has_failure:
                        attempted_recovery_by_episode[episode_id] = True
                    else:
                        attempted_recovery_by_episode[episode_id] = False

                if retry_written:
                    continue

                if has_failure and decision.intervention_action == "reset_session_minimal_context":
                    history = _apply_reset(history, prompt, result.output_text)
                    attempted_recovery_by_episode[episode_id] = True
                else:
                    history.append({"prompt": prompt, "response": result.output_text})
                    if has_failure:
                        attempted_recovery_by_episode[episode_id] = True
                    else:
                        attempted_recovery_by_episode[episode_id] = False

                previous_response_by_episode[episode_id] = result.output_text
                previous_payload_by_episode[episode_id] = evaluation.parsed_payload

    return event_count


def main() -> None:
    args = parse_args()
    emitted = emit_events(args)
    print(f"emitted_events={emitted}")


if __name__ == "__main__":
    main()
