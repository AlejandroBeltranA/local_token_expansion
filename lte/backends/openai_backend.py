from __future__ import annotations

import time
from typing import Any

from lte.backends.api_common import post_json, require_env
from lte.backends.base import Backend, GenerationResult


class OpenAIBackend(Backend):
    name = "openai"

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
        api_key = require_env("OPENAI_API_KEY")
        messages: list[dict[str, Any]] = []
        if system_text:
            messages.append({"role": "system", "content": system_text})
        messages.append({"role": "user", "content": prompt_text})
        payload: dict[str, Any] = {
            "model": model_path,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_completion_tokens": max_tokens,
        }
        if seed is not None:
            payload["seed"] = seed

        start = time.time()
        data = post_json(
            url="https://api.openai.com/v1/chat/completions",
            payload=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        latency_ms = int((time.time() - start) * 1000)

        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError(f"OpenAI response missing choices: {data}")
        choice = choices[0]
        message = choice.get("message") or {}
        output_text = message.get("content")
        if not isinstance(output_text, str):
            raise RuntimeError(f"OpenAI response missing text content: {data}")

        usage = data.get("usage") or {}
        input_tokens = usage.get("prompt_tokens")
        output_tokens = usage.get("completion_tokens")
        if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
            raise RuntimeError(f"OpenAI response missing usage tokens: {data}")

        stop_reason = choice.get("finish_reason")
        if stop_reason is not None and not isinstance(stop_reason, str):
            stop_reason = str(stop_reason)

        return GenerationResult(
            output_text=output_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            token_count_method="openai-usage",
            stop_reason=stop_reason,
            latency_ms=latency_ms,
        )
