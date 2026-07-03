from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal

TokenCountMethod = Literal["mlx-native", "openai-usage", "anthropic-usage", "approx"]


@dataclass(frozen=True)
class GenerationRecord:
    run_id: str
    timestamp: str

    model_name: str
    backend: str
    model_revision: str | None

    suite_name: str
    prompt_id: str
    prompt_text: str
    system_text: str | None

    max_tokens: int
    temperature: float
    top_p: float
    seed: int | None

    output_text: str

    input_tokens: int
    output_tokens: int
    token_count_method: TokenCountMethod
    stop_reason: str | None
    latency_ms: int

    @staticmethod
    def now_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
