from lte.unified import summarize_unified_run


def test_unified_latency_cliff_escalates_from_spec_rule():
    benchmark_row = {
        "run_id": "r",
        "timestamp": "t",
        "model_name": "m",
        "backend": "mock",
        "model_revision": None,
        "suite_name": "core_conciseness",
        "prompt_id": "p0",
        "prompt_text": "x",
        "system_text": None,
        "max_tokens": 32,
        "temperature": 0.2,
        "top_p": 0.95,
        "seed": 0,
        "output_text": "ok",
        "input_tokens": 20,
        "output_tokens": 10,
        "token_count_method": "approx",
        "stop_reason": "mock",
        "latency_ms": 10,
        "mode": "benchmark",
        "experiment_family": "budget_guardrails",
        "tags": ["budget"],
        "trigger_targets": ["over_expansion"],
                "contract": {"output_mode": "single_sentence", "checks": ["one sentence only"]},
        "contract_evaluation": {
            "passed": True,
            "output_mode": "single_sentence",
            "failure_class": "recoverable",
            "recoverable_failure": False,
            "failed_checks": [],
            "satisfied_checks": ["one sentence only"],
        },
        "contract_passed": True,
        "recoverable_failure": False,
        "expansion_ratio": 0.5,
        "length_overrun_rate": 0,
        "runaway_continuation_score": 0.0,
    }
    stress_rows = []
    for step in range(3):
        stress_rows.append(
            {
                "run_id": "r",
                "timestamp": "t",
                "model_name": "m",
                "backend": "mock",
                "model_revision": None,
                "suite_name": "stress",
                "prompt_id": f"step_{step:04d}",
                "prompt_text": "x",
                "system_text": None,
                "max_tokens": 32,
                "temperature": 0.2,
                "top_p": 0.95,
                "seed": 0,
                "output_text": "ok",
                "input_tokens": 1600 + step,
                "output_tokens": 10,
                "token_count_method": "approx",
                "stop_reason": "mock",
                "latency_ms": 4000,
                "mode": "stress",
                "step": step,
                "is_failure": True,
                "failure_reasons": ["latency"],
                "consecutive_failures": 1,
                "failure_consecutive_required": 3,
                "context_fraction": 0.4,
                "expansion_ratio": 0.01,
                "length_overrun_rate": 0,
                "runaway_continuation_score": 0.0,
            }
        )

    summary = summarize_unified_run(records=[benchmark_row, *stress_rows])

    latency = summary["models"][0]["trigger_summary"]["latency_cliff"]
    assert latency["status"] == "fired"
    assert latency["evidence"]["hard_trigger_last_three"] is True
    assert summary["models"][0]["recommendation"]["action"] == "escalate"
    assert summary["overall_recommendation"] == "escalate"


def test_unified_api_latency_requires_hard_trigger():
    benchmark_row = {
        "run_id": "r",
        "timestamp": "t",
        "model_name": "m",
        "backend": "openai",
        "model_revision": None,
        "suite_name": "core_conciseness",
        "prompt_id": "p0",
        "prompt_text": "x",
        "system_text": None,
        "max_tokens": 32,
        "temperature": 0.2,
        "top_p": 0.95,
        "seed": 0,
        "output_text": "ok",
        "input_tokens": 20,
        "output_tokens": 10,
        "token_count_method": "openai-usage",
        "stop_reason": "stop",
        "latency_ms": 10,
        "mode": "benchmark",
        "experiment_family": "budget_guardrails",
        "tags": ["budget"],
        "trigger_targets": ["over_expansion"],
        "contract": {"output_mode": "single_sentence", "checks": ["one sentence only"]},
        "contract_evaluation": {
            "passed": True,
            "output_mode": "single_sentence",
            "failure_class": "recoverable",
            "recoverable_failure": False,
            "failed_checks": [],
            "satisfied_checks": ["one sentence only"],
        },
        "contract_passed": True,
        "recoverable_failure": False,
        "expansion_ratio": 0.5,
        "length_overrun_rate": 0,
        "runaway_continuation_score": 0.0,
    }
    stress_rows = []
    for step in range(30):
        stress_rows.append(
            {
                "run_id": "r",
                "timestamp": "t",
                "model_name": "m",
                "backend": "openai",
                "model_revision": None,
                "suite_name": "stress",
                "prompt_id": f"step_{step:04d}",
                "prompt_text": "x",
                "system_text": None,
                "max_tokens": 32,
                "temperature": 0.2,
                "top_p": 0.95,
                "seed": 0,
                "output_text": "ok",
                "input_tokens": 1600 + step,
                "output_tokens": 10,
                "token_count_method": "openai-usage",
                "stop_reason": "stop",
                "latency_ms": 4000 if step == 29 else 1000,
                "mode": "stress",
                "step": step,
                "is_failure": step == 29,
                "failure_reasons": ["latency"] if step == 29 else [],
                "consecutive_failures": 1 if step == 29 else 0,
                "failure_consecutive_required": 3,
                "context_fraction": 0.4,
                "expansion_ratio": 0.01,
                "length_overrun_rate": 0,
                "runaway_continuation_score": 0.0,
            }
        )

    summary = summarize_unified_run(records=[benchmark_row, *stress_rows])

    latency = summary["models"][0]["trigger_summary"]["latency_cliff"]
    assert latency["status"] == "clear"
    assert latency["evidence"]["backend_mode"] == "api-hard-only"
    assert latency["evidence"]["hard_trigger_last_three"] is False
    assert summary["models"][0]["recommendation"]["action"] == "continue"


