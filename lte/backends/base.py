from __future__ import annotations

from dataclasses import dataclass

from lte.schema import TokenCountMethod


@dataclass(frozen=True)
class GenerationResult:
    output_text: str
    input_tokens: int
    output_tokens: int
    token_count_method: TokenCountMethod
    stop_reason: str | None
    latency_ms: int


class Backend:
    name: str

    def reset(self) -> None:
        """
        Release any cached model state if the backend keeps it.
        Backends may no-op.
        """

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
        raise NotImplementedError
