#!/usr/bin/env python3
"""
Batch runner that executes the same experiment across multiple models.

Non‑technical summary:
1) Read the base experiment settings.
2) For each model, make a temporary config pointing to that model.
3) Run the experiment.
4) Save outputs in separate files named after each model.
"""
import argparse
import json
import time
from pathlib import Path


def load_config(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run propensity experiments across multiple models.")
    parser.add_argument(
        "--config",
        default="research/propensity/local_llm_propensity.json",
        help="Base config JSON",
    )
    parser.add_argument(
        "--models",
        nargs="*",
        default=None,
        help="List of model paths or HF repos (overrides config models list)",
    )
    parser.add_argument(
        "--run-script",
        default="research/propensity/run_propensity.py",
        help="Path to run_propensity.py",
    )
    args = parser.parse_args()

    cfg_path = Path(args.config)
    cfg = load_config(cfg_path)

    models = args.models if args.models else cfg.get("models", [])
    if not models:
        raise SystemExit("No models provided. Add a `models` list in config or pass --models.")

    total = len(models)
    for idx, model_path in enumerate(models, start=1):
        model_name = Path(model_path).name
        run_name = f"{model_name}"

        temp_cfg = dict(cfg)
        temp_cfg["model_path"] = model_path
        temp_cfg["run_name"] = run_name

        temp_path = cfg_path.parent / f"temp_{model_name}_config.json"
        temp_path.write_text(json.dumps(temp_cfg, indent=2))

        print(f"[{idx}/{total}] Running {model_name} -> {run_name}")
        start = time.time()
        cmd = f"python {args.run_script} --config {temp_path}"
        exit_code = os.system(cmd)
        elapsed = time.time() - start
        print(f"[{idx}/{total}] Finished {model_name} in {elapsed/60:.1f} min")
        if exit_code != 0:
            raise SystemExit(f"Run failed for {model_name}")

        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    import os
    main()
