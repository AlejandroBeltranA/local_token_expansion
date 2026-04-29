import pytest

from lte.token_count import count_tokens_approx, count_tokens_native


class DummyTokenizer:
    def encode(self, text: str):
        return text.split()


def test_count_tokens_approx():
    assert count_tokens_approx("hello world") >= 2


def test_count_tokens_native_encode():
    tc = count_tokens_native(DummyTokenizer(), "hello world")
    assert tc.tokens == 2
    assert tc.method == "mlx-native"


def test_count_tokens_native_raises_without_native_support():
    with pytest.raises(RuntimeError, match="Native token counting is unavailable"):
        count_tokens_native(object(), "hello world")
