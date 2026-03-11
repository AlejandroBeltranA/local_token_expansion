import json
import subprocess
import sys
from pathlib import Path


def test_unified_weekend_preflight_writes_manifest(tmp_path):
    base_cfg = tmp_path / "base.yaml"
    base_cfg.write_text(
        "\n".join(
            [
                'run_name: "base"',
                'backend: "mock"',
                "models:",
                '  - name: "placeholder"',
                '    path: "mock://placeholder"',
                "suites:",
                f'  - "{tmp_path / "suite.yaml"}"',
                "generation:",
                "  temperature: 0.2",
                "  top_p: 0.95",
                "  seed: 0",
                "  max_tokens: 32",
                "output:",
                f'  results_dir: "{tmp_path / "results"}"',
                f'  reports_dir: "{tmp_path / "reports"}"',
                "stress:",
                "  enabled: true",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "suite.yaml").write_text(
        "\n".join(
            [
                'name: "suite"',
                "cases:",
                '  - id: "c1"',
                '    prompt: "Say hello"',
            ]
        ),
        encoding="utf-8",
    )
    models_cfg = tmp_path / "models.yaml"
    models_cfg.write_text(
        "\n".join(
            [
                'run_name: "models"',
                'backend: "mock"',
                "models:",
                '  - name: "mock-a"',
                '    path: "mock://a"',
                '  - name: "mock-b"',
                '    path: "mock://b"',
                "suites:",
                f'  - "{tmp_path / "suite.yaml"}"',
            ]
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "weekend"

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/run_unified_weekend.py",
            "--base-config",
            str(base_cfg),
            "--models-config",
            str(models_cfg),
            "--output-dir",
            str(output_dir),
            "--preflight-only",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    manifest_path = output_dir / "manifest.json"
    progress_path = output_dir / "progress.json"
    assert proc.stdout.strip() == str(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    assert len(manifest["baseline_runs"]) == 12
    assert manifest["top_k"] == 0
    assert progress["phase"] == "baseline_pending"
    assert progress["completed_runs"] == 0
    generated = sorted((output_dir / "generated_configs").glob("*.yaml"))
    assert len(generated) == 12


def test_unified_weekend_aggregate_summary_prefers_repair_over_abort(tmp_path):
    baseline_phase = {
        "models": [
            {
                "model_name": "repair-model",
                "runs": 6,
                "recommendation_counts": {"repair": 6},
                "trigger_fire_counts": {},
                "benchmark_contract_failures_mean": 7.0,
                "recoverable_contract_failures_mean": 7.0,
                "unrecoverable_contract_failures_mean": 0.0,
                "mean_stress_latency_ms_mean": 2500.0,
                "first_gated_failure_step_range": None,
            },
            {
                "model_name": "abort-model",
                "runs": 6,
                "recommendation_counts": {"abort": 6},
                "trigger_fire_counts": {"persistent_failure": 6},
                "benchmark_contract_failures_mean": 2.0,
                "recoverable_contract_failures_mean": 0.0,
                "unrecoverable_contract_failures_mean": 2.0,
                "mean_stress_latency_ms_mean": 2000.0,
                "first_gated_failure_step_range": [19, 19],
            },
        ],
        "regimes": {
            "repair": [{"model_name": "repair-model"}],
            "abort": [{"model_name": "abort-model"}],
        },
    }
    assert baseline_phase["models"][0]["model_name"] == "repair-model"
    assert "repair" in baseline_phase["regimes"]
    assert "abort" in baseline_phase["regimes"]
