from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from lte.config import RunConfig
from lte.contracts import evaluate_contract
from lte.io import ensure_dir, read_jsonl, write_jsonl
from lte.metrics import (
    expansion_ratio,
    length_overrun_rate,
    runaway_continuation_score,
    verbosity_drift,
)
from lte.reporting import generate_report_markdown
from lte.schema import GenerationRecord
from lte.stress import run_stress
from lte.suites import PromptCase, PromptSuite, load_suite


@dataclass(frozen=True)
class UnifiedRunPaths:
    run_dir: Path
    benchmark_jsonl: Path
    stress_jsonl: Path
    merged_jsonl: Path
    summary_json: Path
    report_md: Path


def _base_metrics(*, input_tokens: int, output_tokens: int, max_tokens: int, output_text: str) -> dict[str, float | int]:
    return {
        "expansion_ratio": round(expansion_ratio(input_tokens=input_tokens, output_tokens=output_tokens), 6),
        "length_overrun_rate": length_overrun_rate(output_tokens=output_tokens, max_tokens=max_tokens),
        "runaway_continuation_score": round(runaway_continuation_score(output_text), 6),
    }


def _benchmark_row(
    *,
    run_id: str,
    backend: Any,
    model: Any,
    suite: PromptSuite,
    case: PromptCase,
    result: Any,
    cfg: RunConfig,
) -> dict[str, Any]:
    max_tokens = case.max_tokens if case.max_tokens is not None else cfg.generation.max_tokens
    contract_eval = evaluate_contract(contract=case.contract, output_text=result.output_text)
    row = GenerationRecord(
        run_id=run_id,
        timestamp=GenerationRecord.now_timestamp(),
        model_name=model.name,
        backend=backend.name,
        model_revision=model.revision,
        suite_name=suite.name,
        prompt_id=case.id,
        prompt_text=case.prompt,
        system_text=case.system,
        max_tokens=max_tokens,
        temperature=cfg.generation.temperature,
        top_p=cfg.generation.top_p,
        seed=cfg.generation.seed,
        output_text=result.output_text,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        token_count_method=result.token_count_method,
        stop_reason=result.stop_reason,
        latency_ms=result.latency_ms,
    ).to_dict()
    row.update(_base_metrics(
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        max_tokens=max_tokens,
        output_text=result.output_text,
    ))
    row["mode"] = "benchmark"
    row["experiment_family"] = suite.experiment_family
    row["tags"] = list(case.tags)
    row["trigger_targets"] = list(case.trigger_targets)
    row["contract"] = case.contract
    row["contract_evaluation"] = contract_eval.to_dict()
    row["contract_passed"] = contract_eval.passed
    row["failure_class"] = contract_eval.failure_class
    row["recoverable_failure"] = contract_eval.recoverable_failure
    if case.pair_id:
        row["pair_id"] = case.pair_id
    if case.variant:
        row["variant"] = case.variant
    return row


