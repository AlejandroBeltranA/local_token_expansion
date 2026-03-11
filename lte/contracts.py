from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import yaml


@dataclass(frozen=True)
class ContractEvaluation:
    passed: bool
    output_mode: str | None
    failure_class: str
    recoverable_failure: bool
    failed_checks: list[str]
    satisfied_checks: list[str]
    parsed_payload: dict[str, Any] | list[Any] | None
    normalized_output_text: str
    outer_fences_stripped: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "output_mode": self.output_mode,
            "failure_class": self.failure_class,
            "recoverable_failure": self.recoverable_failure,
            "failed_checks": self.failed_checks,
            "satisfied_checks": self.satisfied_checks,
            "normalized_output_text": self.normalized_output_text,
            "outer_fences_stripped": self.outer_fences_stripped,
        }


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_'-]+", text)


def _sentences(text: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"[.!?]+", text) if part.strip()]
    return parts


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _bullet_lines(text: str) -> list[str]:
    bullets: list[str] = []
    for line in _lines(text):
        if re.match(r"^([-*]|\d+\.)\s+", line):
            bullets.append(re.sub(r"^([-*]|\d+\.)\s+", "", line).strip())
    return bullets


def _strip_outer_fences(text: str) -> tuple[str, bool]:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return (text, False)

    lines = stripped.splitlines()
    if not lines:
        return (text, False)

    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return ("\n".join(lines).strip(), True)


def _parse_structured(output_mode: str | None, output_text: str) -> dict[str, Any] | list[Any] | None:
    if output_mode in {"json_object"}:
        try:
            parsed = json.loads(output_text)
        except Exception:
            return None
        return parsed if isinstance(parsed, dict) else None
    if output_mode == "yaml":
        try:
            parsed = yaml.safe_load(output_text)
        except Exception:
            return None
        return parsed if isinstance(parsed, dict) else None
    return None


def _contains_all(text: str, needles: list[str]) -> bool:
    low = text.lower()
    return all(needle.lower() in low for needle in needles)


def _starts_with_verby_word(line: str) -> bool:
    first = _words(line[:30])
    if not first:
        return False
    verbs = {
        "attempt",
        "analyze",
        "archive",
        "check",
        "collect",
        "compare",
        "configure",
        "compress",
        "confirm",
        "emit",
        "escalate",
        "follow",
        "gather",
        "identify",
        "install",
        "keep",
        "load",
        "notify",
        "prepare",
        "preserve",
        "present",
        "repair",
        "report",
        "retry",
        "review",
        "run",
        "strip",
        "summarize",
        "sync",
        "update",
        "validate",
        "verify",
        "write",
    }
    token = first[0].lower()
    return token in verbs or bool(re.match(r".*(ate|fy|ise|ize)$", token))


def _evaluate_check(
    *,
    check: str,
    output_text: str,
    output_mode: str | None,
    parsed_payload: dict[str, Any] | list[Any] | None,
) -> bool:
    text = output_text.strip()
    lines = _lines(text)
    bullets = _bullet_lines(text)
    word_lines = [_words(line) for line in bullets or lines]
    low = check.lower()

    if low == "one sentence only":
        return len(_sentences(text)) == 1
    if low == "22 words or fewer":
        return len(_words(text)) <= 22
    if low == "must mention rollback":
        return "rollback" in text.lower()
    if low == "exactly 2 bullets":
        return len(bullets) == 2
    if low == "8 words or fewer per bullet":
        return bool(bullets) and all(len(words) <= 8 for words in word_lines[: len(bullets)])
    if low == "must mention retention and ticket number":
        return "ticket" in text.lower() and ("retain" in text.lower() or "retention" in text.lower())
    if low == "exactly 2 sentences":
        return len(_sentences(text)) == 2
    if low == "exactly 4 sentences":
        return len(_sentences(text)) == 4
    if low == "exactly 4 lines":
        return len(lines) == 4
    if low == "header must be item,quantity":
        return bool(lines) and lines[0].lower() == "item,quantity"
    if low == "exactly 5 bullets":
        return len(bullets) == 5
    if low == "each bullet starts with a verb":
        return bool(bullets) and all(_starts_with_verby_word(line) for line in bullets)
    if low == "6 words or fewer per bullet":
        return bool(bullets) and all(len(words) <= 6 for words in word_lines[: len(bullets)])
    if low == "must include slack and email":
        return _contains_all(text, ["slack", "email"])
    if low == "must identify pagerduty as stale":
        return "pagerduty" in text.lower() and "stale" in text.lower()
    if low == "exactly 3 bullets":
        return len(bullets) == 3
    if low == "exactly 3 lines":
        return len(lines) == 3
    if low in {"auth: healthy", "cache: healthy", "queue: healthy"}:
        return low in text.lower()
    if low == "exactly 2 bullets":
        return len(bullets) == 2
    if low == "10 words or fewer per bullet":
        return bool(bullets) and all(len(words) <= 10 for words in word_lines[: len(bullets)])
    if low == "action should imply escalate or abort":
        if not isinstance(parsed_payload, dict):
            return False
        action = str(parsed_payload.get("action", "")).lower()
        return any(token in action for token in ("escalate", "abort", "human_review"))
    if low == "exactly 2 lines":
        return len(lines) == 2
    if low == "line prefixes retry: and repair:":
        return len(lines) == 2 and lines[0].lower().startswith("retry:") and lines[1].lower().startswith("repair:")
    if low == "must include slack and email":
        return _contains_all(text, ["slack", "email"])

    if low.startswith("must include "):
        tail = check[13:]
        parts = [part.strip() for part in re.split(r"\band\b", tail, flags=re.IGNORECASE) if part.strip()]
        return _contains_all(text, parts)
    if low.startswith("must identify ") and " as stale" in low:
        target = low.replace("must identify ", "").replace(" as stale", "").strip()
        return target in text.lower() and "stale" in text.lower()
    if low.startswith("line prefixes "):
        targets = [piece.strip(" `") for piece in check[len("line prefixes ") :].split(" and ")]
        return len(lines) == len(targets) and all(
            lines[idx].lower().startswith(target.lower()) for idx, target in enumerate(targets)
        )
    return False


