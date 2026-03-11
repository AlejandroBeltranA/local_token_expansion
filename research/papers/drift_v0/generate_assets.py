#!/usr/bin/env python3
"""Generate paper tables and SVG figures for drift_v0."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate drift_v0 paper assets.")
    parser.add_argument(
        "--manifest",
        default=str(Path("/tmp/drift_v0_sweep/sweep_manifest.csv")),
        help="Sweep manifest CSV.",
    )
    parser.add_argument(
        "--cause-by-model",
        default=str(Path("/tmp/drift_v0_failure_cause_by_model.csv")),
        help="Failure-cause CSV grouped by model.",
    )
    parser.add_argument(
        "--cause-overall",
        default=str(Path("/tmp/drift_v0_failure_cause_overall.csv")),
        help="Failure-cause CSV aggregated overall.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path("research/papers/drift_v0")),
        help="Directory for generated tables and figures.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def short_name(model_name: str) -> str:
    mapping = {
        'Meta-Llama-3.1-8B-Instruct-3bit': 'Llama-3.1-8B',
        'Mistral-7B-Instruct-v0.3': 'Mistral-7B',
        'Phi-3-mini-4k-instruct-4bit': 'Phi-3-mini',
        'Phi-4-mini-instruct-8bit': 'Phi-4-mini',
        'SmolLM-1.7B-Instruct-4bit': 'SmolLM-1.7B',
    }
    return mapping.get(model_name, model_name)


def make_svg_failure_rates(model_rows: list[dict[str, object]], out: Path) -> None:
    width, height = 980, 520
    ml, mr, mt, mb = 90, 30, 35, 80
    cw, ch = width - ml - mr, height - mt - mb
    y_min, y_max = 0.85, 1.0
    colors = {'e1': '#1f77b4', 'e2': '#ff7f0e', 'e3': '#2ca02c'}
    ticks = [0.85, 0.90, 0.95, 1.00]

    n = len(model_rows)
    group_w = cw / n
    bar_w = group_w * 0.2

    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>",
        "<rect width='100%' height='100%' fill='white'/>",
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#222;} .axis{stroke:#333;stroke-width:1;} .grid{stroke:#ddd;stroke-width:1;} </style>",
        "<text x='490' y='22' text-anchor='middle' font-size='16' font-weight='700'>Primary Failure Rate by Model and Experiment</text>",
    ]

    for t in ticks:
        y = mt + ch * (1 - (t - y_min) / (y_max - y_min))
        parts.append(f"<line x1='{ml}' y1='{y:.2f}' x2='{ml+cw}' y2='{y:.2f}' class='grid'/>")
        parts.append(f"<text x='{ml-10}' y='{y+4:.2f}' text-anchor='end' font-size='12'>{t:.2f}</text>")

    parts.append(f"<line x1='{ml}' y1='{mt+ch}' x2='{ml+cw}' y2='{mt+ch}' class='axis'/>")
    parts.append(f"<line x1='{ml}' y1='{mt}' x2='{ml}' y2='{mt+ch}' class='axis'/>")

    for i, r in enumerate(model_rows):
        gx = ml + i * group_w + group_w * 0.2
        vals = [('e1', r['e1_mean']), ('e2', r['e2_mean']), ('e3', r['e3_mean'])]
        for j, (k, v) in enumerate(vals):
            v = float(v)
            h = max(0.0, (v - y_min) / (y_max - y_min)) * ch
            x = gx + j * bar_w * 1.2
            y = mt + ch - h
            parts.append(f"<rect x='{x:.2f}' y='{y:.2f}' width='{bar_w:.2f}' height='{h:.2f}' fill='{colors[k]}'/>")

        lx = ml + i * group_w + group_w * 0.5
        parts.append(f"<text x='{lx:.2f}' y='{height-45}' text-anchor='middle' font-size='11'>{r['model_short']}</text>")

    ly = height - 20
    lx0 = ml + 140
    for idx, (k, label) in enumerate([('e1', 'E1'), ('e2', 'E2'), ('e3', 'E3')]):
        x = lx0 + idx * 110
        parts.append(f"<rect x='{x}' y='{ly-10}' width='12' height='12' fill='{colors[k]}'/>")
        parts.append(f"<text x='{x+18}' y='{ly}' font-size='12'>{label}</text>")

    parts.append(f"<text x='24' y='{mt + ch/2:.2f}' font-size='12' transform='rotate(-90 24 {mt + ch/2:.2f})'>Failure rate</text>")
    parts.append('</svg>')
    out.write_text('\n'.join(parts))


def make_svg_e3_delta(model_rows: list[dict[str, object]], out: Path) -> None:
    width, height = 920, 430
    ml, mr, mt, mb = 90, 30, 35, 90
    cw, ch = width - ml - mr, height - mt - mb
    y_min, y_max = -0.005, 0.055
    ticks = [-0.005, 0.0, 0.025, 0.05]

    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>",
        "<rect width='100%' height='100%' fill='white'/>",
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#222;} .axis{stroke:#333;stroke-width:1;} .grid{stroke:#ddd;stroke-width:1;} </style>",
        "<text x='460' y='22' text-anchor='middle' font-size='16' font-weight='700'>E3 Context Delta (4k - 1k) by Model</text>",
    ]

    def y_of(v: float) -> float:
        return mt + ch * (1 - (v - y_min) / (y_max - y_min))

    for t in ticks:
        y = y_of(t)
        parts.append(f"<line x1='{ml}' y1='{y:.2f}' x2='{ml+cw}' y2='{y:.2f}' class='grid'/>")
        parts.append(f"<text x='{ml-10}' y='{y+4:.2f}' text-anchor='end' font-size='12'>{t:.3f}</text>")

    parts.append(f"<line x1='{ml}' y1='{y_of(0):.2f}' x2='{ml+cw}' y2='{y_of(0):.2f}' class='axis'/>")
    parts.append(f"<line x1='{ml}' y1='{mt}' x2='{ml}' y2='{mt+ch}' class='axis'/>")

    n = len(model_rows)
    bar_w = cw / (n * 1.9)
    gap = (cw - n * bar_w) / (n + 1)

    for i, r in enumerate(model_rows):
        v = float(r['e3_delta_mean'])
        x = ml + gap + i * (bar_w + gap)
        y0 = y_of(0)
        y = y_of(v)
        h = abs(y - y0)
        y_top = min(y, y0)
        color = '#4c78a8' if v >= 0 else '#d62728'
        parts.append(f"<rect x='{x:.2f}' y='{y_top:.2f}' width='{bar_w:.2f}' height='{h:.2f}' fill='{color}'/>")
        parts.append(f"<text x='{x+bar_w/2:.2f}' y='{height-55}' text-anchor='middle' font-size='11'>{r['model_short']}</text>")
        parts.append(f"<text x='{x+bar_w/2:.2f}' y='{y_top-6:.2f}' text-anchor='middle' font-size='10'>{v:.4f}</text>")

    parts.append(f"<text x='24' y='{mt + ch/2:.2f}' font-size='12' transform='rotate(-90 24 {mt + ch/2:.2f})'>Delta in failure rate</text>")
    parts.append('</svg>')
    out.write_text('\n'.join(parts))


def make_svg_failure_taxonomy(cause_rows: list[dict[str, object]], out: Path) -> None:
    width, height = 980, 460
    ml, mr, mt, mb = 90, 30, 35, 80
    cw, ch = width - ml - mr, height - mt - mb
    colors = {'schema_only': '#ffbf00', 'schema_plus_rep': '#9467bd', 'repetition_only': '#17becf'}

    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>",
        "<rect width='100%' height='100%' fill='white'/>",
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#222;} .axis{stroke:#333;stroke-width:1;} .grid{stroke:#ddd;stroke-width:1;} </style>",
        "<text x='490' y='22' text-anchor='middle' font-size='16' font-weight='700'>Failure Taxonomy Composition (E2/E3 Primary Turns)</text>",
    ]

    for t in [0, 25, 50, 75, 100]:
        y = mt + ch * (1 - t / 100)
        parts.append(f"<line x1='{ml}' y1='{y:.2f}' x2='{ml+cw}' y2='{y:.2f}' class='grid'/>")
        parts.append(f"<text x='{ml-10}' y='{y+4:.2f}' text-anchor='end' font-size='12'>{t}%</text>")

    parts.append(f"<line x1='{ml}' y1='{mt+ch}' x2='{ml+cw}' y2='{mt+ch}' class='axis'/>")
    parts.append(f"<line x1='{ml}' y1='{mt}' x2='{ml}' y2='{mt+ch}' class='axis'/>")

    n = len(cause_rows)
    bar_w = cw / (n * 1.8)
    gap = (cw - n * bar_w) / (n + 1)

    for i, r in enumerate(cause_rows):
        x = ml + gap + i * (bar_w + gap)
        y_cursor = mt + ch
        failed = float(r['failed'])
        for key in ['schema_only', 'schema_plus_rep', 'repetition_only']:
            pct = (float(r[key]) / failed) * 100 if failed else 0.0
            h = ch * pct / 100
            y_cursor -= h
            parts.append(f"<rect x='{x:.2f}' y='{y_cursor:.2f}' width='{bar_w:.2f}' height='{h:.2f}' fill='{colors[key]}'/>")
        parts.append(f"<text x='{x+bar_w/2:.2f}' y='{height-45}' text-anchor='middle' font-size='11'>{r['model_short']}</text>")

    ly = height - 20
    lx0 = ml + 90
    labels = [('schema_only', 'Schema only'), ('schema_plus_rep', 'Schema + repetition'), ('repetition_only', 'Repetition only')]
    for idx, (k, label) in enumerate(labels):
        x = lx0 + idx * 220
        parts.append(f"<rect x='{x}' y='{ly-10}' width='12' height='12' fill='{colors[k]}'/>")
        parts.append(f"<text x='{x+18}' y='{ly}' font-size='12'>{label}</text>")

    parts.append(f"<text x='24' y='{mt + ch/2:.2f}' font-size='12' transform='rotate(-90 24 {mt + ch/2:.2f})'>Share of failed turns</text>")
    parts.append('</svg>')
    out.write_text('\n'.join(parts))


def main() -> None:
    args = parse_args()
    manifest = Path(args.manifest)
    cause_by_model = Path(args.cause_by_model)
    out = Path(args.output_dir)
    fig = out / "figures"
    tab = out / "tables"

    out.mkdir(parents=True, exist_ok=True)
    fig.mkdir(parents=True, exist_ok=True)
    tab.mkdir(parents=True, exist_ok=True)

    manifest_rows = read_csv(manifest)
    cause_rows = read_csv(cause_by_model)

    # Aggregate by model.
    by_model: dict[str, list[dict[str, str]]] = {}
    for r in manifest_rows:
        by_model.setdefault(r['model_name'], []).append(r)

    model_summary: list[dict[str, object]] = []
    for model in sorted(by_model.keys()):
        rows = by_model[model]
        e1_vals = [float(r['e1_primary_failure_rate']) for r in rows]
        e2_vals = [float(r['e2_primary_failure_rate']) for r in rows]
        e3_vals = [float(r['e3_primary_failure_rate']) for r in rows]
        d_vals = [float(r['e3_delta_turn_failure_rate']) for r in rows]
        model_summary.append(
            {
                'model': model,
                'model_short': short_name(model),
                'conditions': len(rows),
                'e1_mean': round(mean(e1_vals), 6),
                'e2_mean': round(mean(e2_vals), 6),
                'e3_mean': round(mean(e3_vals), 6),
                'composite_mean': round(mean(e1_vals + e2_vals + e3_vals), 6),
                'e3_delta_mean': round(mean(d_vals), 6),
            }
        )

    write_csv(
        tab / 'model_summary.csv',
        model_summary,
        ['model', 'model_short', 'conditions', 'e1_mean', 'e2_mean', 'e3_mean', 'composite_mean', 'e3_delta_mean'],
    )

    # Best conditions table.
    best_rows: list[dict[str, object]] = []
    for r in manifest_rows:
        e1 = float(r['e1_primary_failure_rate'])
        e2 = float(r['e2_primary_failure_rate'])
        e3 = float(r['e3_primary_failure_rate'])
        best_rows.append(
            {
                'condition_id': r['condition_id'],
                'model': r['model_name'],
                'temperature': r['temperature'],
                'top_p': r['top_p'],
                'e1': round(e1, 6),
                'e2': round(e2, 6),
                'e3': round(e3, 6),
                'composite': round((e1 + e2 + e3) / 3.0, 6),
            }
        )
    best_rows.sort(key=lambda x: (x['composite'], x['condition_id']))
    write_csv(tab / 'best_conditions_top10.csv', best_rows[:10], ['condition_id', 'model', 'temperature', 'top_p', 'e1', 'e2', 'e3', 'composite'])

    # Shortened cause rows for plotting.
    cause_short = []
    for r in cause_rows:
        cause_short.append(
            {
                **r,
                'model_short': short_name(r['model']),
            }
        )

    make_svg_failure_rates(model_summary, fig / 'figure1_failure_rates_by_model.svg')
    make_svg_e3_delta(model_summary, fig / 'figure2_e3_delta_by_model.svg')
    make_svg_failure_taxonomy(cause_short, fig / 'figure3_failure_taxonomy_by_model.svg')


if __name__ == '__main__':
    main()