def _benchmark_rows(*, cfg: RunConfig, backend: Any, run_id: str, progress: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    suites = [load_suite(path) for path in cfg.suites]

    for model in cfg.models:
        try:
            for suite in suites:
                for case in suite.cases:
                    max_tokens = case.max_tokens if case.max_tokens is not None else cfg.generation.max_tokens
                    result = backend.generate(
                        model_path=model.path,
                        model_name=model.name,
                        prompt_text=case.prompt,
                        system_text=case.system,
                        max_tokens=max_tokens,
                        temperature=cfg.generation.temperature,
                        top_p=cfg.generation.top_p,
                        seed=cfg.generation.seed,
                    )
                    row = _benchmark_row(
                        run_id=run_id,
                        backend=backend,
                        model=model,
                        suite=suite,
                        case=case,
                        result=result,
                        cfg=cfg,
                    )
                    rows.append(row)
                    if progress:
                        print(f"{model.name}\tbenchmark\t{suite.name}\t{case.id}\t{result.output_tokens} tok")
        except Exception as exc:
            rows.append(
                {
                    "record_type": "error",
                    "run_id": run_id,
                    "timestamp": GenerationRecord.now_timestamp(),
                    "model_name": model.name,
                    "backend": backend.name,
                    "suite_name": "run",
                    "mode": "benchmark",
                    "error": str(exc),
                }
            )
        finally:
            backend.reset()
    return rows


def _stress_rows(*, cfg: RunConfig, backend: Any, run_id: str, progress: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for model in cfg.models:
        try:
            raw_rows = run_stress(cfg=cfg, backend=backend, model=model, run_id=run_id, progress=progress)
            for row in raw_rows:
                row.update(
                    _base_metrics(
                        input_tokens=int(row["input_tokens"]),
                        output_tokens=int(row["output_tokens"]),
                        max_tokens=int(row["max_tokens"]),
                        output_text=str(row.get("output_text", "")),
                    )
                )
                row.update(_stress_contract_signals(str(row.get("output_text", ""))))
                row["experiment_family"] = "stress"
                rows.append(row)
        except Exception as exc:
            rows.append(
                {
                    "record_type": "error",
                    "run_id": run_id,
                    "timestamp": GenerationRecord.now_timestamp(),
                    "model_name": model.name,
                    "backend": backend.name,
                    "suite_name": "stress",
                    "mode": "stress",
                    "error": str(exc),
                }
            )
        finally:
            backend.reset()
    return rows


def _paired_verbosity_by_model(records: list[dict[str, Any]]) -> dict[str, list[float]]:
    by_pair: dict[tuple[str, str, str], dict[str, int]] = defaultdict(dict)
    for record in records:
        pair_id = record.get("pair_id")
        variant = record.get("variant")
        if not pair_id or not variant:
            continue
        key = (str(record.get("model_name")), str(record.get("suite_name")), str(pair_id))
        by_pair[key][str(variant)] = int(record.get("output_tokens", 0) or 0)

    model_vd: dict[str, list[float]] = defaultdict(list)
    for (model_name, _suite_name, _pair_id), variants in by_pair.items():
        if "concise" in variants and "detailed" in variants:
            model_vd[model_name].append(
                verbosity_drift(concise_len=variants["concise"], detailed_len=variants["detailed"])
            )
    return model_vd


def _stress_contract_signals(output_text: str) -> dict[str, Any]:
    lines = [line.strip() for line in output_text.splitlines() if line.strip()]
    bullets: list[str] = []
    for line in lines:
        if line.startswith(("- ", "* ", "• ")):
            bullets.append(line[2:].strip())
        elif len(line) > 3 and line[0].isdigit() and line[1] == "." and line[2] == " ":
            bullets.append(line[3:].strip())

    ordered_slots = [
        ("status", ["status", "current status", "report"]),
        ("owner", ["owner", "iris"]),
        ("next_action", ["next action", "action"]),
        ("risk", ["risk"]),
        ("escalation", ["escalat"]),
    ]
    slot_hits: dict[str, bool] = {}
    for idx, (slot, patterns) in enumerate(ordered_slots):
        text = bullets[idx].lower() if idx < len(bullets) else ""
        slot_hits[slot] = any(pattern in text for pattern in patterns)

    owner_preserved = any("iris" in bullet.lower() for bullet in bullets)
    exact_bullet_count = len(bullets) == 5
    return {
        "stress_contract_evaluation": {
            "exact_bullet_count": exact_bullet_count,
            "owner_preserved": owner_preserved,
            "ordered_slot_hits": slot_hits,
            "passed": exact_bullet_count and owner_preserved and all(slot_hits.values()),
        }
    }


def _last_window_has_n(rows: list[dict[str, Any]], *, predicate: Any, required: int, window: int) -> bool:
    if len(rows) < required:
        return False
    for idx in range(len(rows)):
        window_rows = rows[max(0, idx - window + 1) : idx + 1]
        if sum(1 for row in window_rows if predicate(row)) >= required:
            return True
    return False


def _trigger_row(*, status: bool, threshold: str, evidence: dict[str, Any], recommended_action: str) -> dict[str, Any]:
    return {
        "status": "fired" if status else "clear",
        "threshold": threshold,
        "evidence": evidence,
        "recommended_action": recommended_action,
    }


def _dominant_failure_reasons(rows: list[dict[str, Any]]) -> list[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        for reason in row.get("failure_reasons") or []:
            counter[str(reason)] += 1
    return [name for name, _count in counter.most_common(2)]


def summarize_unified_run(*, records: list[dict[str, Any]]) -> dict[str, Any]:
    generation_rows = [row for row in records if "output_tokens" in row and "input_tokens" in row and "max_tokens" in row]
    benchmark_rows = [row for row in generation_rows if row.get("mode") == "benchmark"]
    stress_rows = [row for row in generation_rows if row.get("mode") == "stress"]
    error_rows = [row for row in records if row.get("record_type") == "error"]

    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in generation_rows:
        by_model[str(row.get("model_name", "unknown"))].append(row)

    model_vd = _paired_verbosity_by_model(benchmark_rows)
    per_model: list[dict[str, Any]] = []

    for model_name, model_rows in sorted(by_model.items(), key=lambda item: item[0].lower()):
        model_benchmark_rows = [row for row in model_rows if row.get("mode") == "benchmark"]
        model_stress_rows = sorted(
            [row for row in model_rows if row.get("mode") == "stress"],
            key=lambda row: int(row.get("step", -1)),
        )
        benchmark_contract_misses = [row for row in model_benchmark_rows if not bool(row.get("contract_passed"))]
        recoverable_contract_misses = [row for row in benchmark_contract_misses if bool(row.get("recoverable_failure"))]
        unrecoverable_contract_misses = [row for row in benchmark_contract_misses if not bool(row.get("recoverable_failure"))]
        benchmark_budget_rows = [row for row in model_benchmark_rows if "budget" in (row.get("tags") or [])]
        structured_failure_rows = [
            row
            for row in model_benchmark_rows
            if str(row.get("experiment_family")) in {"structured_contracts", "failure_escalation"}
        ]
        context_pressure_rows = [
            row for row in model_benchmark_rows if str(row.get("experiment_family")) == "context_pressure"
        ]
        failure_escalation_rows = [
            row for row in model_benchmark_rows if str(row.get("experiment_family")) == "failure_escalation"
        ]

        budget_control_failures = [
            row
            for row in benchmark_budget_rows
            if float(row.get("expansion_ratio", 0.0)) >= 1.25 or not bool(row.get("contract_passed"))
        ]
        bounded_lorr_failures = [
            row
            for row in model_benchmark_rows
            if int(row.get("max_tokens", 0)) <= 56 and int(row.get("length_overrun_rate", 0)) == 1
        ]
        over_expansion = len(budget_control_failures) >= 2 or bool(bounded_lorr_failures)

        stress_latency_rows = [
            row for row in model_stress_rows if int(row.get("latency_ms", 0)) > 2500 and int(row.get("input_tokens", 0)) >= 1500
        ]
        hard_latency = len(model_stress_rows[-3:]) >= 3 and sum(
            1 for row in model_stress_rows[-3:] if int(row.get("latency_ms", 0)) > 2500 and int(row.get("input_tokens", 0)) >= 1500
        ) >= 2
        latency_cliff = bool(stress_latency_rows)

        structured_lorr_mean = mean(
            [int(row.get("length_overrun_rate", 0)) for row in structured_failure_rows]
        ) if structured_failure_rows else 0.0
        stress_near_cap_window = _last_window_has_n(
            model_stress_rows,
            predicate=lambda row: int(row.get("length_overrun_rate", 0)) == 1,
            required=2,
            window=5,
        )
        near_cap_pressure = structured_lorr_mean >= 0.20 or stress_near_cap_window

        stress_rcs_rows = [row for row in model_stress_rows if float(row.get("runaway_continuation_score", 0.0)) >= 0.30]
        consecutive_rcs = any(
            float(model_stress_rows[idx].get("runaway_continuation_score", 0.0)) >= 0.30
            and float(model_stress_rows[idx - 1].get("runaway_continuation_score", 0.0)) >= 0.30
            for idx in range(1, len(model_stress_rows))
        )
        last_five_mean_rcs = (
            mean(float(row.get("runaway_continuation_score", 0.0)) for row in model_stress_rows[-5:])
            if len(model_stress_rows) >= 5
            else 0.0
        )
        repetition_loop = consecutive_rcs or last_five_mean_rcs >= 0.22

        context_benchmark_failures = [
            row for row in context_pressure_rows if not bool(row.get("contract_passed"))
        ]
        first_gated_failure = next(
            (
                row
                for row in model_stress_rows
                if bool(row.get("is_failure")) and int(row.get("input_tokens", 0)) >= 1500
            ),
            None,
        )
        dominant_reasons = _dominant_failure_reasons(
            [row for row in model_stress_rows if int(row.get("input_tokens", 0)) >= 1500 and bool(row.get("is_failure"))]
        )
        stress_contract_break_rows = [
            row for row in model_stress_rows if not bool((row.get("stress_contract_evaluation") or {}).get("passed", True))
        ]
        context_decay = len(context_benchmark_failures) >= 2 or (
            first_gated_failure is not None and any(reason in {"rcs", "lorr"} for reason in dominant_reasons)
        )

        persistent_failure_row = next(
            (
                row
                for row in model_stress_rows
                if int(row.get("consecutive_failures", 0)) >= int(row.get("failure_consecutive_required", 3))
            ),
            None,
        )
        benchmark_persistent_failure = (
            len(failure_escalation_rows) >= 2
            and all(not bool(row.get("contract_passed")) for row in failure_escalation_rows)
        )
        persistent_failure = persistent_failure_row is not None or benchmark_persistent_failure

        trigger_summary = {
            "over_expansion": _trigger_row(
                status=over_expansion,
                threshold=">=2 budget-tagged benchmark misses with ER>=1.25 or contract failure, or any max_tokens<=56 row with LORR=1",
                evidence={
                    "budget_control_failures": [row["prompt_id"] for row in budget_control_failures],
                    "bounded_lorr_failures": [row["prompt_id"] for row in bounded_lorr_failures],
                },
                recommended_action="retry",
            ),
            "latency_cliff": _trigger_row(
                status=latency_cliff,
                threshold="stress latency_ms>2500 after input_tokens>=1500; hard trigger if 2 of last 3 stress steps exceed it",
                evidence={
                    "gated_latency_steps": [row["step"] for row in stress_latency_rows],
                    "hard_trigger_last_three": hard_latency,
                },
                recommended_action="escalate" if hard_latency else "retry",
            ),
            "near_cap_pressure": _trigger_row(
                status=near_cap_pressure,
                threshold="benchmark LORR mean across structured_contracts+failure_escalation >=0.20, or stress LORR=1 on any 2 steps within 5-step window",
                evidence={
                    "structured_lorr_mean": round(structured_lorr_mean, 6),
                    "stress_window_hit": stress_near_cap_window,
                },
                recommended_action="repair",
            ),
            "repetition_loop": _trigger_row(
                status=repetition_loop,
                threshold="stress RCS>=0.30 on 2 consecutive steps, or last 5 stress steps mean RCS>=0.22",
                evidence={
                    "high_rcs_steps": [row["step"] for row in stress_rcs_rows],
                    "two_consecutive": consecutive_rcs,
                    "last_five_mean_rcs": round(last_five_mean_rcs, 6),
                },
                recommended_action="escalate",
            ),
            "context_decay": _trigger_row(
                status=context_decay,
                threshold=">=2 context_pressure benchmark contract failures, or gated stress failure dominated by repetition/near-cap reasons",
                evidence={
                    "context_benchmark_failures": [row["prompt_id"] for row in context_benchmark_failures],
                    "first_gated_failure_step": first_gated_failure.get("step") if first_gated_failure else None,
                    "dominant_gated_failure_reasons": dominant_reasons,
                    "stress_contract_break_steps": [row["step"] for row in stress_contract_break_rows[:5]],
                },
                recommended_action="escalate",
            ),
            "persistent_failure": _trigger_row(
                status=persistent_failure,
                threshold="stress reaches 3 consecutive failed steps, or both failure_escalation benchmark cases fail contract",
                evidence={
                    "stress_step": persistent_failure_row.get("step") if persistent_failure_row else None,
                    "stress_reasons": persistent_failure_row.get("failure_reasons") if persistent_failure_row else [],
                    "failure_escalation_contract_failures": [row["prompt_id"] for row in failure_escalation_rows if not bool(row.get("contract_passed"))],
                },
                recommended_action="abort",
            ),
        }

        fired = [name for name, summary in trigger_summary.items() if summary["status"] == "fired"]
        if persistent_failure or len(fired) >= 3:
            recommendation = "abort"
            rationale = "persistent failure fired or three trigger families fired"
        elif any(trigger_summary[name]["status"] == "fired" for name in ("context_decay", "repetition_loop", "latency_cliff")):
            recommendation = "escalate"
            rationale = "context decay, repetition loop, or latency cliff fired without persistent failure"
        elif recoverable_contract_misses and not unrecoverable_contract_misses and any(
            row.get("experiment_family") == "structured_contracts" for row in recoverable_contract_misses
        ) and not repetition_loop and not latency_cliff:
            recommendation = "repair"
            rationale = "recoverable benchmark contract failures without repetition or latency cliff"
        elif len(benchmark_contract_misses) == 1 and not any(
            trigger_summary[name]["status"] == "fired"
            for name in ("latency_cliff", "near_cap_pressure", "repetition_loop", "context_decay", "persistent_failure")
        ):
            recommendation = "retry"
            rationale = "one isolated benchmark contract miss with no stress trigger"
        elif over_expansion or near_cap_pressure:
            recommendation = "retry"
            rationale = "budget or cap pressure trigger fired"
        else:
            recommendation = "continue"
            rationale = "no trigger fired"

        per_model.append(
            {
                "model_name": model_name,
                "benchmark_cases": len(model_benchmark_rows),
                "stress_steps": len(model_stress_rows),
                "errors": sum(1 for row in error_rows if row.get("model_name") == model_name),
                "metrics": {
                    "mean_expansion_ratio": round(
                        mean(float(row.get("expansion_ratio", 0.0)) for row in model_benchmark_rows), 6
                    )
                    if model_benchmark_rows
                    else None,
                    "mean_length_overrun_rate": round(
                        mean(int(row.get("length_overrun_rate", 0)) for row in model_rows), 6
                    )
                    if model_rows
                    else None,
                    "mean_runaway_continuation_score": round(
                        mean(float(row.get("runaway_continuation_score", 0.0)) for row in model_rows), 6
                    )
                    if model_rows
                    else None,
                    "mean_verbosity_drift": round(mean(model_vd[model_name]), 6)
                    if model_vd.get(model_name)
                    else None,
                    "mean_stress_latency_ms": round(
                        mean(int(row.get("latency_ms", 0)) for row in model_stress_rows), 3
                    )
                    if model_stress_rows
                    else None,
                    "benchmark_contract_failures": len(benchmark_contract_misses),
                    "recoverable_contract_failures": len(recoverable_contract_misses),
                    "unrecoverable_contract_failures": len(unrecoverable_contract_misses),
                },
                "trigger_summary": trigger_summary,
                "recommendation": {
                    "action": recommendation,
                    "rationale": rationale,
                },
            }
        )

    overall_action = "continue"
    for candidate in ("abort", "escalate", "repair", "retry"):
        if any(model["recommendation"]["action"] == candidate for model in per_model):
            overall_action = candidate
            break

    return {
        "records": {
            "total": len(records),
            "generation_rows": len(generation_rows),
            "benchmark_rows": len(benchmark_rows),
            "stress_rows": len(stress_rows),
            "error_rows": len(error_rows),
        },
        "models": per_model,
        "overall_recommendation": overall_action,
    }


def generate_unified_report_markdown(*, records: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = ["# LTE Unified Report", ""]
    lines.append(f"- Overall recommendation: `{summary['overall_recommendation']}`")
    counts = summary["records"]
    lines.append(
        f"- Records: {counts['total']} total, {counts['benchmark_rows']} benchmark, {counts['stress_rows']} stress, {counts['error_rows']} errors"
    )
    lines.append("")
    lines.append("## Trigger Summary")
    lines.append("")
    for model in summary["models"]:
        lines.append(f"### {model['model_name']}")
        lines.append(f"- Recommendation: `{model['recommendation']['action']}`")
        lines.append(f"- Rationale: {model['recommendation']['rationale']}")
        for trigger_name, trigger in model["trigger_summary"].items():
            lines.append(
                f"- {trigger_name}: status={trigger['status']} threshold={trigger['threshold']} evidence={json.dumps(trigger['evidence'], sort_keys=True)} action={trigger['recommended_action']}"
            )
        lines.append("")

    lines.append("## Aggregated Generation Report")
    lines.append("")
    lines.append(generate_report_markdown(records).strip())
    lines.append("")
    return "\n".join(lines)


def run_unified(
    *,
    cfg: RunConfig,
    backend: Any,
    run_id: str,
    progress: bool = False,
    force: bool = False,
) -> UnifiedRunPaths:
    root_dir = ensure_dir(cfg.output.results_dir)
    dir_name = run_id if run_id.startswith("unified_") else f"unified_{run_id}"
    run_dir = root_dir / dir_name
    if run_dir.exists() and not force:
        raise SystemExit(f"Refusing to overwrite existing unified run: {run_dir} (use --force)")
    ensure_dir(run_dir)

    benchmark_jsonl = run_dir / "benchmark.jsonl"
    stress_jsonl = run_dir / "stress.jsonl"
    merged_jsonl = run_dir / "merged.jsonl"
    summary_json = run_dir / "summary.json"
    report_md = run_dir / "report.md"

    benchmark_rows = _benchmark_rows(cfg=cfg, backend=backend, run_id=run_id, progress=progress)
    write_jsonl(benchmark_jsonl, benchmark_rows)

    stress_rows: list[dict[str, Any]] = []
    if cfg.stress.enabled:
        stress_rows = _stress_rows(cfg=cfg, backend=backend, run_id=run_id, progress=progress)
    write_jsonl(stress_jsonl, stress_rows)

    merged_rows = benchmark_rows + stress_rows
    write_jsonl(merged_jsonl, merged_rows)

    summary = summarize_unified_run(records=merged_rows)
    summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report_md.write_text(
        generate_unified_report_markdown(records=merged_rows, summary=summary),
        encoding="utf-8",
    )
    return UnifiedRunPaths(
        run_dir=run_dir,
        benchmark_jsonl=benchmark_jsonl,
        stress_jsonl=stress_jsonl,
        merged_jsonl=merged_jsonl,
        summary_json=summary_json,
        report_md=report_md,
    )


def load_unified_artifacts(run_dir: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = Path(run_dir)
    records = read_jsonl(root / "merged.jsonl")
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    return (records, summary)