def test_unified_persistent_failure_includes_benchmark_failure_escalation_cases():
    rows = []
    for prompt_id in ("exact_yaml_status", "two_line_recovery_plan"):
        rows.append(
            {
                "run_id": "r",
                "timestamp": "t",
                "model_name": "m",
                "backend": "mock",
                "model_revision": None,
                "suite_name": "persistent_failure_probe",
                "prompt_id": prompt_id,
                "prompt_text": "x",
                "system_text": None,
                "max_tokens": 32,
                "temperature": 0.2,
                "top_p": 0.95,
                "seed": 0,
                "output_text": "bad output",
                "input_tokens": 20,
                "output_tokens": 15,
                "token_count_method": "approx",
                "stop_reason": "mock",
                "latency_ms": 1,
                "mode": "benchmark",
                "experiment_family": "failure_escalation",
                "tags": ["persistent_failure"],
                "trigger_targets": ["persistent_failure"],
                "contract": {},
                "contract_evaluation": {
                    "passed": False,
                    "output_mode": None,
                    "failure_class": "unrecoverable",
                    "recoverable_failure": False,
                    "failed_checks": ["x"],
                    "satisfied_checks": [],
                },
                "contract_passed": False,
                "recoverable_failure": False,
                "expansion_ratio": 0.75,
                "length_overrun_rate": 0,
                "runaway_continuation_score": 0.0,
            }
        )

    summary = summarize_unified_run(records=rows)
    persistent = summary["models"][0]["trigger_summary"]["persistent_failure"]
    assert persistent["status"] == "fired"
    assert sorted(persistent["evidence"]["failure_escalation_contract_failures"]) == [
        "exact_yaml_status",
        "two_line_recovery_plan",
    ]
    assert summary["models"][0]["recommendation"]["action"] == "abort"


def test_unified_repair_requires_only_recoverable_contract_failures():
    rows = [
        {
            "run_id": "r",
            "timestamp": "t",
            "model_name": "m",
            "backend": "mock",
            "model_revision": None,
            "suite_name": "structured_extraction",
            "prompt_id": "emit_csv_rows",
            "prompt_text": "x",
            "system_text": None,
            "max_tokens": 32,
            "temperature": 0.2,
            "top_p": 0.95,
            "seed": 0,
            "output_text": "bad output",
            "input_tokens": 20,
            "output_tokens": 15,
            "token_count_method": "approx",
            "stop_reason": "mock",
            "latency_ms": 1,
            "mode": "benchmark",
            "experiment_family": "structured_contracts",
            "tags": [],
            "trigger_targets": ["near_cap_pressure"],
            "contract": {},
            "contract_evaluation": {
                "passed": False,
                "output_mode": None,
                "failure_class": "recoverable",
                "recoverable_failure": True,
                "failed_checks": ["x"],
                "satisfied_checks": [],
            },
            "contract_passed": False,
            "recoverable_failure": True,
            "expansion_ratio": 0.75,
            "length_overrun_rate": 0,
            "runaway_continuation_score": 0.0,
        }
    ]
    summary = summarize_unified_run(records=rows)
    metrics = summary["models"][0]["metrics"]
    assert metrics["recoverable_contract_failures"] == 1
    assert metrics["unrecoverable_contract_failures"] == 0
    assert summary["models"][0]["recommendation"]["action"] == "repair"
