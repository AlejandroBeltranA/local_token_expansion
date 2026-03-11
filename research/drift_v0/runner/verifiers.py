from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class TriggerFlags:
    schema_failure: bool
    repetition_loop: bool
    state_contradiction: bool


@dataclass
class TaskSpec:
    verifier: str | None = None
    expected_schema: str | None = None
    max_words: int | None = None
    sentences: int | None = None


@dataclass
class TriggerEvaluation:
    flags: TriggerFlags
    parsed_payload: Any


def _parse_json(response_text: str) -> Any:
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return None


def _is_type(value: Any, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "array":
        return isinstance(value, list)
    return True


def _validate_json_schema(instance: Any, schema: dict[str, Any]) -> bool:
    schema_type = schema.get("type")
    if isinstance(schema_type, str) and not _is_type(instance, schema_type):
        return False

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                return False

        properties = schema.get("properties", {})
        additional_properties = schema.get("additionalProperties", True)
        if additional_properties is False:
            allowed = set(properties.keys())
            for key in instance:
                if key not in allowed:
                    return False

        for key, subschema in properties.items():
            if key in instance and isinstance(subschema, dict):
                if not _validate_json_schema(instance[key], subschema):
                    return False

    numeric = isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if numeric:
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and instance < minimum:
            return False
        if maximum is not None and instance > maximum:
            return False

    return True


def _count_sentences(text: str) -> int:
    chunks = [chunk.strip() for chunk in re.split(r"[.!?]+|\n+", text) if chunk.strip()]
    return len(chunks)


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def schema_failure(
    response_text: str,
    task_spec: TaskSpec | None,
    schema_registry: dict[str, Any] | None,
    parsed_payload: Any | None = None,
) -> bool:
    task_spec = task_spec or TaskSpec()
    verifier = task_spec.verifier or ""
    payload = parsed_payload if parsed_payload is not None else _parse_json(response_text)

    if verifier == "length_and_sentence_count":
        if task_spec.max_words is not None and _word_count(response_text) > task_spec.max_words:
            return True
        if task_spec.sentences is not None and _count_sentences(response_text) != task_spec.sentences:
            return True
        return False

    expects_json = bool(task_spec.expected_schema) or verifier in {"schema_json", "state_consistency"}
    if not expects_json:
        return False
    if payload is None:
        return True

    expected_schema = task_spec.expected_schema
    if not expected_schema:
        return False

    registry = schema_registry or {}
    schema = registry.get(expected_schema)
    if not isinstance(schema, dict):
        return True

    return not _validate_json_schema(payload, schema)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _ngrams(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def _duplicate_sentence_ratio(text: str) -> float:
    sentences = [chunk.strip().lower() for chunk in re.split(r"[.!?]+|\n+", text) if chunk.strip()]
    if not sentences:
        return 0.0
    unique_count = len(set(sentences))
    return (len(sentences) - unique_count) / len(sentences)


def repetition_loop(response_text: str, previous_response: str | None) -> bool:
    if _duplicate_sentence_ratio(response_text) >= 0.34:
        return True
    if not previous_response:
        return False

    norm_curr = " ".join(response_text.lower().split())
    norm_prev = " ".join(previous_response.lower().split())
    if norm_curr == norm_prev:
        return True

    curr_tokens = _tokenize(norm_curr)
    prev_tokens = _tokenize(norm_prev)
    if not curr_tokens or not prev_tokens:
        return False

    curr_4grams = _ngrams(curr_tokens, 4)
    prev_4grams = _ngrams(prev_tokens, 4)
    if curr_4grams:
        ngram_overlap = len(curr_4grams & prev_4grams) / max(1, len(curr_4grams))
        if ngram_overlap >= 0.6:
            return True

    token_overlap = len(set(curr_tokens) & set(prev_tokens)) / max(1, len(set(curr_tokens)))
    return token_overlap >= 0.9


def _get_expected_state(event: dict[str, Any]) -> dict[str, Any] | None:
    for key in ("expected_state", "state_expected", "target_state"):
        value = event.get(key)
        if isinstance(value, dict):
            return value
    return None


def _is_state_like(payload: Any, task_spec: TaskSpec | None) -> bool:
    if not isinstance(payload, dict):
        return False
    if {"user", "balance", "last_action"}.issubset(payload.keys()):
        return True
    if not task_spec:
        return False
    return task_spec.expected_schema in {"state_v1", "state_check_v1"} or task_spec.verifier == "state_consistency"


def _action_balance_direction(action: str) -> int:
    lowered = action.lower()
    if any(word in lowered for word in ("withdraw", "debit", "spend", "charge")):
        return -1
    if any(word in lowered for word in ("deposit", "credit", "refund", "income")):
        return 1
    return 0


def state_contradiction(
    parsed_payload: Any,
    previous_payload: Any,
    task_spec: TaskSpec | None,
    event: dict[str, Any] | None = None,
) -> bool:
    if not isinstance(parsed_payload, dict):
        return False

    if parsed_payload.get("consistency_check") is False:
        return True

    event = event or {}
    expected_state = _get_expected_state(event)
    if expected_state:
        for key, value in expected_state.items():
            if key in parsed_payload and parsed_payload[key] != value:
                return True

    if not _is_state_like(parsed_payload, task_spec):
        return False

    if not isinstance(previous_payload, dict):
        return False

    prev_user = previous_payload.get("user")
    curr_user = parsed_payload.get("user")
    if isinstance(prev_user, str) and isinstance(curr_user, str) and prev_user != curr_user:
        return True

    prev_balance = previous_payload.get("balance")
    curr_balance = parsed_payload.get("balance")
    action = parsed_payload.get("last_action")
    if isinstance(prev_balance, int) and isinstance(curr_balance, int) and isinstance(action, str):
        direction = _action_balance_direction(action)
        delta = curr_balance - prev_balance
        if direction < 0 and delta > 0:
            return True
        if direction > 0 and delta < 0:
            return True

    return False

def evaluate_triggers(
    response_text: str,
    previous_response: str | None,
    previous_payload: Any,
    task_spec: TaskSpec | None,
    schema_registry: dict[str, Any] | None,
    event: dict[str, Any] | None = None,
) -> TriggerEvaluation:
    parsed_payload = _parse_json(response_text)
    flags = TriggerFlags(
        schema_failure=schema_failure(response_text, task_spec=task_spec, schema_registry=schema_registry, parsed_payload=parsed_payload),
        repetition_loop=repetition_loop(response_text, previous_response),
        state_contradiction=state_contradiction(
            parsed_payload=parsed_payload,
            previous_payload=previous_payload,
            task_spec=task_spec,
            event=event,
        ),
    )
    return TriggerEvaluation(flags=flags, parsed_payload=parsed_payload)
