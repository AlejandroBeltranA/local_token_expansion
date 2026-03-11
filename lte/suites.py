from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PromptCase:
    id: str
    prompt: str
    system: str | None
    max_tokens: int | None
    tags: list[str]
    pair_id: str | None
    variant: str | None  # "concise" | "detailed" (free-form for now)
    trigger_targets: list[str]
    contract: dict[str, Any]


@dataclass(frozen=True)
class PromptSuite:
    name: str
    description: str | None
    experiment_family: str | None
    cases: list[PromptCase]
    path: Path | None = None


def _as_str(value: Any, *, field: str) -> str:
    if isinstance(value, str):
        return value
    raise ValueError(f"Expected string for '{field}', got {type(value).__name__}")


def _as_int(value: Any, *, field: str) -> int:
    if isinstance(value, int):
        return value
    raise ValueError(f"Expected int for '{field}', got {type(value).__name__}")


def load_suite(path: str | Path) -> PromptSuite:
    suite_path = Path(path)
    raw = yaml.safe_load(suite_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Suite YAML must be a mapping: {suite_path}")

    name = _as_str(raw.get("name"), field="name")
    description = raw.get("description")
    if description is not None and not isinstance(description, str):
        raise ValueError(f"Expected string for 'description', got {type(description).__name__}")
    experiment_family = raw.get("experiment_family")
    if experiment_family is not None and not isinstance(experiment_family, str):
        raise ValueError(f"Expected string for 'experiment_family', got {type(experiment_family).__name__}")

    raw_cases = raw.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError(f"Suite must contain non-empty 'cases' list: {suite_path}")

    cases: list[PromptCase] = []
    seen_ids: set[str] = set()
    for idx, item in enumerate(raw_cases):
        if not isinstance(item, dict):
            raise ValueError(f"Case {idx} must be a mapping: {suite_path}")

        case_id = _as_str(item.get("id"), field="cases[].id")
        if case_id in seen_ids:
            raise ValueError(f"Duplicate case id '{case_id}' in {suite_path}")
        seen_ids.add(case_id)

        prompt = _as_str(item.get("prompt"), field="cases[].prompt")
        system = item.get("system")
        if system is not None and not isinstance(system, str):
            raise ValueError(f"Expected string for cases[].system, got {type(system).__name__}")

        max_tokens = item.get("max_tokens")
        if max_tokens is not None and not isinstance(max_tokens, int):
            raise ValueError(f"Expected int for cases[].max_tokens, got {type(max_tokens).__name__}")

        tags = item.get("tags", [])
        if tags is None:
            tags = []
        if not isinstance(tags, list) or any(not isinstance(t, str) for t in tags):
            raise ValueError("Expected list[str] for cases[].tags")

        pair_id = item.get("pair_id")
        if pair_id is not None and not isinstance(pair_id, str):
            raise ValueError(f"Expected string for cases[].pair_id, got {type(pair_id).__name__}")

        variant = item.get("variant")
        if variant is not None and not isinstance(variant, str):
            raise ValueError(f"Expected string for cases[].variant, got {type(variant).__name__}")

        trigger_targets = item.get("trigger_targets", [])
        if trigger_targets is None:
            trigger_targets = []
        if not isinstance(trigger_targets, list) or any(not isinstance(t, str) for t in trigger_targets):
            raise ValueError("Expected list[str] for cases[].trigger_targets")

        contract = item.get("contract", {})
        if contract is None:
            contract = {}
        if not isinstance(contract, dict):
            raise ValueError("Expected mapping for cases[].contract")

        cases.append(
            PromptCase(
                id=case_id,
                prompt=prompt,
                system=system,
                max_tokens=max_tokens,
                tags=tags,
                pair_id=pair_id,
                variant=variant,
                trigger_targets=trigger_targets,
                contract=contract,
            )
        )

    return PromptSuite(
        name=name,
        description=description,
        experiment_family=experiment_family,
        cases=cases,
        path=suite_path,
    )


def list_suite_files(root: str | Path) -> list[Path]:
    root_path = Path(root)
    if not root_path.exists():
        return []
    return sorted([p for p in root_path.glob("*.yaml") if p.is_file()] + [p for p in root_path.glob("*.yml") if p.is_file()])
