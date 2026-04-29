from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

BackendName = Literal["mlx", "mock", "openai", "anthropic"]


@dataclass(frozen=True)
class ModelConfig:
    name: str
    path: str
    revision: str | None = None
    context_limit_tokens: int | None = None


@dataclass(frozen=True)
class GenerationConfig:
    temperature: float = 0.2
    top_p: float = 0.95
    seed: int | None = 0
    max_tokens: int = 256


@dataclass(frozen=True)
class OutputConfig:
    results_dir: str = "results"
    reports_dir: str = "reports"


@dataclass(frozen=True)
class StressFailureConfig:
    consecutive: int = 3
    max_latency_ms: int | None = None
    latency_only_after_input_tokens: int | None = None
    latency_only_after_context_fraction: float | None = None
    max_rcs: float | None = None
    fail_on_lorr: bool = True


@dataclass(frozen=True)
class StressConfig:
    enabled: bool = False
    max_steps: int = 30
    max_runtime_sec: int = 120
    context_growth: str = "append"  # append | sliding
    sliding_window_steps: int = 6
    system: str | None = None
    prompt: str = "Write a short checklist for running LTE locally."
    history_max_chars_per_step: int = 2000
    history_max_chars_total: int | None = None
    failure: StressFailureConfig = StressFailureConfig()


@dataclass(frozen=True)
class RunConfig:
    run_name: str
    backend: BackendName
    models: list[ModelConfig]
    suites: list[str]
    generation: GenerationConfig = GenerationConfig()
    output: OutputConfig = OutputConfig()
    stress: StressConfig = StressConfig()


def _as_str(value: Any, *, field: str) -> str:
    if isinstance(value, str) and value.strip():
        return value
    raise ValueError(f"Expected non-empty string for '{field}', got {value!r}")


def _as_float(value: Any, *, field: str) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    raise ValueError(f"Expected number for '{field}', got {type(value).__name__}")


def _as_int_or_none(value: Any, *, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    raise ValueError(f"Expected int or null for '{field}', got {type(value).__name__}")


def load_config(path: str | Path) -> RunConfig:
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Config must be a mapping: {config_path}")

    run_name = _as_str(raw.get("run_name", "run"), field="run_name")
    backend = raw.get("backend", "mlx")
    if backend not in ("mlx", "mock", "openai", "anthropic"):
        raise ValueError("backend must be one of: mlx, mock, openai, anthropic")

    raw_models = raw.get("models")
    if not isinstance(raw_models, list) or not raw_models:
        raise ValueError("models must be a non-empty list")
    models: list[ModelConfig] = []
    for m in raw_models:
        if not isinstance(m, dict):
            raise ValueError("models[] entries must be mappings")
        name = _as_str(m.get("name"), field="models[].name")
        model_path = _as_str(m.get("path"), field="models[].path")
        revision = m.get("revision")
        if revision is not None and not isinstance(revision, str):
            raise ValueError("models[].revision must be string or null")
        context_limit_tokens = m.get("context_limit_tokens")
        if context_limit_tokens is not None and not isinstance(context_limit_tokens, int):
            raise ValueError("models[].context_limit_tokens must be int or null")
        models.append(
            ModelConfig(
                name=name,
                path=model_path,
                revision=revision,
                context_limit_tokens=context_limit_tokens,
            )
        )

    raw_suites = raw.get("suites")
    if not isinstance(raw_suites, list) or not raw_suites:
        raise ValueError("suites must be a non-empty list of suite YAML paths")
    suites = [_as_str(s, field="suites[]") for s in raw_suites]

    gen_raw = raw.get("generation", {}) or {}
    if not isinstance(gen_raw, dict):
        raise ValueError("generation must be a mapping")
    generation = GenerationConfig(
        temperature=_as_float(gen_raw.get("temperature", 0.2), field="generation.temperature"),
        top_p=_as_float(gen_raw.get("top_p", 0.95), field="generation.top_p"),
        seed=_as_int_or_none(gen_raw.get("seed", 0), field="generation.seed"),
        max_tokens=int(gen_raw.get("max_tokens", 256)),
    )

    out_raw = raw.get("output", {}) or {}
    if not isinstance(out_raw, dict):
        raise ValueError("output must be a mapping")
    output = OutputConfig(
        results_dir=_as_str(out_raw.get("results_dir", "results"), field="output.results_dir"),
        reports_dir=_as_str(out_raw.get("reports_dir", "reports"), field="output.reports_dir"),
    )

    stress_raw = raw.get("stress", {}) or {}
    if not isinstance(stress_raw, dict):
        raise ValueError("stress must be a mapping")
    if stress_raw.get("system") is not None and not isinstance(stress_raw.get("system"), str):
        raise ValueError("stress.system must be string or null")
    if stress_raw.get("history_max_chars_total") is not None and not isinstance(
        stress_raw.get("history_max_chars_total"), int
    ):
        raise ValueError("stress.history_max_chars_total must be int or null")
    failure_raw = stress_raw.get("failure", {}) or {}
    if not isinstance(failure_raw, dict):
        raise ValueError("stress.failure must be a mapping")
    failure = StressFailureConfig(
        consecutive=int(failure_raw.get("consecutive", 3)),
        max_latency_ms=failure_raw.get("max_latency_ms"),
        latency_only_after_input_tokens=failure_raw.get("latency_only_after_input_tokens"),
        latency_only_after_context_fraction=failure_raw.get("latency_only_after_context_fraction"),
        max_rcs=failure_raw.get("max_rcs"),
        fail_on_lorr=bool(failure_raw.get("fail_on_lorr", True)),
    )
    stress = StressConfig(
        enabled=bool(stress_raw.get("enabled", False)),
        max_steps=int(stress_raw.get("max_steps", 30)),
        max_runtime_sec=int(stress_raw.get("max_runtime_sec", 120)),
        context_growth=_as_str(stress_raw.get("context_growth", "append"), field="stress.context_growth"),
        sliding_window_steps=int(stress_raw.get("sliding_window_steps", 6)),
        system=stress_raw.get("system"),
        prompt=_as_str(stress_raw.get("prompt", "Write a short checklist for running LTE locally."), field="stress.prompt"),
        history_max_chars_per_step=int(stress_raw.get("history_max_chars_per_step", 2000)),
        history_max_chars_total=stress_raw.get("history_max_chars_total"),
        failure=failure,
    )

    return RunConfig(
        run_name=run_name,
        backend=backend,
        models=models,
        suites=suites,
        generation=generation,
        output=output,
        stress=stress,
    )
