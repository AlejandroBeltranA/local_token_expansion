from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from lte.io import ensure_dir, read_jsonl
from lte.metrics import (
    expansion_ratio,
    length_overrun_rate,
    runaway_continuation_score,
    verbosity_drift,
)


@dataclass(frozen=True)
class ReportPaths:
    output_dir: Path
    report_md: Path


def _format_float(x: float) -> str:
    return f"{x:.4f}"


def _format_int(x: int) -> str:
    return str(int(x))


def generate_report_markdown(records: list[dict[str, Any]]) -> str:
    if not records:
        return "# LTE Report\n\nNo records.\n"

    # Filter to generation-like rows; keep error rows out of metrics aggregates.
    gen_records = [r for r in records if "output_tokens" in r and "input_tokens" in r and "max_tokens" in r]

    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in gen_records:
        by_model[str(r.get("model_name", "unknown"))].append(r)

    approx_any = any(r.get("token_count_method") == "approx" for r in gen_records)

    lines: list[str] = []
    lines.append("# LTE Report")
    lines.append("")
    lines.append(f"- Records: {_format_int(len(records))} (generations: {_format_int(len(gen_records))})")
    lines.append(f"- Models: {_format_int(len(by_model))}")
    lines.append(f"- Approx token counting present: {'yes' if approx_any else 'no'}")
    lines.append("")

    stress_rows = [r for r in gen_records if r.get("mode") == "stress" and isinstance(r.get("step"), int)]
    if stress_rows:
        lines.append("## Stress cliff (persistent failure)")
        lines.append("")
        by_model_stress: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in stress_rows:
            by_model_stress[str(r.get("model_name", "unknown"))].append(r)
        for model, rs in sorted(by_model_stress.items(), key=lambda x: x[0].lower()):
            rs_sorted = sorted(rs, key=lambda x: int(x.get("step", 0)))
            required = int(rs_sorted[0].get("failure_consecutive_required", 3))
            chosen = next(
                (r for r in rs_sorted if int(r.get("consecutive_failures", 0)) >= required),
                None,
            )
            if chosen is None:
                chosen = rs_sorted[-1]
            step = chosen.get("step")
            reasons = chosen.get("failure_reasons") or []
            frac = chosen.get("context_fraction")
            frac_s = _format_float(float(frac)) if isinstance(frac, (int, float)) else "n/a"
            reached = (
                "yes" if int(chosen.get("consecutive_failures", 0)) >= required else "no"
            )
            lines.append(
                f"- {model}: cliff_reached={reached} step={step} reasons={reasons} context_fraction={frac_s}"
            )
        lines.append("")

    lines.append("## Per-model summary")
    lines.append("")
    lines.append("| model | ER(mean) | LORR(mean) | RCS(mean) | VD(mean, paired) |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")

    model_vd: dict[str, list[float]] = defaultdict(list)
    # Compute VD by pairing within (model, suite, pair_id).
    by_pair: dict[tuple[str, str, str], dict[str, int]] = defaultdict(dict)
    for r in gen_records:
        pair_id = r.get("pair_id")
        variant = r.get("variant")
        if not pair_id or not variant:
            continue
        key = (str(r.get("model_name")), str(r.get("suite_name")), str(pair_id))
        out_len = int(r.get("output_tokens") or 0)
        by_pair[key][str(variant)] = out_len
    for (model, _suite, _pair), variants in by_pair.items():
        if "concise" in variants and "detailed" in variants:
            model_vd[model].append(
                verbosity_drift(concise_len=variants["concise"], detailed_len=variants["detailed"])
            )

    for model, rs in sorted(by_model.items(), key=lambda x: x[0].lower()):
        ers = [
            expansion_ratio(input_tokens=int(r["input_tokens"]), output_tokens=int(r["output_tokens"]))
            for r in rs
        ]
        lorrs = [
            length_overrun_rate(output_tokens=int(r["output_tokens"]), max_tokens=int(r["max_tokens"]))
            for r in rs
        ]
        rcss = [runaway_continuation_score(str(r.get("output_text", ""))) for r in rs]
        vds = model_vd.get(model, [])
        lines.append(
            "| "
            + " | ".join(
                [
                    model,
                    _format_float(mean(ers)),
                    _format_float(mean(lorrs)),
                    _format_float(mean(rcss)),
                    _format_float(mean(vds)) if vds else "n/a",
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Per-suite breakdown")
    lines.append("")
    by_suite_model: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in gen_records:
        by_suite_model[(str(r.get("suite_name")), str(r.get("model_name")))].append(r)
    for (suite, model), rs in sorted(by_suite_model.items(), key=lambda x: (x[0][0].lower(), x[0][1].lower())):
        ers = [
            expansion_ratio(input_tokens=int(r["input_tokens"]), output_tokens=int(r["output_tokens"]))
            for r in rs
        ]
        rcss = [runaway_continuation_score(str(r.get("output_text", ""))) for r in rs]
        lines.append(f"### {suite} — {model}")
        lines.append(f"- ER(mean): {_format_float(mean(ers))}")
        lines.append(f"- RCS(mean): {_format_float(mean(rcss))}")
        lines.append("")

    lines.append("## Worst prompts (by metric)")
    lines.append("")
    scored: list[tuple[float, str, dict[str, Any]]] = []
    for r in gen_records:
        score = runaway_continuation_score(str(r.get("output_text", "")))
        scored.append((score, "RCS", r))
    scored.sort(key=lambda x: x[0], reverse=True)
    for score, label, r in scored[:5]:
        lines.append(
            f"- {label}={_format_float(score)} model={r.get('model_name')} suite={r.get('suite_name')} prompt_id={r.get('prompt_id')}"
        )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- VD is computed using `output_tokens` for paired `variant: concise|detailed` cases with the same `pair_id`."
    )
    lines.append(
        "- If any records use approximate token counting, treat ER/LORR/VD as approximate as well."
    )
    lines.append("")
    return "\n".join(lines)


def write_report(*, input_jsonl: str | Path, output_dir: str | Path) -> ReportPaths:
    records = read_jsonl(input_jsonl)
    out_dir = ensure_dir(output_dir)
    report_md = out_dir / "report.md"
    report_md.write_text(generate_report_markdown(records), encoding="utf-8")
    return ReportPaths(output_dir=out_dir, report_md=report_md)
