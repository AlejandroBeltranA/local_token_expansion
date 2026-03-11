from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from lte.backends import MLXBackend, MockBackend
from lte.config import load_config
from lte.io import append_jsonl, ensure_dir
from lte.schema import GenerationRecord
from lte.suites import list_suite_files, load_suite
from lte.reporting import write_report
from lte.stress import run_stress
from lte.unified import run_unified


def _backend_from_name(name: str):
    if name == "mlx":
        return MLXBackend()
    if name == "mock":
        return MockBackend()
    raise ValueError(f"Unknown backend: {name}")


def _default_run_id(run_name: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{run_name}_{stamp}"


def cmd_list_models(args: argparse.Namespace) -> int:
    if args.config:
        cfg = load_config(args.config)
        for m in cfg.models:
            print(f"{m.name}\t{m.path}")
        return 0

    models_root = Path(args.models_dir)
    if not models_root.exists():
        return 0
    for p in sorted([d for d in models_root.iterdir() if d.is_dir()], key=lambda x: x.name.lower()):
        print(p.name)
    return 0


def cmd_list_suites(args: argparse.Namespace) -> int:
    for p in list_suite_files(args.suites_dir):
        print(str(p))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    backend = _backend_from_name(cfg.backend)
    run_id = args.run_id or _default_run_id(cfg.run_name)

    results_dir = ensure_dir(cfg.output.results_dir)
    out_jsonl = results_dir / f"run_{run_id}.jsonl"
    if out_jsonl.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing results: {out_jsonl} (use --force)")

    # Truncate file if exists and --force.
    out_jsonl.write_text("", encoding="utf-8")

    suites = [load_suite(p) for p in cfg.suites]

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
                    record = GenerationRecord(
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
                    # Add suite-level metadata useful for reporting.
                    if case.pair_id:
                        record["pair_id"] = case.pair_id
                    if case.variant:
                        record["variant"] = case.variant
                    append_jsonl(out_jsonl, record)
                    if args.progress:
                        print(f"{model.name}\t{suite.name}\t{case.id}\t{result.output_tokens} tok")
        except Exception as exc:
            append_jsonl(
                out_jsonl,
                {
                    "record_type": "error",
                    "run_id": run_id,
                    "timestamp": GenerationRecord.now_timestamp(),
                    "model_name": model.name,
                    "backend": backend.name,
                    "suite_name": "run",
                    "error": str(exc),
                },
            )
        finally:
            backend.reset()

    if not args.no_report:
        reports_dir = ensure_dir(cfg.output.reports_dir)
        out_dir = reports_dir / f"run_{run_id}"
        write_report(input_jsonl=out_jsonl, output_dir=out_dir)

    print(str(out_jsonl))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    paths = write_report(input_jsonl=args.input, output_dir=args.output)
    print(str(paths.report_md))
    return 0


def cmd_stress(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    if not cfg.stress.enabled:
        raise SystemExit("Config has stress.enabled=false (set true to run stress).")
    backend = _backend_from_name(cfg.backend)
    run_id = args.run_id or _default_run_id(cfg.run_name)

    results_dir = ensure_dir(cfg.output.results_dir)
    out_jsonl = results_dir / f"stress_{run_id}.jsonl"
    if out_jsonl.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing results: {out_jsonl} (use --force)")
    out_jsonl.write_text("", encoding="utf-8")

    for model in cfg.models:
        try:
            rows = run_stress(cfg=cfg, backend=backend, model=model, run_id=run_id, progress=args.progress)
            for row in rows:
                append_jsonl(out_jsonl, row)
        except Exception as exc:
            append_jsonl(
                out_jsonl,
                {
                    "record_type": "error",
                    "run_id": run_id,
                    "timestamp": GenerationRecord.now_timestamp(),
                    "model_name": model.name,
                    "backend": backend.name,
                    "suite_name": "stress",
                    "error": str(exc),
                },
            )
        finally:
            backend.reset()

    if not args.no_report:
        reports_dir = ensure_dir(cfg.output.reports_dir)
        out_dir = reports_dir / f"stress_{run_id}"
        write_report(input_jsonl=out_jsonl, output_dir=out_dir)

    print(str(out_jsonl))
    return 0


def cmd_unified(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    backend = _backend_from_name(cfg.backend)
    run_id = args.run_id or _default_run_id(cfg.run_name)

    paths = run_unified(
        cfg=cfg,
        backend=backend,
        run_id=run_id,
        progress=args.progress,
        force=args.force,
    )
    print(str(paths.run_dir))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="lte", description="Local Token Expansion (LTE) runner")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run LTE suites and write results JSONL")
    p_run.add_argument("--config", required=True, help="Path to YAML config (e.g. configs/default.yaml)")
    p_run.add_argument("--run-id", default=None, help="Override run id (default: derived from run_name + timestamp)")
    p_run.add_argument("--force", action="store_true", help="Overwrite existing results file")
    p_run.add_argument("--progress", action="store_true", help="Print per-case progress")
    p_run.add_argument("--no-report", action="store_true", help="Skip report generation")
    p_run.set_defaults(func=cmd_run)

    p_rep = sub.add_parser("report", help="Generate a markdown report from results JSONL")
    p_rep.add_argument("--input", required=True, help="Input JSONL (e.g. results/run_YYYYMMDD.jsonl)")
    p_rep.add_argument("--output", required=True, help="Output directory (e.g. reports/run_YYYYMMDD/)")
    p_rep.set_defaults(func=cmd_report)

    p_stress = sub.add_parser("stress", help="Run rolling stress test to find sustained-failure cliff")
    p_stress.add_argument("--config", required=True, help="Path to YAML config (must set stress.enabled=true)")
    p_stress.add_argument("--run-id", default=None, help="Override run id (default: derived from run_name + timestamp)")
    p_stress.add_argument("--force", action="store_true", help="Overwrite existing results file")
    p_stress.add_argument("--progress", action="store_true", help="Print per-step progress")
    p_stress.add_argument("--no-report", action="store_true", help="Skip report generation")
    p_stress.set_defaults(func=cmd_stress)

    p_unified = sub.add_parser(
        "unified",
        help="Run benchmark and stress together, then write merged artifacts and one consolidated report",
    )
    p_unified.add_argument("--config", required=True, help="Path to YAML config")
    p_unified.add_argument("--run-id", default=None, help="Override run id (default: derived from run_name + timestamp)")
    p_unified.add_argument("--force", action="store_true", help="Overwrite an existing unified run directory")
    p_unified.add_argument("--progress", action="store_true", help="Print benchmark and stress progress")
    p_unified.set_defaults(func=cmd_unified)

    p_lm = sub.add_parser("list-models", help="List configured models or local mlx_models entries")
    p_lm.add_argument("--config", default=None, help="Optional config; if set, lists models from config")
    p_lm.add_argument("--models-dir", default="mlx_models", help="Local models directory (default: mlx_models)")
    p_lm.set_defaults(func=cmd_list_models)

    p_ls = sub.add_parser("list-suites", help="List available suite YAML files")
    p_ls.add_argument("--suites-dir", default="suites", help="Suite directory (default: suites)")
    p_ls.set_defaults(func=cmd_list_suites)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        rc = int(args.func(args))
    except BrokenPipeError:  # pragma: no cover
        rc = 1
    sys.exit(rc)
