from __future__ import annotations

import time
from typing import Any

from lte.backends.api_common import post_json, require_env
from lte.backends.base import Backend, GenerationResult


class AnthropicBackend(Backend):
    name = "anthropic"

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
        del model_name
        del seed
        api_key = require_env("ANTHROPIC_API_KEY")
        payload: dict[str, Any] = {
            "model": model_path,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt_text}],
        }
        # Newer Anthropic models reject requests that specify both temperature and top_p.
        # Keep temperature as the canonical sampling control for this backend.
        if system_text:
            payload["system"] = system_text

        start = time.time()
        data = post_json(
            url="https://api.anthropic.com/v1/messages",
            payload=payload,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )
        latency_ms = int((time.time() - start) * 1000)

        blocks = data.get("content")
        if not isinstance(blocks, list) or not blocks:
            raise RuntimeError(f"Anthropic response missing content blocks: {data}")
        texts = [block.get("text", "") for block in blocks if isinstance(block, dict) and block.get("type") == "text"]
        output_text = "".join(texts).strip()
        if not output_text:
            raise RuntimeError(f"Anthropic response missing text content: {data}")

        usage = data.get("usage") or {}
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
            raise RuntimeError(f"Anthropic response missing usage tokens: {data}")

        stop_reason = data.get("stop_reason")
        if stop_reason is not None and not isinstance(stop_reason, str):
            stop_reason = str(stop_reason)

        return GenerationResult(
            output_text=output_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            token_count_method="anthropic-usage",
            stop_reason=stop_reason,
            latency_ms=latency_ms,
        )
