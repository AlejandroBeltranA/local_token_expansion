#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

TRIGGERS = ("schema_failure", "repetition_loop", "state_contradiction")
RETRY_PREFIX = "retry_"
E3_BUDGET_KEYS = ("context_budget", "context_limit", "context_window", "budget", "e3_condition")
ATTEMPT_PRIMARY = "primary"
ATTEMPT_RETRY = "retry"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute paper-ready drift-v0 metrics from evaluated JSONL logs."
    )
    parser.add_argument("--input", required=True, help="Evaluated JSONL file.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional directory for report artifacts (Markdown, JSON, CSV).",
    )
    return parser.parse_args()


def episode_id(row: dict[str, Any]) -> str:
    if row.get("episode_id"):
        return str(row["episode_id"])
    return f"{row.get('run_id', 'run')}:{row.get('task_id', 'task')}"


def parse_turn(row: dict[str, Any]) -> int:
    try:
        return int(row.get("turn", 1))
    except (TypeError, ValueError):
        return 1


def has_failure(row: dict[str, Any]) -> bool:
    return any(bool(row.get(name)) for name in TRIGGERS)


def attempt_kind(row: dict[str, Any]) -> str:
    value = str(row.get("attempt_kind", ATTEMPT_PRIMARY)).strip().lower()
    if value in {ATTEMPT_PRIMARY, ATTEMPT_RETRY}:
        return value
    return ATTEMPT_PRIMARY


def retry_succeeded(row: dict[str, Any]) -> bool:
    if row.get("recovered") is not None:
        return bool(row.get("recovered"))
    return not has_failure(row)


