from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

RECOMMENDATION_ORDER = {
    "continue": 0,
    "retry": 1,
    "repair": 2,
    "escalate": 3,
    "abort": 4,
}


@dataclass(frozen=True)
class RunSpec:
    stage: str
    backend: str
    model_name: str
    model_path: str
    revision: str | None
    context_limit_tokens: int | None
    temperature: float
    top_p: float
    max_tokens: int
    seed: int

    @property
    def run_id(self) -> str:
        model_slug = self.model_name.lower().replace(".", "").replace(" ", "_")
        return (
            f"weekend_{self.stage}_{model_slug}"
            f"_t{str(self.temperature).replace('.', 'p')}"
            f"_m{self.max_tokens}_s{self.seed}"
        )


@dataclass(frozen=True)
class RunOutcome:
    stage: str
    model_name: str
    temperature: float
    max_tokens: int
    seed: int
    run_id: str
    status: str
    run_dir: str
    recommendation: str | None = None
    fired_triggers: list[str] | None = None
    benchmark_contract_failures: int | None = None
    recoverable_contract_failures: int | None = None
    unrecoverable_contract_failures: int | None = None
    mean_stress_latency_ms: float | None = None
    first_gated_failure_step: int | None = None
    stress_steps: int | None = None
    duration_sec: float | None = None
    error: str | None = None


def _load_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected mapping in {path}")
    return raw


def _models_from_config(path: Path) -> list[dict[str, Any]]:
    raw = _load_yaml(path)
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
            }
        )
    return out


def _build_run_specs(
    *,
    models: list[dict[str, Any]],
    temperatures: list[float],
    max_tokens: list[int],
    seeds: list[int],
    stage: str,
) -> list[RunSpec]:
    specs: list[RunSpec] = []
    for model in models:
        for temperature in temperatures:
            for budget in max_tokens:
                for seed in seeds:
                    specs.append(
                        RunSpec(
                            stage=stage,
                            backend=str(model.get("backend", "mlx")),
                            model_name=str(model["name"]),
                            model_path=str(model["path"]),
                            revision=model.get("revision"),
                            context_limit_tokens=model.get("context_limit_tokens"),
                            temperature=float(temperature),
                            top_p=0.95,
                            max_tokens=int(budget),
                            seed=int(seed),
                        )
                    )
    return specs


def _write_run_config(*, base_config: dict[str, Any], spec: RunSpec, config_path: Path, results_dir: Path) -> None:
    cfg = json.loads(json.dumps(base_config))
    cfg["run_name"] = spec.run_id
    cfg["backend"] = spec.backend
    cfg["models"] = [
        {
            "name": spec.model_name,
            "path": spec.model_path,
            "revision": spec.revision,
            "context_limit_tokens": spec.context_limit_tokens,
        }
    ]
    generation = dict(cfg.get("generation") or {})
    generation["temperature"] = spec.temperature
    generation["top_p"] = spec.top_p
    generation["max_tokens"] = spec.max_tokens
    generation["seed"] = spec.seed
    cfg["generation"] = generation
    output = dict(cfg.get("output") or {})
    output["results_dir"] = str(results_dir)
    output["reports_dir"] = str(results_dir / "reports")
    cfg["output"] = output
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")


def _run_summary(run_dir: Path) -> dict[str, Any]:
    summary_path = run_dir / "summary.json"
    return json.loads(summary_path.read_text(encoding="utf-8"))


