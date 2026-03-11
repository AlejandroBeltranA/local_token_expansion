import csv
import json
import subprocess
import sys


def test_failure_cause_script_outputs_expected_counts(tmp_path):
    input_path = tmp_path / "eval.jsonl"
    by_model = tmp_path / "by_model.csv"
    overall = tmp_path / "overall.csv"
    rows = [
        {
            "experiment_id": "E2",
            "attempt_kind": "primary",
            "model": "m1",
            "response": '{"ok": 1}',
            "max_tokens": 100,
            "tokens_out": 99,
            "schema_failure": True,
            "repetition_loop": False,
            "state_contradiction": False,
        },
        {
            "experiment_id": "E3",
            "attempt_kind": "primary",
            "model": "m1",
            "response": "loop loop loop",
            "max_tokens": 100,
            "tokens_out": 10,
            "schema_failure": False,
            "repetition_loop": True,
            "state_contradiction": False,
        },
        {
            "experiment_id": "E3",
            "attempt_kind": "retry",
            "model": "m1",
            "response": "{}",
            "max_tokens": 100,
            "tokens_out": 5,
            "schema_failure": True,
            "repetition_loop": False,
            "state_contradiction": False,
        },
    ]
    input_path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    subprocess.run(
        [
            sys.executable,
            "research/drift_v0/analysis/failure_causes.py",
            "--input",
            str(input_path),
            "--output-by-model",
            str(by_model),
            "--output-overall",
            str(overall),
        ],
        check=True,
    )

    with by_model.open("r", encoding="utf-8", newline="") as infile:
        data = list(csv.DictReader(infile))

    assert len(data) == 1
    row = data[0]
    assert row["model"] == "m1"
    assert row["rows"] == "2"
    assert row["failed"] == "2"
    assert row["near_cap"] == "1"
    assert row["schema_extractable"] == "1"
    assert row["repetition_only"] == "1"
