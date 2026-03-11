from pathlib import Path

from lte.suites import load_suite


def test_load_suite_ok():
    suite = load_suite(Path("suites/core_conciseness.yaml"))
    assert suite.name == "core_conciseness"
    assert suite.experiment_family == "budget_guardrails"
    assert len(suite.cases) >= 2
    assert suite.cases[0].trigger_targets == ["over_expansion"]
    assert "checks" in suite.cases[0].contract
