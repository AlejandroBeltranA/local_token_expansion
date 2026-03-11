#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODELS_DIR = REPO_ROOT / "mlx_models"
DEFAULT_OUTPUT = REPO_ROOT / "research" / "drift_v0" / "runner" / "sweep_config_weekend_local.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a local drift_v0 weekend sweep config from available MLX models."
    )
    parser.add_argument(
        "--models-dir",
        default=str(DEFAULT_MODELS_DIR),
        help="Directory containing local MLX model folders.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output path for the generated sweep config JSON.",
    )
    parser.add_argument(
        "--backend",
        choices=("mlx", "mock"),
        default="mlx",
        help="Backend to record in the config.",
    )
    parser.add_argument(
        "--max-models",
        type=int,
        default=0,
        help="Optional cap on number of discovered models. 0 means no cap.",
    )
    return parser.parse_args()


def discover_models(models_dir: Path, max_models: int) -> list[dict[str, str]]:
    models = [
        {"name": path.name, "path": str(path.resolve())}
        for path in sorted(models_dir.iterdir(), key=lambda item: item.name.lower())
        if path.is_dir()
    ]
    if max_models > 0:
        models = models[:max_models]
    return models


def main() -> None:
    args = parse_args()
    models_dir = Path(args.models_dir)
    if not models_dir.exists():
        raise SystemExit(f"Models directory does not exist: {models_dir}")

    models = discover_models(models_dir, args.max_models)
    if not models and args.backend != "mock":
        raise SystemExit(f"No model directories found under: {models_dir}")

    cfg = {
        "models": models if args.backend != "mock" else [{"name": "mock-model", "path": "unused"}],
        "backend": args.backend,
        "temperatures": [0.0, 0.2, 0.6],
        "top_p": [0.8, 0.95, 1.0],
        "max_tokens": 256,
        "seed": 0,
        "history_max_chars": {
            "e2": 4000,
            "e3_1k": 4000,
            "e3_4k": 16000,
        },
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
