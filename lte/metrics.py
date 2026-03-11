from __future__ import annotations

import re


def expansion_ratio(*, input_tokens: int, output_tokens: int) -> float:
    return output_tokens / max(1, input_tokens)


def length_overrun_rate(*, output_tokens: int, max_tokens: int) -> int:
    return 1 if output_tokens >= int(0.95 * max_tokens) else 0


def verbosity_drift(*, concise_len: int, detailed_len: int) -> float:
    return (detailed_len - concise_len) / max(1, concise_len)


def runaway_continuation_score(output_text: str) -> float:
    """
    4-gram repetition fraction over output text.
    Returns 0..1, where higher means more repetitive.
    """
    tokens = [t.lower() for t in re.findall(r"[A-Za-z0-9_]+", output_text)]
    n = 4
    if len(tokens) < n:
        return 0.0
    ngrams = [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]
    if not ngrams:
        return 0.0
    unique = len(set(ngrams))
    return 1.0 - (unique / len(ngrams))

