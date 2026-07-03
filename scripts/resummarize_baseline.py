"""Re-summarise a baseline weekend-sweep run with the cfg-driven summariser.

Why this exists: the API baseline runs in results/api_rerun/ were summarised
before lte/unified.py was fixed to read trigger thresholds from cfg, so their
per-run summary.json trigger description strings carry the hardcoded defaults
(e.g. latency_ms>2500) instead of the per-model configured values
(API models use max_latency_ms=8000). The raw trajectories are correct — the
stress runner gated on the configured thresholds — so verdicts and trigger
firings are unaffected; only the human-readable threshold strings are stale.

This script walks each per-run directory, reads that run's generated config,
recomputes summary.json with the fixed summariser, and overwrites it in place.
It refuses to proceed if any verdict or trigger-fire set would change, so the
aggregate baseline_phase_summary.json (which records verdicts/triggers/means)
remains valid without rebuilding.

Usage:
    python scripts/resummarize_baseline.py --dir results/api_rerun
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lte.config import load_config
from lte.io import read_jsonl
from lte.unified import summarize_unified_run


def _fired(summary: dict) -> set[str]:
    m = summary["models"][0]
    return {k for k, v in m["trigger_summary"].items() if v["status"] == "fired"}


def _verdict(summary: dict) -> str:
    rec = summary["models"][0].get("recommendation") or {}
    return rec.get("action") if isinstance(rec, dict) else rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", dest="root", required=True,
                    help="sweep output dir containing runs/ and generated_configs/")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change without writing")
    args = ap.parse_args()

    root = Path(args.root)
    runs_dir = root / "runs"
    cfgs_dir = root / "generated_configs"
    if not runs_dir.is_dir() or not cfgs_dir.is_dir():
        raise SystemExit(f"expected {runs_dir} and {cfgs_dir} to exist")

    written = 0
    drift = []
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        merged = run_dir / "merged.jsonl"
        summary_path = run_dir / "summary.json"
        cfg_path = cfgs_dir / f"{run_dir.name.replace('unified_', '')}.yaml"
        if not (merged.exists() and summary_path.exists() and cfg_path.exists()):
            print(f"  skip {run_dir.name}: missing merged/summary/config", file=sys.stderr)
            continue

        cfg = load_config(str(cfg_path))
        records = list(read_jsonl(merged))
        new = summarize_unified_run(records=records, failure=cfg.stress.failure)
        old = json.loads(summary_path.read_text())

        # Guard: verdicts and trigger firings must be invariant. Only the
        # threshold description strings are expected to change.
        if _verdict(new) != _verdict(old) or _fired(new) != _fired(old):
            drift.append((run_dir.name, _verdict(old), _verdict(new),
                          sorted(_fired(old)), sorted(_fired(new))))
            continue

        if not args.dry_run:
            summary_path.write_text(json.dumps(new, indent=2, sort_keys=True), encoding="utf-8")
        written += 1

    if drift:
        print("\nABORTED: verdict/trigger drift detected — not a string-only fix:", file=sys.stderr)
        for name, ov, nv, ot, nt in drift:
            print(f"  {name}: {ov}->{nv}  {ot}->{nt}", file=sys.stderr)
        return 1

    verb = "would rewrite" if args.dry_run else "rewrote"
    print(f"{verb} {written} per-run summary.json files (verdicts/triggers unchanged)")
    print("aggregate baseline_phase_summary.json is unaffected and remains valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
