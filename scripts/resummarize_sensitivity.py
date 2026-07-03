"""Re-summarise a threshold-sensitivity sweep with a corrected summariser.

Why this exists: the 2026-06-08 sweep was run before lte/unified.py was
fixed to read trigger thresholds from cfg. The raw stress trajectories
(benchmark.jsonl, stress.jsonl, merged.jsonl) are correct — the stress
runner respected the perturbed thresholds at gating time. Only summary.json
was wrong, because summarize_unified_run used hardcoded values.

This script walks every per-(model, condition) run directory, reads the
variant config (which records the perturbed thresholds), recomputes the
summary using the fixed summariser, and rebuilds the stability report.

Usage:
    python scripts/resummarize_sensitivity.py \
        --in results/threshold_sensitivity \
        --out results/threshold_sensitivity_fixed
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lte.config import load_config
from lte.io import read_jsonl
from lte.unified import summarize_unified_run


def _build_stability_report(table: dict[str, dict[str, str]], baseline_label: str) -> dict:
    report = {"models": [], "all_stable": True, "baseline_label": baseline_label}
    for model, by_label in sorted(table.items()):
        baseline = by_label.get(baseline_label)
        flips = {lab: r for lab, r in sorted(by_label.items()) if r != baseline}
        stable = len(flips) == 0
        if not stable:
            report["all_stable"] = False
        report["models"].append({
            "model": model,
            "baseline_regime": baseline,
            "regimes_by_condition": {lab: r for lab, r in sorted(by_label.items())},
            "stable": stable,
            "flips": flips,
        })
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", required=True)
    ap.add_argument("--out", dest="out_dir", required=True)
    ap.add_argument("--baseline-label", default="f1p0")
    args = ap.parse_args()

    in_root = Path(args.in_dir)
    out_root = Path(args.out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    # model_name -> condition_label -> recommendation
    table: dict[str, dict[str, str]] = {}
    n_resummarised = 0

    for model_dir in sorted(in_root.iterdir()):
        if not model_dir.is_dir():
            continue
        model_slug = model_dir.name
        for cond_dir in sorted(model_dir.iterdir()):
            if not cond_dir.is_dir():
                continue
            cond_label = cond_dir.name
            # Find the variant config (one .yaml in cond_dir).
            yaml_files = list(cond_dir.glob("*.yaml"))
            if not yaml_files:
                print(f"  skip {model_slug}/{cond_label}: no config yaml", file=sys.stderr)
                continue
            cfg_path = yaml_files[0]
            # Find the unified run dir under cond_dir.
            unified_dirs = list(cond_dir.glob("unified_*"))
            if not unified_dirs:
                print(f"  skip {model_slug}/{cond_label}: no unified run dir", file=sys.stderr)
                continue
            run_dir = unified_dirs[0]
            merged = run_dir / "merged.jsonl"
            if not merged.exists():
                print(f"  skip {model_slug}/{cond_label}: no merged.jsonl", file=sys.stderr)
                continue

            cfg = load_config(str(cfg_path))
            records = list(read_jsonl(merged))
            summary = summarize_unified_run(records=records, failure=cfg.stress.failure)
            summary["resummarised_from"] = str(run_dir)

            # Write the corrected summary into the mirror tree.
            out_run_dir = out_root / model_slug / cond_label / run_dir.name
            out_run_dir.mkdir(parents=True, exist_ok=True)
            (out_run_dir / "summary.json").write_text(
                json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
            )
            # Copy the cfg yaml so the corrected tree is self-contained.
            shutil.copy(cfg_path, out_root / model_slug / cond_label / cfg_path.name)

            for model_summary in summary.get("models", []):
                m_name = model_summary.get("model_name", "?")
                rec_obj = model_summary.get("recommendation") or {}
                rec = rec_obj.get("action") if isinstance(rec_obj, dict) else rec_obj
                table.setdefault(m_name, {})[cond_label] = rec
            n_resummarised += 1

    stability = _build_stability_report(table, baseline_label=args.baseline_label)
    report_path = out_root / "stability_report.json"
    report_path.write_text(json.dumps(stability, indent=2), encoding="utf-8")

    print(f"\nRe-summarised {n_resummarised} runs")
    print(f"baseline_label: {stability['baseline_label']}")
    print(f"all_stable:     {stability['all_stable']}")
    print()
    print(f"{'model':<36} {'baseline':<10} {'stable':<8} flips")
    for m in stability["models"]:
        flips_str = ", ".join(f"{k}={v}" for k, v in m["flips"].items()) if m["flips"] else ""
        print(f"  {m['model']:<34} {str(m['baseline_regime']):<10} "
              f"{('STABLE' if m['stable'] else 'FLIPS'):<8} {flips_str}")
    print(f"\nWrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
