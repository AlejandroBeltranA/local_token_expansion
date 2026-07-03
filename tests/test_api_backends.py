
from lte.backends.anthropic_backend import AnthropicBackend
from lte.backends.openai_backend import OpenAIBackend


def test_openai_backend_maps_usage_and_finish_reason(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_post_json(*, url, payload, headers, timeout_sec=120):
        assert url == "https://api.openai.com/v1/chat/completions"
        assert payload["model"] == "gpt-4o-mini"
        assert payload["max_completion_tokens"] == 64
        assert payload["seed"] == 7
        assert headers["Authorization"] == "Bearer test-key"
        return {
            "choices": [
                {
                    "message": {"content": "ok"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3},
        }

    monkeypatch.setattr("lte.backends.openai_backend.post_json", fake_post_json)

    result = OpenAIBackend().generate(
        model_path="gpt-4o-mini",
        model_name="GPT-4o mini",
        prompt_text="hello",
        system_text="be brief",
        max_tokens=64,
        temperature=0.2,
        top_p=0.95,
        seed=7,
    )

    assert result.output_text == "ok"
    assert result.input_tokens == 12
    assert result.output_tokens == 3
    assert result.token_count_method == "openai-usage"
    assert result.stop_reason == "stop"


def test_anthropic_backend_maps_usage_and_stop_reason(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def fake_post_json(*, url, payload, headers, timeout_sec=120):
        assert url == "https://api.anthropic.com/v1/messages"
        assert payload["model"] == "claude-3-5-haiku-latest"
        assert payload["max_tokens"] == 80
        assert payload["messages"][0]["content"] == "hello"
        assert headers["x-api-key"] == "test-key"
        return {
            "content": [{"type": "text", "text": "done"}],
            "usage": {"input_tokens": 20, "output_tokens": 4},
            "stop_reason": "end_turn",
        }

    monkeypatch.setattr("lte.backends.anthropic_backend.post_json", fake_post_json)

    result = AnthropicBackend().generate(
        model_path="claude-3-5-haiku-latest",
        model_name="Claude 3.5 Haiku",
        prompt_text="hello",
        system_text="be brief",
        max_tokens=80,
        temperature=0.2,
        top_p=0.95,
        seed=0,
    )

    assert result.output_text == "done"
    assert result.input_tokens == 20
    assert result.output_tokens == 4
    assert result.token_count_method == "anthropic-usage"
    assert result.stop_reason == "end_turn"


def test_openai_backend_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    backend = OpenAIBackend()
    try:
        backend.generate(
            model_path="gpt-4o-mini",
            model_name="GPT-4o mini",
            prompt_text="hello",
            system_text=None,
            max_tokens=32,
            temperature=0.2,
            top_p=0.95,
            seed=0,
        )
    except RuntimeError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected missing OPENAI_API_KEY to raise RuntimeError")
