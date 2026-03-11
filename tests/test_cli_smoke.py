import subprocess
import sys
import json


def test_cli_list_suites():
    proc = subprocess.run(
        [sys.executable, "-m", "lte", "list-suites", "--suites-dir", "suites"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "suites/core_conciseness.yaml" in proc.stdout


def test_cli_run_mock(tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        "\n".join(
            [
                'run_name: "t"',
                "backend: mock",
                "models:",
                '  - name: "m"',
                '    path: "unused"',
                "suites:",
                '  - "suites/core_conciseness.yaml"',
                "generation:",
                "  seed: 0",
                "  max_tokens: 64",
                "output:",
                f'  results_dir: "{tmp_path.as_posix()}/results"',
                f'  reports_dir: "{tmp_path.as_posix()}/reports"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, "-m", "lte", "run", "--config", str(cfg), "--run-id", "x"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "results/run_x.jsonl" in proc.stdout


def test_cli_stress_mock(tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        "\n".join(
            [
                'run_name: "t"',
                "backend: mock",
                "models:",
                '  - name: "m"',
                '    path: "unused"',
                "suites:",
                '  - "suites/core_conciseness.yaml"',
                "generation:",
                "  seed: 0",
                "  max_tokens: 32",
                "output:",
                f'  results_dir: "{tmp_path.as_posix()}/results"',
                f'  reports_dir: "{tmp_path.as_posix()}/reports"',
                "stress:",
                "  enabled: true",
                "  max_steps: 10",
                "  max_runtime_sec: 5",
                "  context_growth: append",
                "  prompt: test",
                "  failure:",
                "    consecutive: 2",
                "    max_rcs: 0.0",
                "",
            ]
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, "-m", "lte", "stress", "--config", str(cfg), "--run-id", "x"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "results/stress_x.jsonl" in proc.stdout


def test_report_ignores_error_rows(tmp_path):
    inp = tmp_path / "in.jsonl"
    out_dir = tmp_path / "out"
    inp.write_text(
        "\n".join(
            [
                '{"record_type":"error","run_id":"r","timestamp":"t","model_name":"m","backend":"mock","suite_name":"stress","error":"boom"}',
                '{"run_id":"r","timestamp":"t","model_name":"m","backend":"mock","model_revision":null,"suite_name":"stress","prompt_id":"p","prompt_text":"x","system_text":null,"max_tokens":10,"temperature":0.2,"top_p":0.95,"seed":0,"output_text":"a b c d a b c d","input_tokens":5,"output_tokens":9,"token_count_method":"approx","stop_reason":"mock","latency_ms":1,"mode":"stress","step":0,"is_failure":false,"failure_reasons":[],"consecutive_failures":0,"failure_consecutive_required":3}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, "-m", "lte", "report", "--input", str(inp), "--output", str(out_dir)],
        check=True,
        capture_output=True,
        text=True,
    )
    report_path = proc.stdout.strip()
    assert report_path.endswith("report.md")
    md = (out_dir / "report.md").read_text(encoding="utf-8")
    assert "Records: 2 (generations: 1)" in md


def test_cli_unified_mock(tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        "\n".join(
            [
                'run_name: "t"',
                "backend: mock",
                "models:",
                '  - name: "m"',
                '    path: "unused"',
                "    context_limit_tokens: 32",
                "suites:",
                '  - "suites/core_conciseness.yaml"',
                '  - "suites/structured_extraction.yaml"',
                "generation:",
                "  seed: 0",
                "  max_tokens: 32",
                "output:",
                f'  results_dir: "{tmp_path.as_posix()}/results"',
                f'  reports_dir: "{tmp_path.as_posix()}/reports"',
                "stress:",
                "  enabled: true",
                "  max_steps: 6",
                "  max_runtime_sec: 5",
                "  context_growth: append",
                "  prompt: test",
                "  failure:",
                "    consecutive: 2",
                "    max_rcs: 0.0",
                "",
            ]
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, "-m", "lte", "unified", "--config", str(cfg), "--run-id", "x"],
        check=True,
        capture_output=True,
        text=True,
    )

    run_dir = tmp_path / "results" / "unified_x"
    assert proc.stdout.strip() == str(run_dir)
    assert (run_dir / "benchmark.jsonl").exists()
    assert (run_dir / "stress.jsonl").exists()
    assert (run_dir / "merged.jsonl").exists()
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "report.md").exists()

    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    benchmark_rows = [line for line in (run_dir / "benchmark.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    stress_rows = [line for line in (run_dir / "stress.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    benchmark_sample = json.loads(benchmark_rows[0])
    stress_sample = json.loads(stress_rows[0])
    assert summary["overall_recommendation"] in {"continue", "retry", "repair", "escalate", "abort"}
    assert summary["records"]["benchmark_rows"] == len(benchmark_rows)
    assert summary["records"]["stress_rows"] == len(stress_rows)
    assert summary["records"]["benchmark_rows"] >= 1
    assert summary["records"]["stress_rows"] >= 1
    assert "contract_evaluation" in benchmark_sample
    assert "expansion_ratio" in benchmark_sample
    assert "length_overrun_rate" in benchmark_sample
    assert "runaway_continuation_score" in benchmark_sample
    assert "runaway_continuation_score" in stress_sample
    assert summary["models"][0]["trigger_summary"]["persistent_failure"]["status"] == "fired"
    assert summary["models"][0]["recommendation"]["action"] == "abort"

    report = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "# LTE Unified Report" in report
    assert "## Trigger Summary" in report
    assert "Overall recommendation: `abort`" in report


def test_cli_unified_preserves_prefixed_run_id(tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        "\n".join(
            [
                'run_name: "t"',
                "backend: mock",
                "models:",
                '  - name: "m"',
                '    path: "unused"',
                "suites:",
                '  - "suites/core_conciseness.yaml"',
                "generation:",
                "  seed: 0",
                "  max_tokens: 32",
                "output:",
                f'  results_dir: "{tmp_path.as_posix()}/results"',
                f'  reports_dir: "{tmp_path.as_posix()}/reports"',
                "stress:",
                "  enabled: false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, "-m", "lte", "unified", "--config", str(cfg), "--run-id", "unified_x"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert proc.stdout.strip() == str(tmp_path / "results" / "unified_x")
