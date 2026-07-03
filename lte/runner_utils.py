"""Shared helpers for the orchestration scripts.

Both `scripts/run_unified_weekend.py` (the sweep runner) and
`scripts/run_threshold_sensitivity.py` (the threshold-sensitivity sweep)
need the same things: env-file loading, missing-key checks, models- and
suites-config parsing. Keeping those in one place stops the two scripts
drifting apart — the 2026-06-04 overnight sweep failed in part because
the sweep runner ignored the models-config's `suites:` block; we do not
want the sensitivity script to repeat that bug.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

# Env vars each API backend requires. Checked in preflight so a missing
# key fails the sweep up front instead of silently failing every API run.
BACKEND_REQUIRED_ENV: dict[str, list[str]] = {
    "anthropic": ["ANTHROPIC_API_KEY"],
    "openai": ["OPENAI_API_KEY"],
}


def load_env_file(path: Path) -> list[str]:
    """Load KEY=VALUE lines from an env file into os.environ.

    Existing environment variables win — the file only fills gaps, so an
    explicitly exported key is never overridden. Returns the names loaded.
    No python-dotenv dependency; handles comments, blank lines, optional
    `export ` prefix, and surrounding quotes.
    """
    if not path.exists():
        return []
    loaded: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        name, _, value = line.partition("=")
        name = name.strip()
        value = value.strip().strip("'\"")
        if not name or not value:
            continue
        if not os.environ.get(name):
            os.environ[name] = value
            loaded.append(name)
    return loaded


def check_backend_env(models: list[dict[str, Any]]) -> list[str]:
    """Return the missing required env var names for the backends in use."""
    missing: list[str] = []
    backends = {str(model.get("backend", "mlx")) for model in models}
    for backend in sorted(backends):
        for var in BACKEND_REQUIRED_ENV.get(backend, []):
            if not os.environ.get(var) and var not in missing:
                missing.append(var)
    return missing


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected mapping in {path}")
    return raw


def models_from_config(path: Path) -> list[dict[str, Any]]:
    raw = load_yaml_mapping(path)
    models = raw.get("models")
    if not isinstance(models, list) or not models:
        raise ValueError(f"No models found in {path}")
    out: list[dict[str, Any]] = []
    for model in models:
        if not isinstance(model, dict):
            raise ValueError(f"Invalid model entry in {path}: {model!r}")
        out.append(
            {
                "name": str(model["name"]),
                "backend": str(model.get("backend", raw.get("backend", "mlx"))),
                "path": str(model["path"]),
                "revision": model.get("revision"),
                "context_limit_tokens": model.get("context_limit_tokens"),
                "max_latency_ms": model.get("max_latency_ms"),
            }
        )
    return out


def suites_from_config(path: Path) -> list[str] | None:
    """Optional `suites:` list in the models-config, overriding the base config.

    The 2026-06-04 sweep silently ran only the base config's 4 suites
    because the models-config's suites block was never read — the two new
    probe families never executed. Both orchestration scripts now honour
    this override.
    """
    raw = load_yaml_mapping(path)
    suites = raw.get("suites")
    if suites is None:
        return None
    if not isinstance(suites, list) or not all(isinstance(s, str) for s in suites):
        raise ValueError(f"Invalid suites list in {path}: {suites!r}")
    return suites
