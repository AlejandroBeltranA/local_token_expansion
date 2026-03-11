from __future__ import annotations

import time
from typing import Any

from lte.backends.base import Backend, GenerationResult
from lte.token_count import count_tokens_native_or_approx


def _safe_import_mlx() -> tuple[Any, Any]:
    try:
        import mlx.core as mx  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "MLX is not available. On Apple Silicon macOS, install with `pip install -e .` "
            "(mlx-lm is installed automatically via platform marker)."
        ) from exc
    try:
        from mlx_lm import generate, load  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "mlx-lm is not available. Install it on Apple Silicon macOS (see README)."
        ) from exc
    return (mx, (generate, load))


def _strip_unsupported_kwargs(fn: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    # Older mlx-lm versions may not support some kwargs; best-effort filter.
    try:
        import inspect

        sig = inspect.signature(fn)
    except Exception:
        return kwargs
    supported = set(sig.parameters.keys())
    return {k: v for k, v in kwargs.items() if k in supported}


def _format_prompt(tokenizer: Any, prompt_text: str, system_text: str | None) -> str:
    if system_text is None:
        return prompt_text
    if hasattr(tokenizer, "apply_chat_template"):
        messages = [
            {"role": "system", "content": system_text},
            {"role": "user", "content": prompt_text},
        ]
        try:
            return tokenizer.apply_chat_template(  # type: ignore[no-any-return]
                messages, tokenize=False, add_generation_prompt=True
            )
        except Exception:
            pass
    return f"System:\n{system_text}\n\nUser:\n{prompt_text}\n\nAssistant:\n"


def _try_clear_metal_cache(mx: Any) -> None:
    clear_cache = getattr(mx, "clear_cache", None)
    if callable(clear_cache):
        try:
            clear_cache()
            return
        except Exception:
            pass

    # Fallback for older MLX versions.
    metal = getattr(mx, "metal", None)
    if metal is None:
        return
    clear_cache = getattr(metal, "clear_cache", None)
    if callable(clear_cache):
        try:
            clear_cache()
        except Exception:
            pass


class MLXBackend(Backend):
    name = "mlx"

    def __init__(self) -> None:
        self._current_model_path: str | None = None
        self._model: Any | None = None
        self._tokenizer: Any | None = None

    def reset(self) -> None:
        mx, _ = _safe_import_mlx()
        self._current_model_path = None
        self._model = None
        self._tokenizer = None
        _try_clear_metal_cache(mx)

    def _load_for_path(self, model_path: str) -> tuple[Any, Any]:
        if self._current_model_path == model_path and self._model is not None and self._tokenizer is not None:
            return self._model, self._tokenizer

        # Switching models: drop references and clear cache to reduce Metal OOM risk.
        self.reset()
        _mx, (_generate, load) = _safe_import_mlx()
        model, tokenizer = load(model_path)
        self._current_model_path = model_path
        self._model = model
        self._tokenizer = tokenizer
        return model, tokenizer

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
        mx, (generate, _load) = _safe_import_mlx()
        model, tokenizer = self._load_for_path(model_path)

        prompt = _format_prompt(tokenizer, prompt_text, system_text)
        in_count = count_tokens_native_or_approx(tokenizer, prompt)

        if seed is not None:
            try:
                mx.random.seed(seed)
            except Exception:
                # MLX seed behavior is not fully stable across versions/models.
                pass

        start = time.time()
        kwargs: dict[str, Any] = {
            "model": model,
            "tokenizer": tokenizer,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temp": temperature,
            "top_p": top_p,
            "verbose": False,
        }
        kwargs = _strip_unsupported_kwargs(generate, kwargs)
        output_text = generate(**kwargs)
        latency_ms = int((time.time() - start) * 1000)

        out_count = count_tokens_native_or_approx(tokenizer, output_text)
        method = "mlx-native" if (in_count.method == "mlx-native" and out_count.method == "mlx-native") else "approx"

        stop_reason = "length" if out_count.tokens >= int(0.95 * max_tokens) else "eos/other"
        return GenerationResult(
            output_text=output_text,
            input_tokens=in_count.tokens,
            output_tokens=out_count.tokens,
            token_count_method=method,
            stop_reason=stop_reason,
            latency_ms=latency_ms,
        )
