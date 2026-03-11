from lte.metrics import (
    expansion_ratio,
    length_overrun_rate,
    runaway_continuation_score,
    verbosity_drift,
)


def test_expansion_ratio():
    assert expansion_ratio(input_tokens=10, output_tokens=20) == 2.0
    assert expansion_ratio(input_tokens=0, output_tokens=5) == 5.0


def test_length_overrun_rate():
    assert length_overrun_rate(output_tokens=95, max_tokens=100) == 1
    assert length_overrun_rate(output_tokens=94, max_tokens=100) == 0


def test_verbosity_drift():
    assert verbosity_drift(concise_len=10, detailed_len=15) == 0.5
    assert verbosity_drift(concise_len=0, detailed_len=10) == 10.0


def test_runaway_continuation_score_simple():
    assert runaway_continuation_score("hello world") == 0.0


def test_runaway_continuation_score_repeats():
    # Repeating 4-grams should yield a high score.
    txt = "a b c d a b c d a b c d a b c d"
    assert runaway_continuation_score(txt) > 0.5

