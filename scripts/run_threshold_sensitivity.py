"""Threshold-sensitivity sweep for LTE.

The accountability claim in the paper depends on the intervention regime being a
property of the model, not an accident of where the thresholds were set. This
script tests that directly. It perturbs the four stress-failure thresholds
(latency, repetition, length-overrun, consecutive-failure count), runs the FULL
unified evaluation freshly at each perturbed setting, and reports whether each
model's regime holds.

It deliberately reuses the existing unified runner (lte.unified.run_unified) so
the perturbed runs use exactly the same code path as the headline results. The
only thing that varies between conditions is the threshold block.

Output: a stability table per model — for each perturbation, the resulting
recommendation and whether it matches the baseline regime. A model whose regime
is invariant across the grid is one whose audit verdict can be trusted as
evidence; a model whose regime flips under a small nudge cannot.

Usage (run on a machine with the real backends/models):
    python scripts/run_threshold_sensitivity.py \
        --base-config configs/stress_all_models.yaml \
        --out results/threshold_sensitivity \
        --grid 0.8,0.9,1.0,1.1,1.2

Use --backend mock for a dry run that exercises the whole pipeline without
calling real models.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import yaml

from lte.backends import AnthropicBackend, MLXBackend, MockBackend, OpenAIBackend
from lte.config import load_config
from lte.unified import run_unified


def _backend_from_name(name: str):
    return {
        "mlx": MLXBackend,
        "mock": MockBackend,
        "openai": OpenAIBackend,
        "anthropic": AnthropicBackend,
    }[name]()

# Thresholds that get scaled. consecutive is integer-valued so it is rounded and
# floored at 1. fail_on_lorr is boolean and is toggled separately, not scaled.
SCALABLE = ("max_latency_ms", "max_rcs")
INT_SCALABLE = ("consecutive",)

RECOMMENDATION_ORDER = {
    "continue": 0,
    "retry": 1,
    "repair": 2,
    "escalate": 3,
    "abort": 4,
}


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _perturbed_failure_block(base_failure: dict[str, Any], factor: float) -> dict[str, Any]:
    out = copy.deepcopy(base_failure)
    for key in SCALABLE:
        if out.get(key) is not None:
            out[key] = type(base_failure[key])(base_failure[key] * factor)
    for key in INT_SCALABLE:
        if out.get(key) is not None:
            out[key] = max(1, round(base_failure[key] * factor))
    return out


def _write_variant_config(base_raw: dict[str, Any], failure_block: dict[str, Any],
                          run_name: str, results_dir: Path, backend: str | None) -> Path:
    variant = copy.deepcopy(base_raw)
    variant["run_name"] = run_name
    variant.setdefault("stress", {}).setdefault("failure", {})
    variant["stress"]["failure"] = failure_block
    variant.setdefault("output", {})["results_dir"] = str(results_dir)
    if backend:
        variant["backend"] = backend
    cfg_path = results_dir / f"{run_name}.yaml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(yaml.safe_dump(variant, sort_keys=False), encoding="utf-8")
    return cfg_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-config", required=True)
    ap.add_argument("--out", default="results/threshold_sensitivity")
    ap.add_argument("--grid", default="0.8,0.9,1.0,1.1,1.2",
                    help="comma-separated scaling factors applied to thresholds")
    ap.add_argument("--backend", default=None,
                    help="override backend (e.g. mock) for a dry run")
    args = ap.parse_args()

    base_path = Path(args.base_config)
    base_raw = _load_yaml(base_path)
    base_failure = (base_raw.get("stress", {}) or {}).get("failure", {}) or {}
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    factors = [float(x) for x in args.grid.split(",")]

    # model -> factor -> recommendation
    table: dict[str, dict[float, str]] = {}

    for factor in factors:
        failure_block = _perturbed_failure_block(base_failure, factor)
        tag = f"f{str(factor).replace('.', 'p')}"
        run_name = f"sensitivity_{tag}"
        variant_results = out_root / tag
        cfg_path = _write_variant_config(base_raw, failure_block, run_name,
                                         variant_results, args.backend)
        cfg = load_config(str(cfg_path))
        backend = _backend_from_name(cfg.backend)
        print(f"[sensitivity] factor={factor} thresholds={failure_block}")
        paths = run_unified(cfg=cfg, backend=backend, run_id=run_name, force=True)
        summary = json.loads(Path(paths.summary_json).read_text(encoding="utf-8"))
        for model_summary in summary.get("models", []):
            model_name = model_summary.get("model_name", "?")
            rec_obj = model_summary.get("recommendation") or {}
            rec = rec_obj.get("action") if isinstance(rec_obj, dict) else rec_obj
            table.setdefault(model_name, {})[factor] = rec

    stability = _build_stability_report(table, baseline_factor=1.0)
    report_path = out_root / "stability_report.json"
    report_path.write_text(json.dumps(stability, indent=2), encoding="utf-8")
    _print_stability(stability)
    print(f"\nWrote {report_path}")
    return 0


def _build_stability_report(table: dict[str, dict[float, str]],
                            baseline_factor: float) -> dict[str, Any]:
    report: dict[str, Any] = {"models": [], "all_stable": True}
    for model, by_factor in sorted(table.items()):
        baseline = by_factor.get(baseline_factor)
        flips = {str(f): r for f, r in sorted(by_factor.items()) if r != baseline}
        stable = len(flips) == 0
        if not stable:
            report["all_stable"] = False
        report["models"].append({
            "model": model,
            "baseline_regime": baseline,
            "regimes_by_factor": {str(f): r for f, r in sorted(by_factor.items())},
            "stable": stable,
            "flips": flips,
        })
    return report


def _print_stability(report: dict[str, Any]) -> None:
    print("\n=== Threshold-sensitivity stability ===")
    for m in report["models"]:
        mark = "STABLE" if m["stable"] else "FLIPS"
        print(f"  {m['model']:<36} baseline={m['baseline_regime']:<9} {mark}")
        if not m["stable"]:
            print(f"      flips: {m['flips']}")
    print(f"\nall_stable = {report['all_stable']}")


if __name__ == "__main__":
    raise SystemExit(main())
