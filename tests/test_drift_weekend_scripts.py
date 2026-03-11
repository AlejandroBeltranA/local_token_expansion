import json
import subprocess
import sys
from pathlib import Path


def test_prepare_drift_weekend_config_discovers_models(tmp_path):
    models_dir = tmp_path / "mlx_models"
    (models_dir / "Model-A").mkdir(parents=True)
    (models_dir / "Model-B").mkdir(parents=True)
    output = tmp_path / "cfg.json"

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/prepare_drift_weekend_config.py",
            "--models-dir",
            str(models_dir),
            "--output",
            str(output),
            "--max-models",
            "1",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert output.exists()
    cfg = json.loads(output.read_text(encoding="utf-8"))
    assert proc.stdout.strip() == str(output)
    assert cfg["backend"] == "mlx"
    assert len(cfg["models"]) == 1
    assert cfg["models"][0]["name"] == "Model-A"


def test_run_drift_weekend_preflight_only_mock(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(
        json.dumps(
            {
                "models": [{"name": "mock-model", "path": "unused"}],
                "backend": "mock",
                "temperatures": [0.2],
                "top_p": [0.95],
                "max_tokens": 256,
                "seed": 0,
                "history_max_chars": {"e2": 4000, "e3_1k": 4000, "e3_4k": 16000},
            }
        ),
        encoding="utf-8",
    )
    output_root = tmp_path / "artifacts"

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/run_drift_weekend.py",
            "--python-bin",
            sys.executable,
            "--sweep-config",
            str(cfg),
            "--output-root",
            str(output_root),
            "--preflight-only",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Preflight OK" in proc.stdout
    assert output_root.exists()


def test_run_drift_weekend_preflight_fails_for_missing_model(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(
        json.dumps(
            {
                "models": [{"name": "missing-model", "path": str(tmp_path / "nope")}],
                "backend": "mlx",
                "temperatures": [0.2],
                "top_p": [0.95],
            }
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/run_drift_weekend.py",
            "--python-bin",
            sys.executable,
            "--sweep-config",
            str(cfg),
            "--output-root",
            str(tmp_path / "artifacts"),
            "--preflight-only",
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode != 0
    assert "Preflight failed" in proc.stderr or "Preflight failed" in proc.stdout