def _extract_model_summary(summary: dict[str, Any]) -> dict[str, Any]:
    models = summary.get("models")
    if not isinstance(models, list) or not models:
        error_rows = int((summary.get("records") or {}).get("error_rows", 0) or 0)
        raise ValueError(f"summary.json missing models[] (error_rows={error_rows})")
    model_summary = models[0]
    recommendation = model_summary.get("recommendation") or {}
    if isinstance(recommendation, dict):
        action = str(recommendation.get("action", "abort"))
    else:
        action = str(recommendation)
    trigger_summary = model_summary.get("trigger_summary") or {}
    fired_triggers = sorted(
        [name for name, payload in trigger_summary.items() if isinstance(payload, dict) and payload.get("status") == "fired"]
    )
    latency_evidence = trigger_summary.get("latency_cliff") or {}
    latency_payload = latency_evidence.get("evidence") if isinstance(latency_evidence, dict) else {}
    first_gated = None
    if isinstance(latency_payload, dict):
        steps = latency_payload.get("gated_latency_steps") or []
        if isinstance(steps, list) and steps:
            first_gated = steps[0]
    metrics = model_summary.get("metrics") or {}
    return {
        "recommendation": action,
        "fired_triggers": fired_triggers,
        "benchmark_contract_failures": int(metrics.get("benchmark_contract_failures", 0) or 0),
        "recoverable_contract_failures": int(metrics.get("recoverable_contract_failures", 0) or 0),
        "unrecoverable_contract_failures": int(metrics.get("unrecoverable_contract_failures", 0) or 0),
        "mean_stress_latency_ms": float(metrics.get("mean_stress_latency_ms", 0.0) or 0.0),
        "first_gated_failure_step": first_gated,
        "stress_steps": int(model_summary.get("stress_steps", 0) or 0),
    }


def _rank_key(result: dict[str, Any]) -> tuple[Any, ...]:
    first_gated = result.get("first_gated_failure_step")
    if first_gated is None:
        first_gated_rank = -999999
    else:
        first_gated_rank = -int(first_gated)
    return (
        RECOMMENDATION_ORDER.get(str(result.get("recommendation")), 99),
        len(result.get("fired_triggers", [])),
        int(result.get("benchmark_contract_failures", 0)),
        first_gated_rank,
        float(result.get("mean_stress_latency_ms", 0.0)),
        -int(result.get("stress_steps", 0)),
        str(result.get("model_name", "")),
    )


def _aggregate_rank_key(result: dict[str, Any]) -> tuple[Any, ...]:
    counts = result.get("recommendation_counts") or {}
    if counts:
        modal_recommendation = min(
            counts.items(),
            key=lambda item: (RECOMMENDATION_ORDER.get(str(item[0]), 99), -int(item[1])),
        )[0]
    else:
        modal_recommendation = "abort"
    trigger_burden = sum(int(v) for v in (result.get("trigger_fire_counts") or {}).values())
    first_gated_range = result.get("first_gated_failure_step_range")
    first_gated_rank = -999999 if not first_gated_range else -int(first_gated_range[0])
    return (
        RECOMMENDATION_ORDER.get(str(modal_recommendation), 99),
        trigger_burden,
        float(result.get("benchmark_contract_failures_mean", 0.0)),
        first_gated_rank,
        float(result.get("mean_stress_latency_ms_mean", 0.0)),
        str(result.get("model_name", "")),
    )