def _evaluate_invariant(invariant: str, parsed_payload: dict[str, Any] | list[Any] | None) -> bool:
    if not isinstance(parsed_payload, dict):
        return False
    low = invariant.lower()
    if low == "run_id must remain weekend-17":
        return parsed_payload.get("run_id") == "weekend-17"
    if low == "region must remain eu-west":
        return parsed_payload.get("region") == "eu-west"
    if low == "blocked_services must include cache and queue":
        services = parsed_payload.get("blocked_services")
        return isinstance(services, list) and "cache" in services and "queue" in services
    if low == "retry_budget must be 0":
        return parsed_payload.get("retry_budget") == 0
    if low == "status must be escalate":
        return parsed_payload.get("status") == "escalate"
    if low == "run_id must remain batch-03":
        return parsed_payload.get("run_id") == "batch-03"
    if low == "owner must remain nadia":
        return str(parsed_payload.get("owner", "")).lower() == "nadia"
    if low == "last_recommendation must be escalate":
        return parsed_payload.get("last_recommendation") == "escalate"
    if low == "priority_triggers must include over_expansion and latency_cliff":
        triggers = parsed_payload.get("priority_triggers")
        return isinstance(triggers, list) and "over_expansion" in triggers and "latency_cliff" in triggers
    if low == "pending_action must be switch to fallback model":
        return parsed_payload.get("pending_action") == "switch to fallback model"
    return False


def evaluate_contract(*, contract: dict[str, Any], output_text: str) -> ContractEvaluation:
    output_mode = contract.get("output_mode")
    output_mode = str(output_mode) if isinstance(output_mode, str) else None
    failure_class = str(contract.get("failure_class", "recoverable"))
    normalized_output_text, outer_fences_stripped = _strip_outer_fences(output_text)
    parsed_payload = _parse_structured(output_mode, normalized_output_text)

    satisfied: list[str] = []
    failed: list[str] = []

    required_keys = contract.get("required_keys") or []
    if required_keys:
        if isinstance(parsed_payload, dict):
            present = all(key in parsed_payload for key in required_keys if isinstance(key, str))
        else:
            present = False
        label = f"required_keys:{','.join(str(k) for k in required_keys)}"
        (satisfied if present else failed).append(label)

    for check in contract.get("checks") or []:
        if not isinstance(check, str):
            continue
        (satisfied if _evaluate_check(
            check=check,
            output_text=normalized_output_text,
            output_mode=output_mode,
            parsed_payload=parsed_payload,
        ) else failed).append(check)

    for invariant in contract.get("invariants") or []:
        if not isinstance(invariant, str):
            continue
        (satisfied if _evaluate_invariant(invariant, parsed_payload) else failed).append(invariant)

    return ContractEvaluation(
        passed=len(failed) == 0,
        output_mode=output_mode,
        failure_class=failure_class,
        recoverable_failure=(len(failed) > 0 and failure_class != "unrecoverable"),
        failed_checks=failed,
        satisfied_checks=satisfied,
        parsed_payload=parsed_payload,
        normalized_output_text=normalized_output_text,
        outer_fences_stripped=outer_fences_stripped,
    )
