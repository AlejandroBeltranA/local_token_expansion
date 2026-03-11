from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from lte.schema import TokenCountMethod


@dataclass(frozen=True)
class TokenCount:
    tokens: int
    method: TokenCountMethod


def count_tokens_approx(text: str) -> int:
    # Cheap fallback: count "word-ish" pieces.
    # This is intentionally simple and only used when native tokenization is unavailable.
    return len(re.findall(r"[A-Za-z0-9_]+|[^\\sA-Za-z0-9_]", text))


def count_tokens_native_or_approx(tokenizer: Any, text: str) -> TokenCount:
    """
    Best-effort native token counting. Supports common tokenizer APIs:
    - tokenizer.encode(text)
    - tokenizer(text).input_ids / ["input_ids"]
    Falls back to an approximate counter when unavailable.
    """
    try:
        if hasattr(tokenizer, "encode"):
            ids = tokenizer.encode(text)
            if isinstance(ids, (list, tuple)):
                return TokenCount(tokens=len(ids), method="mlx-native")
        out = tokenizer(text)
        if isinstance(out, dict) and "input_ids" in out and isinstance(out["input_ids"], (list, tuple)):
            return TokenCount(tokens=len(out["input_ids"]), method="mlx-native")
        if hasattr(out, "input_ids") and isinstance(out.input_ids, (list, tuple)):  # type: ignore[attr-defined]
            return TokenCount(tokens=len(out.input_ids), method="mlx-native")
    except Exception:
        pass
    return TokenCount(tokens=count_tokens_approx(text), method="approx")

