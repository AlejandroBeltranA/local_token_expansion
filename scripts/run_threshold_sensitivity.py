"""Threshold-sensitivity sweep for LTE.

The accountability claim in the paper depends on the intervention regime being a
property of the model, not an accident of where the thresholds were set. This
script tests that directly. It perturbs the continuous stress-failure
thresholds, runs the FULL unified evaluation freshly at each perturbed
setting, and reports whether each model's regime holds.

The stress.failure block has five knobs:
  - max_latency_ms (float)      — scaled by the grid factor
  - max_rcs (float, 0..1)       — scaled by the grid factor, clipped to [0, 1]
  - consecutive (int)           — scaled, rounded, floored at 1
  - latency_only_after_input_tokens (int) — scaled, rounded, floored at 0
  - fail_on_lorr (bool)         — toggle; no continuous range, swept
                                  separately via --include-lorr-toggle

A grid of 1.0 reproduces the baseline thresholds exactly. With the
--include-lorr-toggle flag the script adds two extra conditions at factor 1.0
with fail_on_lorr forced True/False so the binary knob also gets a sensitivity
read.

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
        --grid 0.8,0.9,1.0,1.1,1.2 \
        --include-lorr-toggle

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

# Continuous thresholds the grid factor scales. fail_on_lorr is a boolean
# toggle and is swept separately via --include-lorr-toggle, not scaled.
SCALABLE = ("max_latency_ms", "max_rcs")
INT_SCALABLE = ("consecutive", "latency_only_after_input_tokens")
# max_rcs is a ratio in [0, 1]; the scale can push it out of range.
CLIPPED = {"max_rcs": (0.0, 1.0)}

RECOMMENDATION_ORDER = {
    "continue": 0,
    "retry": 1,
    "repair": 2,
    "escalate": 3,
    "abort": 4,
}


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _perturbed_failure_block(
    base_failure: dict[str, Any],
    factor: float,
    *,
    lorr_override: bool | None = None,
) -> dict[str, Any]:
    out = copy.deepcopy(base_failure)
    for key in SCALABLE:
        if out.get(key) is not None:
            scaled = type(base_failure[key])(base_failure[key] * factor)
            if key in CLIPPED:
                lo, hi = CLIPPED[key]
                scaled = type(scaled)(max(lo, min(hi, scaled)))
            out[key] = scaled
    for key in INT_SCALABLE:
        if out.get(key) is not None:
            floor = 1 if key == "consecutive" else 0
            out[key] = max(floor, round(base_failure[key] * factor))
    if lorr_override is not None:
        out["fail_on_lorr"] = lorr_override
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
    ap.add_argument("--include-lorr-toggle", action="store_true",
                    help="add two extra factor-1.0 conditions with "
                         "fail_on_lorr forced True/False to sweep the toggle")
    ap.add_argument("--no-reuse-benchmark", action="store_true",
                    help="re-run the benchmark pass at every threshold "
                         "condition (default: reuse the baseline's "
                         "benchmark rows since benchmark outcomes do not "
                         "depend on stress thresholds)")
    args = ap.parse_args()

    base_path = Path(args.base_config)
    base_raw = _load_yaml(base_path)
    base_failure = (base_raw.get("stress", {}) or {}).get("failure", {}) or {}
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    factors = [float(x) for x in args.grid.split(",")]
    # Build the condition list. Grid conditions are labelled by their float
    # factor; lorr-toggle conditions get explicit names so they show up in the
    # stability report separately from the grid.
    conditions: list[tuple[str, dict[str, Any]]] = []
    for factor in factors:
        tag = f"f{str(factor).replace('.', 'p')}"
        conditions.append((tag, _perturbed_failure_block(base_failure, factor)))
    if args.include_lorr_toggle:
        for value in (True, False):
            tag = f"lorr_{'on' if value else 'off'}"
            conditions.append((tag, _perturbed_failure_block(
                base_failure, 1.0, lorr_override=value)))
    baseline_label = "f1p0"

    # Reorder so the baseline condition runs first. Its benchmark.jsonl is
    # then reused by every other condition: benchmark contract outcomes do
    # not depend on stress thresholds (only stress rows do), so re-running
    # the benchmark pass per condition is wasted work — most of the API/MLX
    # cost goes to the long stress runs, not the short benchmark probes.
    reuse = not args.no_reuse_benchmark
    if reuse:
        conditions.sort(key=lambda lf: 0 if lf[0] == baseline_label else 1)
        if conditions[0][0] != baseline_label:
            raise SystemExit(
                f"--no-reuse-benchmark not set but baseline {baseline_label!r} "
                f"is not in the condition list; pass --grid that includes 1.0 "
                f"or set --no-reuse-benchmark."
            )

    # model -> condition_label -> recommendation
    table: dict[str, dict[str, str]] = {}
    baseline_benchmark_jsonl: Path | None = None

    for label, failure_block in conditions:
        run_name = f"sensitivity_{label}"
        variant_results = out_root / label
        cfg_path = _write_variant_config(base_raw, failure_block, run_name,
                                         variant_results, args.backend)
        cfg = load_config(str(cfg_path))
        backend = _backend_from_name(cfg.backend)
        reuse_path = baseline_benchmark_jsonl if reuse and label != baseline_label else None
        reuse_tag = " (benchmark reused)" if reuse_path else ""
        print(f"[sensitivity] {label} thresholds={failure_block}{reuse_tag}")
        paths = run_unified(
            cfg=cfg, backend=backend, run_id=run_name, force=True,
            reuse_benchmark_from=reuse_path,
        )
        if reuse and label == baseline_label:
            baseline_benchmark_jsonl = paths.benchmark_jsonl
        summary = json.loads(Path(paths.summary_json).read_text(encoding="utf-8"))
        for model_summary in summary.get("models", []):
            model_name = model_summary.get("model_name", "?")
            rec_obj = model_summary.get("recommendation") or {}
            rec = rec_obj.get("action") if isinstance(rec_obj, dict) else rec_obj
            table.setdefault(model_name, {})[label] = rec

    stability = _build_stability_report(table, baseline_label=baseline_label)
    report_path = out_root / "stability_report.json"
    report_path.write_text(json.dumps(stability, indent=2), encoding="utf-8")
    _print_stability(stability)
    print(f"\nWrote {report_path}")
    return 0


def _build_stability_report(table: dict[str, dict[str, str]],
                            baseline_label: str) -> dict[str, Any]:
    report: dict[str, Any] = {"models": [], "all_stable": True,
                              "baseline_label": baseline_label}
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
