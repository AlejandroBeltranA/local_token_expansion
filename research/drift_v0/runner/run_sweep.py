#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER_DIR = Path(__file__).resolve().parent
RUN_EXPERIMENTS = RUNNER_DIR / "run_experiments.py"
EVALUATE_EVENTS = RUNNER_DIR / "evaluate_events.py"
SUMMARIZE = REPO_ROOT / "research" / "drift_v0" / "analysis" / "summarize.py"
TASKS_DIR = REPO_ROOT / "research" / "drift_v0" / "tasks"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run overnight drift_v0 parameter sweeps.")
    parser.add_argument(
        "--config",
        default=str(RUNNER_DIR / "sweep_config_template.json"),
        help="Sweep JSON config.",
    )
    parser.add_argument(
        "--output-root",
        default="/tmp/drift_v0_sweep",
        help="Output root directory for all sweep runs.",
    )
    parser.add_argument(
        "--python-bin",
        default=sys.executable,
        help="Python executable to use for child commands.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip completed conditions when metrics_summary.json already exists.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as infile:
        return json.load(infile)


def run_cmd(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def slug(value: str) -> str:
    out = []
    for ch in value.lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in {"-", "_"}:
            out.append(ch)
        else:
            out.append("-")
    return "".join(out).strip("-")


def metric_row(metrics_summary: dict[str, Any], experiment_id: str) -> dict[str, Any]:
    rows = metrics_summary.get("failure_and_escalation_by_experiment", [])
    for row in rows:
        if str(row.get("experiment_id")) == experiment_id:
            return row
    return {}


def retry_row(metrics_summary: dict[str, Any], experiment_id: str) -> dict[str, Any]:
    rows = metrics_summary.get("retry_effectiveness_by_experiment", [])
    for row in rows:
        if str(row.get("experiment_id")) == experiment_id:
            return row
    return {}


def main() -> None:
    args = parse_args()
    config = load_json(Path(args.config))
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    models = config["models"]
    backend = str(config.get("backend", "mlx"))
    if backend not in {"mlx", "mock"}:
        raise ValueError("config.backend must be 'mlx' or 'mock'")
    temperatures = config["temperatures"]
    top_ps = config["top_p"]
    max_tokens = int(config.get("max_tokens", 256))
    seed = int(config.get("seed", 0))
    history_cfg = config.get("history_max_chars", {})
    h_e2 = int(history_cfg.get("e2", 4000))
    h_e3_1k = int(history_cfg.get("e3_1k", 4000))
    h_e3_4k = int(history_cfg.get("e3_4k", 16000))

    manifest_rows: list[dict[str, Any]] = []

    for model in models:
        model_name = str(model["name"])
        model_path = str(model["path"])
        model_slug = slug(model_name)

        for temp in temperatures:
            for top_p in top_ps:
                temp_str = str(temp).replace(".", "p")
                top_p_str = str(top_p).replace(".", "p")
                cond_id = f"{model_slug}__t{temp_str}__p{top_p_str}"
                cond_dir = output_root / cond_id
                cond_dir.mkdir(parents=True, exist_ok=True)

                metrics_path = cond_dir / "report" / "metrics_summary.json"
                if args.resume and metrics_path.exists():
                    print(f"skip_completed={cond_id}")
                    summary = load_json(metrics_path)
                else:
                    raw_e1 = cond_dir / "e1_raw.jsonl"
                    raw_e2 = cond_dir / "e2_raw.jsonl"
                    raw_e3_1k = cond_dir / "e3_1k_raw.jsonl"
                    raw_e3_4k = cond_dir / "e3_4k_raw.jsonl"
                    raw_all = cond_dir / "all_raw.jsonl"
                    eval_all = cond_dir / "all_eval.jsonl"
                    report_dir = cond_dir / "report"

                    base_args = [
                        args.python_bin,
                        str(RUN_EXPERIMENTS),
                        "--model-name",
                        model_name,
                        "--model-path",
                        model_path,
                        "--backend",
                        backend,
                        "--seed",
                        str(seed),
                        "--temperature",
                        str(temp),
                        "--top-p",
                        str(top_p),
                        "--max-tokens",
                        str(max_tokens),
                    ]

                    run_cmd(
                        base_args
                        + [
                            "--task-pack",
                            str(TASKS_DIR / "e1_tasks_v1.jsonl"),
                            "--output",
                            str(raw_e1),
                            "--run-id",
                            f"{cond_id}__e1",
                        ]
                    )

                    run_cmd(
                        base_args
                        + [
                            "--task-pack",
                            str(TASKS_DIR / "e2_tasks_v2.jsonl"),
                            "--output",
                            str(raw_e2),
                            "--run-id",
                            f"{cond_id}__e2",
                            "--history-max-chars",
                            str(h_e2),
                        ]
                    )

                    run_cmd(
                        base_args
                        + [
                            "--task-pack",
                            str(TASKS_DIR / "e2_tasks_v2.jsonl"),
                            "--output",
                            str(raw_e3_1k),
                            "--run-id",
                            f"{cond_id}__e3_1k",
                            "--experiment-id",
                            "E3",
                            "--e3-condition",
                            "1k",
                            "--history-max-chars",
                            str(h_e3_1k),
                        ]
                    )

                    run_cmd(
                        base_args
                        + [
                            "--task-pack",
                            str(TASKS_DIR / "e2_tasks_v2.jsonl"),
                            "--output",
                            str(raw_e3_4k),
                            "--run-id",
                            f"{cond_id}__e3_4k",
                            "--experiment-id",
                            "E3",
                            "--e3-condition",
                            "4k",
                            "--history-max-chars",
                            str(h_e3_4k),
                        ]
                    )

                    with raw_all.open("w", encoding="utf-8") as outfile:
                        for src in (raw_e1, raw_e2, raw_e3_1k, raw_e3_4k):
                            with src.open("r", encoding="utf-8") as infile:
                                outfile.write(infile.read())

                    run_cmd(
                        [
                            args.python_bin,
                            str(EVALUATE_EVENTS),
                            "--input",
                            str(raw_all),
                            "--output",
                            str(eval_all),
                            "--task-pack",
                            str(TASKS_DIR / "e1_tasks_v1.jsonl"),
                            "--task-pack",
                            str(TASKS_DIR / "e2_tasks_v2.jsonl"),
                            "--schema-registry",
                            str(TASKS_DIR / "schema_registry.json"),
                        ]
                    )

                    run_cmd(
                        [
                            args.python_bin,
                            str(SUMMARIZE),
                            "--input",
                            str(eval_all),
                            "--output-dir",
                            str(report_dir),
                        ]
                    )

                    summary = load_json(metrics_path)

                e1 = metric_row(summary, "E1")
                e2 = metric_row(summary, "E2")
                e3 = metric_row(summary, "E3")
                e3_delta = summary.get("e3_degradation_delta_4k_minus_1k", {})
                e2_retry = retry_row(summary, "E2")
                e3_retry = retry_row(summary, "E3")

                manifest_rows.append(
                    {
                        "condition_id": cond_id,
                        "model_name": model_name,
                        "model_path": model_path,
                        "temperature": temp,
                        "top_p": top_p,
                        "e1_primary_failure_rate": e1.get("turn_failure_rate", ""),
                        "e2_primary_failure_rate": e2.get("turn_failure_rate", ""),
                        "e3_primary_failure_rate": e3.get("turn_failure_rate", ""),
                        "e2_retry_effectiveness": e2_retry.get("retry_effectiveness_rate", ""),
                        "e3_retry_effectiveness": e3_retry.get("retry_effectiveness_rate", ""),
                        "e3_delta_turn_failure_rate": e3_delta.get("turn_failure_rate", ""),
                        "e3_delta_first_failure_turn_mean": e3_delta.get(
                            "first_failure_turn_mean", ""
                        ),
                    }
                )

                print(f"completed={cond_id}")

    manifest_path = output_root / "sweep_manifest.csv"
    headers = [
        "condition_id",
        "model_name",
        "model_path",
        "temperature",
        "top_p",
        "e1_primary_failure_rate",
        "e2_primary_failure_rate",
        "e3_primary_failure_rate",
        "e2_retry_effectiveness",
        "e3_retry_effectiveness",
        "e3_delta_turn_failure_rate",
        "e3_delta_first_failure_turn_mean",
    ]
    with manifest_path.open("w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(manifest_rows)
    print(f"manifest={manifest_path}")


if __name__ == "__main__":
    main()
