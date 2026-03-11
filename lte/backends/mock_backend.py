from __future__ import annotations

import hashlib
import random
import time

from lte.backends.base import Backend, GenerationResult
from lte.token_count import count_tokens_approx


class MockBackend(Backend):
    name = "mock"

    def reset(self) -> None:
        return

    def generate(
        self,
        *,
        model_path: str,
        model_name: str,
        prompt_text: str,
        system_text: str | None,
        max_tokens: int,
        temperature: float,
        top_p: float,
        seed: int | None,
    ) -> GenerationResult:
        start = time.time()

        h = hashlib.sha256()
        h.update(model_name.encode("utf-8"))
        h.update(b"\n")
        if seed is not None:
            h.update(str(seed).encode("utf-8"))
            h.update(b"\n")
        h.update((system_text or "").encode("utf-8"))
        h.update(b"\n")
        h.update(prompt_text.encode("utf-8"))
        rng = random.Random(int.from_bytes(h.digest()[:8], "big"))

        base = [
            "Checklist:",
            "- Install dependencies",
            "- Load suites",
            "- Run prompts",
            "- Write results",
            "- Generate report",
        ]
        # Introduce some controlled variability and repetition.
        extras = [
            "Note: token counts are approximate.",
            "Note: mock backend is deterministic.",
            "Note: use MLX on Apple Silicon for real runs.",
        ]
        rng.shuffle(extras)
        text = "\n".join(base + extras[: rng.randint(1, 3)])

        # Enforce rough max_tokens by truncating words until we're under budget.
        words = text.split()
        while len(words) > 0 and count_tokens_approx(" ".join(words)) > max_tokens:
            words = words[:-1]
        output_text = " ".join(words).strip()

        latency_ms = int((time.time() - start) * 1000)
        in_tok = count_tokens_approx(prompt_text) + count_tokens_approx(system_text or "")
        out_tok = count_tokens_approx(output_text)
        return GenerationResult(
            output_text=output_text,
            input_tokens=in_tok,
            output_tokens=out_tok,
            token_count_method="approx",
            stop_reason="mock",
            latency_ms=latency_ms,
        )
