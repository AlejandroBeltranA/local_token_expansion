from lte.config import StressFailureConfig
from lte.unified import summarize_unified_run


def _benchmark_row():
    return {
        "run_id": "r", "timestamp": "t", "model_name": "m", "backend": "mock",
        "model_revision": None, "suite_name": "core_conciseness", "prompt_id": "p0",
        "prompt_text": "x", "system_text": None, "max_tokens": 32, "temperature": 0.2,
        "top_p": 0.95, "seed": 0, "output_text": "ok", "input_tokens": 20,
        "output_tokens": 10, "token_count_method": "approx", "stop_reason": "mock",
        "latency_ms": 10, "mode": "benchmark", "experiment_family": "budget_guardrails",
        "tags": ["budget"], "trigger_targets": ["over_expansion"],
        "contract": {"output_mode": "single_sentence", "checks": ["one sentence only"]},
        "contract_evaluation": {"passed": True, "output_mode": "single_sentence",
            "failure_class": "recoverable", "recoverable_failure": False,
            "failed_checks": [], "satisfied_checks": ["one sentence only"]},
        "contract_passed": True, "recoverable_failure": False, "expansion_ratio": 0.5,
        "length_overrun_rate": 0, "runaway_continuation_score": 0.0,
    }


def _stress_row(*, step, latency_ms, input_tokens, is_failure=False,
                consecutive=0, required=3, rcs=0.0, lorr=0):
    return {
        "run_id": "r", "timestamp": "t", "model_name": "m", "backend": "openai",
        "model_revision": None, "suite_name": "stress", "prompt_id": f"step_{step:04d}",
        "prompt_text": "x", "system_text": None, "max_tokens": 32, "temperature": 0.2,
        "top_p": 0.95, "seed": 0, "output_text": "ok", "input_tokens": input_tokens,
        "output_tokens": 10, "token_count_method": "approx", "stop_reason": "mock",
        "latency_ms": latency_ms, "mode": "stress", "step": step,
        "is_failure": is_failure, "failure_reasons": ["latency"] if is_failure else [],
        "consecutive_failures": consecutive, "failure_consecutive_required": required,
        "context_fraction": 0.4, "expansion_ratio": 0.01,
        "length_overrun_rate": lorr, "runaway_continuation_score": rcs,
    }


# --- Cfg-driven trigger thresholds -----------------------------------------
# These tests prove the bug we found yesterday: summarize_unified_run used
# hardcoded thresholds (2500ms latency, 0.30 RCS, 0.20 LORR, 1500 input
# tokens) regardless of cfg, so the threshold-sensitivity sweep was
# scaling values that the summarizer ignored. Each test below builds a
# stress trajectory that would fire at the legacy hardcoded threshold and
# proves that raising the cfg threshold keeps the trigger clear.


def test_latency_cliff_respects_cfg_max_latency_ms():
    # Three API stress steps at 4000 ms each, after enough input tokens —
    # fires at the legacy 2500 ms hardcoded threshold, must not fire when
    # cfg raises the threshold above 4000 ms.
    rows = [_benchmark_row()] + [
        _stress_row(step=s, latency_ms=4000, input_tokens=1600 + s) for s in range(3)
    ]
    # Legacy (no cfg): fires.
    s_legacy = summarize_unified_run(records=rows)
    assert s_legacy["models"][0]["trigger_summary"]["latency_cliff"]["status"] == "fired"
    # Cfg with raised threshold: clears.
    cfg = StressFailureConfig(
        max_latency_ms=8000, latency_only_after_input_tokens=1500, max_rcs=0.30,
    )
    s_cfg = summarize_unified_run(records=rows, failure=cfg)
    assert s_cfg["models"][0]["trigger_summary"]["latency_cliff"]["status"] == "clear"


def test_latency_cliff_respects_cfg_latency_only_after_input_tokens():
    # Same latencies, but input tokens just below the raised gate — should
    # not fire because the gate is not satisfied.
    rows = [_benchmark_row()] + [
        _stress_row(step=s, latency_ms=4000, input_tokens=1800) for s in range(3)
    ]
    cfg = StressFailureConfig(
        max_latency_ms=2500, latency_only_after_input_tokens=2000, max_rcs=0.30,
    )
    s = summarize_unified_run(records=rows, failure=cfg)
    assert s["models"][0]["trigger_summary"]["latency_cliff"]["status"] == "clear"


def test_repetition_loop_respects_cfg_max_rcs():
    # Two consecutive RCS=0.35 stress steps. Fires at legacy 0.30 hardcoded
    # threshold; must clear when cfg raises threshold to 0.50.
    rows = [_benchmark_row()] + [
        _stress_row(step=s, latency_ms=10, input_tokens=100, rcs=0.35)
        for s in range(3)
    ]
    assert summarize_unified_run(records=rows)["models"][0][
        "trigger_summary"]["repetition_loop"]["status"] == "fired"
    cfg = StressFailureConfig(max_rcs=0.50)
    assert summarize_unified_run(records=rows, failure=cfg)["models"][0][
        "trigger_summary"]["repetition_loop"]["status"] == "clear"


def test_trigger_threshold_strings_report_actual_cfg_values():
    # The threshold-description strings in trigger_summary should reflect
    # the cfg values, not the legacy hardcoded ones — auditor-visible
    # provenance.
    cfg = StressFailureConfig(
        max_latency_ms=8000, latency_only_after_input_tokens=2000,
        max_rcs=0.45, max_rcs_window_mean=0.30, max_lorr_mean=0.25,
    )
    rows = [_benchmark_row()] + [
        _stress_row(step=s, latency_ms=10, input_tokens=100) for s in range(3)
    ]
    s = summarize_unified_run(records=rows, failure=cfg)
    triggers = s["models"][0]["trigger_summary"]
    assert "8000" in triggers["latency_cliff"]["threshold"]
    assert "2000" in triggers["latency_cliff"]["threshold"]
    assert "0.45" in triggers["repetition_loop"]["threshold"]
    assert "0.3" in triggers["repetition_loop"]["threshold"]  # 0.30 mean
    assert "0.25" in triggers["near_cap_pressure"]["threshold"]


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