def _aggregate_phase(results: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault(str(result["model_name"]), []).append(result)

    aggregate: list[dict[str, Any]] = []
    for model_name, rows in sorted(grouped.items()):
        recommendations = [str(row["recommendation"]) for row in rows]
        trigger_counts: dict[str, int] = {}
        for row in rows:
            for trigger in row["fired_triggers"]:
                trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
        first_gated_steps = [row["first_gated_failure_step"] for row in rows if row["first_gated_failure_step"] is not None]
        aggregate.append(
            {
                "model_name": model_name,
                "runs": len(rows),
                "recommendation_counts": {k: recommendations.count(k) for k in sorted(set(recommendations))},
                "trigger_fire_counts": trigger_counts,
                "benchmark_contract_failures_mean": round(
                    sum(int(row["benchmark_contract_failures"]) for row in rows) / len(rows), 3
                ),
                "recoverable_contract_failures_mean": round(
                    sum(int(row.get("recoverable_contract_failures", 0)) for row in rows) / len(rows), 3
                ),
                "unrecoverable_contract_failures_mean": round(
                    sum(int(row.get("unrecoverable_contract_failures", 0)) for row in rows) / len(rows), 3
                ),
                "mean_stress_latency_ms_mean": round(
                    sum(float(row["mean_stress_latency_ms"]) for row in rows) / len(rows), 3
                ),
                "first_gated_failure_step_range": (
                    [min(first_gated_steps), max(first_gated_steps)] if first_gated_steps else None
                ),
            }
        )

    aggregate.sort(key=_aggregate_rank_key)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in aggregate:
        counts = row.get("recommendation_counts") or {}
        regime = min(
            counts.items(),
            key=lambda item: (RECOMMENDATION_ORDER.get(str(item[0]), 99), -int(item[1])),
        )[0] if counts else "abort"
        grouped[str(regime)].append(row)
    return {"models": aggregate, "regimes": grouped}


def _write_markdown_report(path: Path, *, baseline: list[dict[str, Any]], expansion: list[dict[str, Any]]) -> None:
    lines: list[str] = []
    lines.append("# Unified Weekend Sweep")
    lines.append("")
    lines.append("## Baseline")
    lines.append("")
    for row in baseline:
        lines.append(
            f"- {row['model_name']}: rec={row['recommendation']} triggers={row['fired_triggers']} "
            f"contract_failures={row['benchmark_contract_failures']} "
            f"recoverable={row.get('recoverable_contract_failures', 0)} "
            f"unrecoverable={row.get('unrecoverable_contract_failures', 0)} "
            f"first_gated={row['first_gated_failure_step']} "
            f"mean_latency_ms={round(float(row['mean_stress_latency_ms']), 1)}"
        )
    lines.append("")
    lines.append("## Expansion")
    lines.append("")
    if expansion:
        for row in expansion:
            lines.append(
                f"- {row['model_name']} temp={row['temperature']} max_tokens={row['max_tokens']} seed={row['seed']}: "
                f"rec={row['recommendation']} triggers={row['fired_triggers']} "
                f"contract_failures={row['benchmark_contract_failures']} "
                f"recoverable={row.get('recoverable_contract_failures', 0)} "
                f"unrecoverable={row.get('unrecoverable_contract_failures', 0)} "
                f"first_gated={row['first_gated_failure_step']} "
                f"mean_latency_ms={round(float(row['mean_stress_latency_ms']), 1)}"
            )
    else:
        lines.append("- No expansion runs executed.")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _format_seconds(seconds: float | None) -> str:
    if seconds is None:
        return "n/a"
    total = max(0, int(round(seconds)))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _write_progress(
    *,
    output_dir: Path,
    total_runs: int,
    completed_runs: int,
    current: dict[str, Any] | None,
    completed_durations: list[float],
    phase: str,
) -> None:
    avg_sec = (sum(completed_durations) / len(completed_durations)) if completed_durations else None
    remaining_runs = max(0, total_runs - completed_runs - (1 if current else 0))
    eta_sec = (avg_sec * remaining_runs) if avg_sec is not None else None
    payload = {
        "phase": phase,
        "total_runs": total_runs,
        "completed_runs": completed_runs,
        "remaining_runs": max(0, total_runs - completed_runs),
        "current_run": current,
        "average_duration_sec": round(avg_sec, 3) if avg_sec is not None else None,
        "eta_sec": round(eta_sec, 3) if eta_sec is not None else None,
        "eta_human": _format_seconds(eta_sec),
    }
    (output_dir / "progress.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_one(*, python_bin: str, config_path: Path, run_id: str, progress: bool) -> subprocess.CompletedProcess[str]:
    cmd = [python_bin, "-m", "lte", "unified", "--config", str(config_path), "--run-id", run_id, "--force"]
    if progress:
        cmd.append("--progress")
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        assert proc.stdout is not None
        output_lines: list[str] = []
        for line in proc.stdout:
            print(line, end="")
            output_lines.append(line)
        returncode = proc.wait()
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=returncode,
            stdout="".join(output_lines),
            stderr="",
        )
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a staged weekend LTE unified sweep.")
    parser.add_argument("--base-config", default="configs/default.yaml", help="Canonical single-model config template.")
    parser.add_argument(
        "--models-config",
        default="configs/stress_all_models.yaml",
        help="Config used only to source the model list for the weekend sweep.",
    )
    parser.add_argument("--output-dir", default="results/weekend_sweep", help="Directory for generated configs and summaries.")
    parser.add_argument("--python-bin", default=sys.executable, help="Python binary to use for invoking `python -m lte unified`.")
    parser.add_argument(
        "--top-k",
        type=int,
        default=0,
        help="How many models from baseline advance to the expansion phase. Use 0 to advance all models.",
    )
    parser.add_argument("--baseline-temps", default="0.0,0.2", help="Comma-separated temperatures for baseline.")
    parser.add_argument("--baseline-max-tokens", default="192", help="Comma-separated max_tokens values for baseline.")
    parser.add_argument("--baseline-seeds", default="0,1,2", help="Comma-separated seeds for baseline.")
    parser.add_argument("--expansion-temps", default="0.5", help="Comma-separated temperatures for expansion phase.")
    parser.add_argument("--expansion-max-tokens", default="128,256", help="Comma-separated max_tokens values for expansion phase.")
    parser.add_argument("--expansion-seeds", default="0,1,2", help="Comma-separated seeds for expansion phase.")
    parser.add_argument("--preflight-only", action="store_true", help="Write the plan and configs without running the matrix.")
    parser.add_argument("--progress", action="store_true", help="Pass through unified progress output for each run.")
    parser.add_argument("--resume", action="store_true", help="Skip runs whose summary.json already exists.")
    parser.add_argument("--stop-on-error", action="store_true", help="Abort the sweep on the first failed run.")
    parser.add_argument("--skip-expansion", action="store_true", help="Run only the baseline phase.")
    return parser


def _parse_csv_numbers(raw: str, *, float_mode: bool) -> list[int] | list[float]:
    values = [piece.strip() for piece in raw.split(",") if piece.strip()]
    if not values:
        raise ValueError("Expected at least one value")
    if float_mode:
        return [float(value) for value in values]
    return [int(value) for value in values]


def _execute_spec(
    *,
    spec: RunSpec,
    cfg_path: Path,
    unified_results_dir: Path,
    python_bin: str,
    progress: bool,
    resume: bool,
) -> RunOutcome:
    run_dir = unified_results_dir / f"unified_{spec.run_id}"
    summary_path = run_dir / "summary.json"
    if resume and summary_path.exists():
        summary = _run_summary(run_dir)
        if not isinstance(summary.get("models"), list) or not summary.get("models"):
            # Treat error-only summaries as not resumable-complete; rerun them.
            pass
        else:
            return RunOutcome(
                stage=spec.stage,
                model_name=spec.model_name,
                temperature=spec.temperature,
                max_tokens=spec.max_tokens,
                seed=spec.seed,
                run_id=spec.run_id,
                status="completed",
                run_dir=str(run_dir),
                duration_sec=0.0,
                **_extract_model_summary(summary),
            )

    started = time.time()
    proc = _run_one(python_bin=python_bin, config_path=cfg_path, run_id=spec.run_id, progress=progress)
    duration_sec = time.time() - started
    if proc.returncode != 0:
        return RunOutcome(
            stage=spec.stage,
            model_name=spec.model_name,
            temperature=spec.temperature,
            max_tokens=spec.max_tokens,
            seed=spec.seed,
            run_id=spec.run_id,
            status="failed",
            run_dir=str(run_dir),
            duration_sec=duration_sec,
            error=(proc.stderr or proc.stdout or "").strip(),
        )

    summary = _run_summary(run_dir)
    if not isinstance(summary.get("models"), list) or not summary.get("models"):
        return RunOutcome(
            stage=spec.stage,
            model_name=spec.model_name,
            temperature=spec.temperature,
            max_tokens=spec.max_tokens,
            seed=spec.seed,
            run_id=spec.run_id,
            status="failed",
            run_dir=str(run_dir),
            duration_sec=duration_sec,
            error=f"invalid summary: {json.dumps(summary)}",
        )
    return RunOutcome(
        stage=spec.stage,
        model_name=spec.model_name,
        temperature=spec.temperature,
        max_tokens=spec.max_tokens,
        seed=spec.seed,
        run_id=spec.run_id,
        status="completed",
        run_dir=str(run_dir),
        duration_sec=duration_sec,
        **_extract_model_summary(summary),
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    base_config_path = Path(args.base_config)
    models_config_path = Path(args.models_config)
    output_dir = Path(args.output_dir)
    generated_configs_dir = output_dir / "generated_configs"
    unified_results_dir = output_dir / "runs"
    output_dir.mkdir(parents=True, exist_ok=True)

    base_config = _load_yaml(base_config_path)
    models = _models_from_config(models_config_path)

    baseline_specs = _build_run_specs(
        models=models,
        temperatures=list(_parse_csv_numbers(args.baseline_temps, float_mode=True)),
        max_tokens=list(_parse_csv_numbers(args.baseline_max_tokens, float_mode=False)),
        seeds=list(_parse_csv_numbers(args.baseline_seeds, float_mode=False)),
        stage="baseline",
    )

    manifest = {
        "base_config": str(base_config_path),
        "models_config": str(models_config_path),
        "baseline_runs": [asdict(spec) | {"run_id": spec.run_id} for spec in baseline_specs],
        "top_k": args.top_k,
        "skip_expansion": bool(args.skip_expansion),
        "expansion_temps": list(_parse_csv_numbers(args.expansion_temps, float_mode=True)),
        "expansion_max_tokens": list(_parse_csv_numbers(args.expansion_max_tokens, float_mode=False)),
        "expansion_seeds": list(_parse_csv_numbers(args.expansion_seeds, float_mode=False)),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    _write_progress(
        output_dir=output_dir,
        total_runs=len(baseline_specs),
        completed_runs=0,
        current=None,
        completed_durations=[],
        phase="baseline_pending",
    )

    for spec in baseline_specs:
        _write_run_config(
            base_config=base_config,
            spec=spec,
            config_path=generated_configs_dir / f"{spec.run_id}.yaml",
            results_dir=unified_results_dir,
        )

    if args.preflight_only:
        print(str(output_dir / "manifest.json"))
        return 0

    baseline_outcomes: list[dict[str, Any]] = []
    completed_durations: list[float] = []
    total_runs = len(baseline_specs)
    for idx, spec in enumerate(baseline_specs, start=1):
        cfg_path = generated_configs_dir / f"{spec.run_id}.yaml"
        _write_progress(
            output_dir=output_dir,
            total_runs=total_runs,
            completed_runs=idx - 1,
            current={
                "index": idx,
                "stage": "baseline",
                "model_name": spec.model_name,
                "temperature": spec.temperature,
                "max_tokens": spec.max_tokens,
                "seed": spec.seed,
                "run_id": spec.run_id,
            },
            completed_durations=completed_durations,
            phase="baseline_running",
        )
        avg_sec = (sum(completed_durations) / len(completed_durations)) if completed_durations else None
        eta_sec = (avg_sec * (total_runs - idx + 1)) if avg_sec is not None else None
        print(
            f"[{idx}/{total_runs}] baseline model={spec.model_name} "
            f"temp={spec.temperature} max_tokens={spec.max_tokens} seed={spec.seed} "
            f"eta={_format_seconds(eta_sec)}"
        )
        outcome = asdict(
            _execute_spec(
                spec=spec,
                cfg_path=cfg_path,
                unified_results_dir=unified_results_dir,
                python_bin=args.python_bin,
                progress=args.progress,
                resume=args.resume,
            )
        )
        baseline_outcomes.append(outcome)
        if outcome.get("duration_sec") is not None:
            completed_durations.append(float(outcome["duration_sec"]))
        (output_dir / "baseline_results.json").write_text(json.dumps(baseline_outcomes, indent=2), encoding="utf-8")
        _write_progress(
            output_dir=output_dir,
            total_runs=total_runs,
            completed_runs=idx,
            current=None,
            completed_durations=completed_durations,
            phase="baseline_running",
        )
        print(
            f"  -> {outcome['status']} run_id={spec.run_id} duration={_format_seconds(outcome.get('duration_sec'))}"
        )
        if outcome["status"] == "failed" and args.stop_on_error:
            raise SystemExit(f"Baseline run failed: {spec.run_id}")

    baseline_results = [row for row in baseline_outcomes if row["status"] == "completed"]
    baseline_phase = _aggregate_phase(baseline_results) if baseline_results else {"models": []}
    (output_dir / "baseline_phase_summary.json").write_text(json.dumps(baseline_phase, indent=2), encoding="utf-8")

    if args.skip_expansion:
        _write_markdown_report(output_dir / "report.md", baseline=baseline_results, expansion=[])
        _write_progress(
            output_dir=output_dir,
            total_runs=total_runs,
            completed_runs=total_runs,
            current=None,
            completed_durations=completed_durations,
            phase="completed",
        )
        print(str(output_dir / "report.md"))
        return 0

    if int(args.top_k) <= 0:
        selected_models = list(models)
    else:
        ranked_models = [row["model_name"] for row in baseline_phase["models"][: int(args.top_k)]]
        selected_models = [model for model in models if str(model["name"]) in ranked_models]

    expansion_specs = _build_run_specs(
        models=selected_models,
        temperatures=list(_parse_csv_numbers(args.expansion_temps, float_mode=True)),
        max_tokens=list(_parse_csv_numbers(args.expansion_max_tokens, float_mode=False)),
        seeds=list(_parse_csv_numbers(args.expansion_seeds, float_mode=False)),
        stage="expansion",
    )
    for spec in expansion_specs:
        _write_run_config(
            base_config=base_config,
            spec=spec,
            config_path=generated_configs_dir / f"{spec.run_id}.yaml",
            results_dir=unified_results_dir,
        )

    expansion_outcomes: list[dict[str, Any]] = []
    overall_total = len(baseline_specs) + len(expansion_specs)
    for offset, spec in enumerate(expansion_specs, start=1):
        cfg_path = generated_configs_dir / f"{spec.run_id}.yaml"
        current_index = len(baseline_specs) + offset
        _write_progress(
            output_dir=output_dir,
            total_runs=overall_total,
            completed_runs=current_index - 1,
            current={
                "index": current_index,
                "stage": "expansion",
                "model_name": spec.model_name,
                "temperature": spec.temperature,
                "max_tokens": spec.max_tokens,
                "seed": spec.seed,
                "run_id": spec.run_id,
            },
            completed_durations=completed_durations,
            phase="expansion_running",
        )
        avg_sec = (sum(completed_durations) / len(completed_durations)) if completed_durations else None
        eta_sec = (avg_sec * (overall_total - current_index + 1)) if avg_sec is not None else None
        print(
            f"[{current_index}/{overall_total}] expansion model={spec.model_name} "
            f"temp={spec.temperature} max_tokens={spec.max_tokens} seed={spec.seed} "
            f"eta={_format_seconds(eta_sec)}"
        )
        outcome = asdict(
            _execute_spec(
                spec=spec,
                cfg_path=cfg_path,
                unified_results_dir=unified_results_dir,
                python_bin=args.python_bin,
                progress=args.progress,
                resume=args.resume,
            )
        )
        expansion_outcomes.append(outcome)
        if outcome.get("duration_sec") is not None:
            completed_durations.append(float(outcome["duration_sec"]))
        (output_dir / "expansion_results.json").write_text(json.dumps(expansion_outcomes, indent=2), encoding="utf-8")
        _write_progress(
            output_dir=output_dir,
            total_runs=overall_total,
            completed_runs=current_index,
            current=None,
            completed_durations=completed_durations,
            phase="expansion_running",
        )
        print(
            f"  -> {outcome['status']} run_id={spec.run_id} duration={_format_seconds(outcome.get('duration_sec'))}"
        )
        if outcome["status"] == "failed" and args.stop_on_error:
            raise SystemExit(f"Expansion run failed: {spec.run_id}")

    expansion_results = [row for row in expansion_outcomes if row["status"] == "completed"]
    _write_markdown_report(output_dir / "report.md", baseline=baseline_results, expansion=expansion_results)
    _write_progress(
        output_dir=output_dir,
        total_runs=overall_total,
        completed_runs=overall_total,
        current=None,
        completed_durations=completed_durations,
        phase="completed",
    )
    print(str(output_dir / "report.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
