from lte.contracts import evaluate_contract


def test_checklist_verbs_accept_common_imperatives():
    evaluation = evaluate_contract(
        contract={
            "output_mode": "bullet_list",
            "checks": [
                "exactly 5 bullets",
                "each bullet starts with a verb",
                "6 words or fewer per bullet",
            ],
        },
        output_text=(
            "1. Install model locally.\n"
            "2. Prepare dataset for local use.\n"
            "3. Run model on local dataset.\n"
            "4. Analyze local model results.\n"
            "5. Compare with known benchmarks."
        ),
    )
    assert evaluation.passed


def test_fenced_yaml_is_treated_as_repairable_and_normalized():
    evaluation = evaluate_contract(
        contract={
            "output_mode": "yaml",
            "required_keys": ["status", "action", "reason"],
            "checks": ["action should imply escalate or abort"],
        },
        output_text=(
            "```yaml\n"
            "status: error\n"
            "action: human_review\n"
            "reason: Latency exceeded threshold.\n"
            "```"
        ),
    )
    assert evaluation.passed
    assert evaluation.outer_fences_stripped is True
    assert evaluation.failure_class == "recoverable"


def test_opening_fence_only_two_line_output_still_normalizes():
    evaluation = evaluate_contract(
        contract={
            "output_mode": "two_lines",
            "checks": ["exactly 2 lines", "line prefixes retry: and repair:"],
        },
        output_text=(
            "```\n"
            "retry: Attempt schema sync with updated schema file.\n"
            "repair: Re-run data migration scripts to ensure data conforms."
        ),
    )
    assert evaluation.passed
    assert evaluation.outer_fences_stripped is True


def test_unrecoverable_failure_class_is_reported():
    evaluation = evaluate_contract(
        contract={
            "output_mode": "json_object",
            "failure_class": "unrecoverable",
            "required_keys": ["run_id"],
        },
        output_text='{"wrong_key": "x"}',
    )
    assert evaluation.passed is False
    assert evaluation.failure_class == "unrecoverable"
    assert evaluation.recoverable_failure is False