def parse_budget_label(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip().lower().replace(" ", "")
    if not raw:
        return None
    if raw in {"1k", "1024", "1024tok", "1024tokens"}:
        return "1k"
    if raw in {"4k", "4096", "4096tok", "4096tokens"}:
        return "4k"
    if "1k" in raw or "1024" in raw:
        return "1k"
    if "4k" in raw or "4096" in raw:
        return "4k"
    return None


def e3_condition(row: dict[str, Any]) -> str:
    if str(row.get("experiment_id", "")).upper() != "E3":
        return "na"
    for key in E3_BUDGET_KEYS:
        label = parse_budget_label(row.get(key))
        if label:
            return label
    run_id_label = parse_budget_label(row.get("run_id"))
    if run_id_label:
        return run_id_label
    return "unknown"


def percentile(values: list[int], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    pos = (len(ordered) - 1) * pct
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    if low == high:
        return float(ordered[low])
    frac = pos - low
    return ordered[low] * (1.0 - frac) + ordered[high] * frac


def ratio(num: int, den: int) -> float:
    return float(num) / den if den else 0.0


def format_float(value: float) -> str:
    return f"{value:.3f}"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    sep = ["---"] * len(headers)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(headers)
        writer.writerows(rows)


def compute_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts_by_exp = Counter()
    fail_by_exp = Counter()
    escalations_by_exp = Counter()
    episodes_by_exp: dict[str, set[str]] = defaultdict(set)
    failed_episodes_by_exp: dict[str, set[str]] = defaultdict(set)
    escalated_episodes_by_exp: dict[str, set[str]] = defaultdict(set)
    trigger_counts_by_exp: dict[str, Counter[str]] = defaultdict(Counter)

    first_failure_turns_by_exp: dict[str, list[int]] = defaultdict(list)
    first_failure_seen: set[tuple[str, str]] = set()

    rows_by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        exp = str(row.get("experiment_id", "unknown"))
        ep = episode_id(row)
        failed = has_failure(row)
        counts_by_exp[exp] += 1
        episodes_by_exp[exp].add(ep)
        rows_by_episode[ep].append(row)

        for name in TRIGGERS:
            if bool(row.get(name)):
                trigger_counts_by_exp[exp][name] += 1

        if failed:
            fail_by_exp[exp] += 1
            failed_episodes_by_exp[exp].add(ep)
            key = (exp, ep)
            if key not in first_failure_seen:
                first_failure_turns_by_exp[exp].append(parse_turn(row))
                first_failure_seen.add(key)

        if bool(row.get("escalated")):
            escalations_by_exp[exp] += 1
            escalated_episodes_by_exp[exp].add(ep)

    recovery_attempts_total = 0
    recovery_attempts_evaluable = 0
    recovery_success = 0
    recovery_attempts_by_exp = Counter()
    recovery_evaluable_by_exp = Counter()
    recovery_success_by_exp = Counter()
    primary_turns_by_exp = Counter()
    primary_failures_by_exp = Counter()
    retries_attempted_by_exp = Counter()
    retries_success_by_exp = Counter()
    retries_escalated_by_exp = Counter()
    retries_unresolved_by_exp = Counter()

    for row in rows:
        exp = str(row.get("experiment_id", "unknown"))
        kind = attempt_kind(row)
        if kind == ATTEMPT_PRIMARY:
            primary_turns_by_exp[exp] += 1
            if has_failure(row):
                primary_failures_by_exp[exp] += 1
            continue

        retries_attempted_by_exp[exp] += 1
        if retry_succeeded(row):
            retries_success_by_exp[exp] += 1
        else:
            retries_unresolved_by_exp[exp] += 1
        if bool(row.get("escalated")):
            retries_escalated_by_exp[exp] += 1

    for ep_rows in rows_by_episode.values():
        ep_rows.sort(key=parse_turn)
        for idx, row in enumerate(ep_rows):
            exp = str(row.get("experiment_id", "unknown"))
            action = str(row.get("intervention_action", ""))
            if not action.startswith(RETRY_PREFIX):
                continue
            recovery_attempts_total += 1
            recovery_attempts_by_exp[exp] += 1

            explicit = row.get("recovered")
            inferred: bool | None = None
            if explicit is not None:
                inferred = bool(explicit)
            elif idx + 1 < len(ep_rows):
                inferred = not has_failure(ep_rows[idx + 1])

            if inferred is None:
                continue
            recovery_attempts_evaluable += 1
            recovery_evaluable_by_exp[exp] += 1
            if inferred:
                recovery_success += 1
                recovery_success_by_exp[exp] += 1

    summary_rows: list[dict[str, Any]] = []
    for exp in sorted(counts_by_exp):
        turns = counts_by_exp[exp]
        failed_turns = fail_by_exp[exp]
        episodes = len(episodes_by_exp[exp])
        failed_episodes = len(failed_episodes_by_exp[exp])
        escalated_turns = escalations_by_exp[exp]
        escalated_episodes = len(escalated_episodes_by_exp[exp])
        summary_rows.append(
            {
                "experiment_id": exp,
                "turns": turns,
                "episodes": episodes,
                "failed_turns": failed_turns,
                "turn_failure_rate": ratio(failed_turns, turns),
                "failed_episodes": failed_episodes,
                "episode_failure_rate": ratio(failed_episodes, episodes),
                "escalated_turns": escalated_turns,
                "escalation_turn_rate": ratio(escalated_turns, turns),
                "escalated_episodes": escalated_episodes,
                "escalation_episode_rate": ratio(escalated_episodes, episodes),
                "recovery_attempts": recovery_attempts_by_exp[exp],
                "recovery_evaluable": recovery_evaluable_by_exp[exp],
                "recovery_success": recovery_success_by_exp[exp],
                "recovery_success_rate": ratio(
                    recovery_success_by_exp[exp], recovery_evaluable_by_exp[exp]
                ),
            }
        )

    trigger_rows: list[dict[str, Any]] = []
    for exp in sorted(counts_by_exp):
        for trigger in TRIGGERS:
            failures = trigger_counts_by_exp[exp][trigger]
            trigger_rows.append(
                {
                    "experiment_id": exp,
                    "trigger": trigger,
                    "count": failures,
                    "rate_per_turn": ratio(failures, counts_by_exp[exp]),
                }
            )

    closed_loop_rows: list[dict[str, Any]] = []
    for exp in sorted(counts_by_exp):
        primary_turns = primary_turns_by_exp[exp]
        primary_failures = primary_failures_by_exp[exp]
        retries_attempted = retries_attempted_by_exp[exp]
        retries_success = retries_success_by_exp[exp]
        retries_escalated = retries_escalated_by_exp[exp]
        retries_unresolved = retries_unresolved_by_exp[exp]
        closed_loop_rows.append(
            {
                "experiment_id": exp,
                "primary_turns": primary_turns,
                "primary_failures": primary_failures,
                "primary_failure_rate": ratio(primary_failures, primary_turns),
                "retries_attempted": retries_attempted,
                "retries_success": retries_success,
                "retry_effectiveness_rate": ratio(retries_success, retries_attempted),
                "retries_escalated": retries_escalated,
                "escalation_after_retry_rate": ratio(retries_escalated, retries_attempted),
                "retries_unresolved": retries_unresolved,
            }
        )

    first_failure_rows: list[dict[str, Any]] = []
    for exp in sorted(first_failure_turns_by_exp):
        values = first_failure_turns_by_exp[exp]
        if not values:
            continue
        first_failure_rows.append(
            {
                "experiment_id": exp,
                "n_failed_episodes": len(values),
                "mean_turn": statistics.fmean(values),
                "median_turn": statistics.median(values),
                "p25_turn": percentile(values, 0.25),
                "p75_turn": percentile(values, 0.75),
            }
        )

    e3_by_condition: dict[str, dict[str, float]] = {}
    for condition in ("1k", "4k"):
        bucket = [
            row
            for row in rows
            if str(row.get("experiment_id", "unknown")) == "E3" and e3_condition(row) == condition
        ]
        if not bucket:
            continue

        turns = len(bucket)
        eps = {episode_id(row) for row in bucket}
        failed_turns = sum(1 for row in bucket if has_failure(row))
        escalated_eps = {episode_id(row) for row in bucket if bool(row.get("escalated"))}

        by_ep: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in bucket:
            by_ep[episode_id(row)].append(row)

        recovery_evaluable = 0
        recovery_success_local = 0
        first_failure_values: list[int] = []

        for ep_rows in by_ep.values():
            ep_rows.sort(key=parse_turn)
            first_recorded = False
            for idx, row in enumerate(ep_rows):
                if has_failure(row) and not first_recorded:
                    first_failure_values.append(parse_turn(row))
                    first_recorded = True

                action = str(row.get("intervention_action", ""))
                if not action.startswith(RETRY_PREFIX):
                    continue
                explicit = row.get("recovered")
                inferred: bool | None = None
                if explicit is not None:
                    inferred = bool(explicit)
                elif idx + 1 < len(ep_rows):
                    inferred = not has_failure(ep_rows[idx + 1])
                if inferred is None:
                    continue
                recovery_evaluable += 1
                if inferred:
                    recovery_success_local += 1

        e3_by_condition[condition] = {
            "turn_failure_rate": ratio(failed_turns, turns),
            "escalation_episode_rate": ratio(len(escalated_eps), len(eps)),
            "recovery_success_rate": ratio(recovery_success_local, recovery_evaluable),
            "first_failure_turn_mean": statistics.fmean(first_failure_values)
            if first_failure_values
            else 0.0,
        }

    e3_delta = {}
    if "1k" in e3_by_condition and "4k" in e3_by_condition:
        one = e3_by_condition["1k"]
        four = e3_by_condition["4k"]
        for metric in (
            "turn_failure_rate",
            "escalation_episode_rate",
            "recovery_success_rate",
            "first_failure_turn_mean",
        ):
            e3_delta[metric] = four[metric] - one[metric]

    return {
        "overview": {
            "input_rows": len(rows),
            "experiments": sorted(counts_by_exp.keys()),
        },
        "failure_and_escalation_by_experiment": summary_rows,
        "trigger_failure_by_experiment": trigger_rows,
        "first_failure_turn_distribution": first_failure_rows,
        "recovery": {
            "attempts_total": recovery_attempts_total,
            "attempts_evaluable": recovery_attempts_evaluable,
            "success_total": recovery_success,
            "success_rate": ratio(recovery_success, recovery_attempts_evaluable),
        },
        "closed_loop_primary_vs_retry": closed_loop_rows,
        "e3_condition_metrics": e3_by_condition,
        "e3_degradation_delta_4k_minus_1k": e3_delta,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary_headers = [
        "Experiment",
        "Turns",
        "Episodes",
        "Failed Turns",
        "Turn Failure Rate",
        "Failed Episodes",
        "Episode Failure Rate",
        "Escalated Episodes",
        "Escalation Episode Rate",
        "Recovery Success Rate",
    ]
    summary_rows = [
        [
            str(row["experiment_id"]),
            str(row["turns"]),
            str(row["episodes"]),
            str(row["failed_turns"]),
            format_float(row["turn_failure_rate"]),
            str(row["failed_episodes"]),
            format_float(row["episode_failure_rate"]),
            str(row["escalated_episodes"]),
            format_float(row["escalation_episode_rate"]),
            format_float(row["recovery_success_rate"]),
        ]
        for row in report["failure_and_escalation_by_experiment"]
    ]

    trigger_headers = ["Experiment", "Trigger", "Count", "Rate per Turn"]
    trigger_rows = [
        [
            str(row["experiment_id"]),
            str(row["trigger"]),
            str(row["count"]),
            format_float(row["rate_per_turn"]),
        ]
        for row in report["trigger_failure_by_experiment"]
    ]

    first_headers = ["Experiment", "N Failed Episodes", "Mean", "Median", "P25", "P75"]
    first_rows = [
        [
            str(row["experiment_id"]),
            str(row["n_failed_episodes"]),
            format_float(row["mean_turn"]),
            format_float(row["median_turn"]),
            format_float(row["p25_turn"]),
            format_float(row["p75_turn"]),
        ]
        for row in report["first_failure_turn_distribution"]
    ]

    e3_headers = ["Metric", "1k", "4k", "Delta (4k-1k)"]
    metrics = (
        "turn_failure_rate",
        "escalation_episode_rate",
        "recovery_success_rate",
        "first_failure_turn_mean",
    )
    e3_rows: list[list[str]] = []
    one = report["e3_condition_metrics"].get("1k")
    four = report["e3_condition_metrics"].get("4k")
    for metric in metrics:
        one_v = one.get(metric) if one else None
        four_v = four.get(metric) if four else None
        delta_v = report["e3_degradation_delta_4k_minus_1k"].get(metric)
        e3_rows.append(
            [
                metric,
                format_float(one_v) if one_v is not None else "NA",
                format_float(four_v) if four_v is not None else "NA",
                format_float(delta_v) if delta_v is not None else "NA",
            ]
        )

    retry_headers = [
        "Experiment",
        "Primary Turns",
        "Primary Failures",
        "Primary Failure Rate",
        "Retries Attempted",
        "Retries Success",
        "Retry Effectiveness",
        "Retry Escalations",
        "Escalation-After-Retry Rate",
    ]
    retry_rows = [
        [
            str(row["experiment_id"]),
            str(row["primary_turns"]),
            str(row["primary_failures"]),
            format_float(row["primary_failure_rate"]),
            str(row["retries_attempted"]),
            str(row["retries_success"]),
            format_float(row["retry_effectiveness_rate"]),
            str(row["retries_escalated"]),
            format_float(row["escalation_after_retry_rate"]),
        ]
        for row in report["closed_loop_primary_vs_retry"]
    ]

    recovery = report["recovery"]
    lines = [
        "# drift_v0 Analysis Summary",
        "",
        f"- Rows: {report['overview']['input_rows']}",
        f"- Experiments: {', '.join(report['overview']['experiments'])}",
        (
            "- Recovery attempts: "
            f"{recovery['attempts_total']} (evaluable={recovery['attempts_evaluable']}, "
            f"success_rate={format_float(recovery['success_rate'])})"
        ),
        "",
        "## Table 1. Failure and Escalation by Experiment",
        markdown_table(summary_headers, summary_rows),
        "",
        "## Table 2. Trigger Failure Rates by Experiment",
        markdown_table(trigger_headers, trigger_rows),
        "",
        "## Table 3. First-Failure Turn Distribution",
        markdown_table(first_headers, first_rows),
        "",
        "## Table 4. E3 Degradation Delta",
        markdown_table(e3_headers, e3_rows),
        "",
        "## Table 5. Retry Effectiveness and Escalation-After-Retry",
        markdown_table(retry_headers, retry_rows),
        "",
    ]
    return "\n".join(lines)


def write_report_artifacts(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown = render_markdown(report)
    (output_dir / "report.md").write_text(markdown, encoding="utf-8")
    (output_dir / "metrics_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    summary_headers = [
        "experiment_id",
        "turns",
        "episodes",
        "failed_turns",
        "turn_failure_rate",
        "failed_episodes",
        "episode_failure_rate",
        "escalated_turns",
        "escalation_turn_rate",
        "escalated_episodes",
        "escalation_episode_rate",
        "recovery_attempts",
        "recovery_evaluable",
        "recovery_success",
        "recovery_success_rate",
    ]
    summary_rows = [
        [str(row[key]) for key in summary_headers]
        for row in report["failure_and_escalation_by_experiment"]
    ]
    write_csv(output_dir / "failure_escalation_by_experiment.csv", summary_headers, summary_rows)

    trigger_headers = ["experiment_id", "trigger", "count", "rate_per_turn"]
    trigger_rows = [
        [str(row[key]) for key in trigger_headers]
        for row in report["trigger_failure_by_experiment"]
    ]
    write_csv(output_dir / "trigger_failure_by_experiment.csv", trigger_headers, trigger_rows)

    first_headers = [
        "experiment_id",
        "n_failed_episodes",
        "mean_turn",
        "median_turn",
        "p25_turn",
        "p75_turn",
    ]
    first_rows = [
        [str(row[key]) for key in first_headers]
        for row in report["first_failure_turn_distribution"]
    ]
    write_csv(output_dir / "first_failure_turn_distribution.csv", first_headers, first_rows)

    e3_headers = ["metric", "value_1k", "value_4k", "delta_4k_minus_1k"]
    e3_rows = []
    one = report["e3_condition_metrics"].get("1k", {})
    four = report["e3_condition_metrics"].get("4k", {})
    delta = report["e3_degradation_delta_4k_minus_1k"]
    for metric in (
        "turn_failure_rate",
        "escalation_episode_rate",
        "recovery_success_rate",
        "first_failure_turn_mean",
    ):
        e3_rows.append([metric, str(one.get(metric, "")), str(four.get(metric, "")), str(delta.get(metric, ""))])
    write_csv(output_dir / "e3_degradation_delta.csv", e3_headers, e3_rows)

    retry_headers = [
        "experiment_id",
        "primary_turns",
        "primary_failures",
        "primary_failure_rate",
        "retries_attempted",
        "retries_success",
        "retry_effectiveness_rate",
        "retries_escalated",
        "escalation_after_retry_rate",
        "retries_unresolved",
    ]
    retry_rows = [[str(row[key]) for key in retry_headers] for row in report["closed_loop_primary_vs_retry"]]
    write_csv(output_dir / "retry_effectiveness_by_experiment.csv", retry_headers, retry_rows)


def main() -> None:
    args = parse_args()
    rows: list[dict[str, Any]] = []
    with Path(args.input).open("r", encoding="utf-8") as infile:
        for line in infile:
            if not line.strip():
                continue
            rows.append(json.loads(line))

    report = compute_report(rows)
    markdown = render_markdown(report)
    print(markdown)
    if args.output_dir:
        write_report_artifacts(report, Path(args.output_dir))


if __name__ == "__main__":
    main()
