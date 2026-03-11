#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
RUN_SWEEP = REPO_ROOT / "research" / "drift_v0" / "runner" / "run_sweep.py"
FAILURE_CAUSES = REPO_ROOT / "research" / "drift_v0" / "analysis" / "failure_causes.py"
GENERATE_ASSETS = REPO_ROOT / "research" / "papers" / "drift_v0" / "generate_assets.py"
DEFAULT_SWEEP_CONFIG = REPO_ROOT / "research" / "drift_v0" / "runner" / "sweep_config_template.json"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "artifacts" / "drift_v0" / "weekend"
DEFAULT_ASSETS_OUTPUT = DEFAULT_OUTPUT_ROOT / "paper_assets"
DEFAULT_TASKS_DIR = REPO_ROOT / "research" / "drift_v0" / "tasks"
REQUIRED_TASK_FILES = (
    DEFAULT_TASKS_DIR / "e1_tasks_v1.jsonl",
    DEFAULT_TASKS_DIR / "e2_tasks_v2.jsonl",
    DEFAULT_TASKS_DIR / "schema_registry.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run drift_v0 tests, sweep, failure-cause analysis, and paper assets from repo-local paths."
    )
    parser.add_argument(
        "--python-bin",
        default=str(DEFAULT_VENV_PYTHON if DEFAULT_VENV_PYTHON.exists() else sys.executable),
        help="Python interpreter used for child commands.",
    )
    parser.add_argument(
        "--sweep-config",
        default=str(DEFAULT_SWEEP_CONFIG),
        help="Sweep config JSON.",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Repo-local root for sweep and analysis artifacts.",
    )
    parser.add_argument(
        "--assets-output-dir",
        default=str(DEFAULT_ASSETS_OUTPUT),
        help="Directory for generated report tables/figures.",
    )
    parser.add_argument("--skip-tests", action="store_true", help="Skip pytest.")
    parser.add_argument("--skip-sweep", action="store_true", help="Skip run_sweep.py.")
    parser.add_argument(
        "--skip-failure-causes",
        action="store_true",
        help="Skip derived failure-cause CSV generation.",
    )
    parser.add_argument("--skip-assets", action="store_true", help="Skip paper asset generation.")
    parser.add_argument("--resume", action="store_true", help="Resume an existing sweep.")
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Validate config, tasks, and model paths, then stop without running jobs.",
    )
    return parser.parse_args()


def run_cmd(cmd: list[str], cwd: Path) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as infile:
        data = json.load(infile)
    if not isinstance(data, dict):
        raise SystemExit(f"Sweep config must be a JSON object: {path}")
    return data


def preflight_check(*, python_bin: Path, sweep_config: Path, output_root: Path) -> None:
    failures: list[str] = []

    if not python_bin.exists():
        failures.append(f"Python interpreter not found: {python_bin}")

    if not sweep_config.exists():
        failures.append(f"Sweep config not found: {sweep_config}")
    else:
        cfg = load_json(sweep_config)
        backend = str(cfg.get("backend", "mlx"))
        models = cfg.get("models")
        if not isinstance(models, list) or not models:
            failures.append("Sweep config must define a non-empty models list.")
        else:
            for idx, model in enumerate(models, start=1):
                if not isinstance(model, dict):
                    failures.append(f"models[{idx}] must be an object.")
                    continue
                name = model.get("name")
                path = model.get("path")
                if not isinstance(name, str) or not name.strip():
                    failures.append(f"models[{idx}].name must be a non-empty string.")
                if not isinstance(path, str) or not path.strip():
                    failures.append(f"models[{idx}].path must be a non-empty string.")
                    continue
                if backend != "mock" and not Path(path).exists():
                    failures.append(f"Model path does not exist for {name}: {path}")

    for required in REQUIRED_TASK_FILES:
        if not required.exists():
            failures.append(f"Required task file missing: {required}")

    try:
        output_root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        failures.append(f"Could not create output root {output_root}: {exc}")

    if failures:
        raise SystemExit("Preflight failed:\n- " + "\n- ".join(failures))

    print("Preflight OK")
    print(f"- python: {python_bin}")
    print(f"- config: {sweep_config}")
    print(f"- output_root: {output_root}")


def merge_eval_files(output_root: Path) -> Path:
    merged = output_root / "all_eval_merged.jsonl"
    with merged.open("w", encoding="utf-8") as outfile:
        for path in sorted(output_root.glob("*/*_eval.jsonl")):
            with path.open("r", encoding="utf-8") as infile:
                outfile.write(infile.read())
    return merged


def main() -> None:
    args = parse_args()
    python_bin = Path(args.python_bin)
    sweep_config = Path(args.sweep_config)
    output_root = Path(args.output_root)
    assets_output_dir = Path(args.assets_output_dir)
    preflight_check(python_bin=python_bin, sweep_config=sweep_config, output_root=output_root)

    if args.preflight_only:
        return

    if not args.skip_tests:
        run_cmd([str(python_bin), "-m", "pytest", "-q"], REPO_ROOT)

    if not args.skip_sweep:
        cmd = [
            str(python_bin),
            str(RUN_SWEEP),
            "--config",
            str(sweep_config),
            "--output-root",
            str(output_root),
            "--python-bin",
            str(python_bin),
        ]
        if args.resume:
            cmd.append("--resume")
        run_cmd(cmd, REPO_ROOT)

    merged_eval = output_root / "all_eval_merged.jsonl"
    if not args.skip_failure_causes or not args.skip_assets:
        merged_eval = merge_eval_files(output_root)

    cause_by_model = output_root / "failure_cause_by_model.csv"
    cause_overall = output_root / "failure_cause_overall.csv"
    if not args.skip_failure_causes:
        run_cmd(
            [
                str(python_bin),
                str(FAILURE_CAUSES),
                "--input",
                str(merged_eval),
                "--output-by-model",
                str(cause_by_model),
                "--output-overall",
                str(cause_overall),
            ],
            REPO_ROOT,
        )

    if not args.skip_assets:
        run_cmd(
            [
                str(python_bin),
                str(GENERATE_ASSETS),
                "--manifest",
                str(output_root / "sweep_manifest.csv"),
                "--cause-by-model",
                str(cause_by_model),
                "--cause-overall",
                str(cause_overall),
                "--output-dir",
                str(assets_output_dir),
            ],
            REPO_ROOT,
        )


if __name__ == "__main__":
    main()
