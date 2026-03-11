from lte.config import StressConfig
from lte.stress import _build_context


def test_build_context_avoids_step_scaffold():
    stress = StressConfig(enabled=True)
    ctx = _build_context(base_prompt="Do X", history=["out1", "out2"], stress=stress)
    assert "Step 0 output" not in ctx


def test_build_context_delimits_reference_and_ends_with_constraints():
    stress = StressConfig(enabled=True)
    ctx = _build_context(base_prompt="Do X", history=["alpha"], stress=stress)
    assert "BEGIN REFERENCE" in ctx
    assert "END REFERENCE" in ctx
    # Constraints should be after the reference block.
    assert ctx.rfind("CONSTRAINTS:") > ctx.rfind("END REFERENCE")


def test_build_context_sliding_window():
    stress = StressConfig(enabled=True, context_growth="sliding", sliding_window_steps=1)
    ctx = _build_context(base_prompt="Do X", history=["one", "two"], stress=stress)
    assert "one" not in ctx
    assert "two" in ctx

