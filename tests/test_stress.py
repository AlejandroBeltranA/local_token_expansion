from lte.config import StressConfig, StressFailureConfig
from lte.stress import evaluate_step_failure


def test_evaluate_step_failure_latency():
    stress = StressConfig(enabled=True, failure=StressFailureConfig(max_latency_ms=10))
    f = evaluate_step_failure(
        output_text="ok",
        output_tokens=10,
        max_tokens=100,
        latency_ms=11,
        input_tokens=1,
        context_fraction=None,
        stress=stress,
    )
    assert f.is_failure
    assert "latency" in f.reasons


def test_evaluate_step_failure_lorr():
    stress = StressConfig(enabled=True, failure=StressFailureConfig(fail_on_lorr=True))
    # 95% of 100 => failure at >=95
    f = evaluate_step_failure(
        output_text="ok",
        output_tokens=95,
        max_tokens=100,
        latency_ms=0,
        input_tokens=1,
        context_fraction=None,
        stress=stress,
    )
    assert f.is_failure
    assert "lorr" in f.reasons


def test_evaluate_step_failure_latency_gated_by_input_tokens():
    stress = StressConfig(
        enabled=True,
        failure=StressFailureConfig(
            max_latency_ms=10,
            latency_only_after_input_tokens=100,
        ),
    )
    f = evaluate_step_failure(
        output_text="ok",
        output_tokens=10,
        max_tokens=100,
        latency_ms=11,
        input_tokens=50,
        context_fraction=None,
        stress=stress,
    )
    assert not f.is_failure

    f2 = evaluate_step_failure(
        output_text="ok",
        output_tokens=10,
        max_tokens=100,
        latency_ms=11,
        input_tokens=150,
        context_fraction=None,
        stress=stress,
    )
    assert f2.is_failure
    assert "latency" in f2.reasons


def test_evaluate_step_failure_latency_gated_by_context_fraction():
    stress = StressConfig(
        enabled=True,
        failure=StressFailureConfig(
            max_latency_ms=10,
            latency_only_after_context_fraction=0.5,
        ),
    )
    f = evaluate_step_failure(
        output_text="ok",
        output_tokens=10,
        max_tokens=100,
        latency_ms=11,
        input_tokens=1,
        context_fraction=0.49,
        stress=stress,
    )
    assert not f.is_failure

    f2 = evaluate_step_failure(
        output_text="ok",
        output_tokens=10,
        max_tokens=100,
        latency_ms=11,
        input_tokens=1,
        context_fraction=0.75,
        stress=stress,
    )
    assert f2.is_failure
    assert "latency" in f2.reasons
