from __future__ import annotations


def test_model_provider_rejects_requested_model_mismatch() -> None:
    from battle_planner.llm_runtime.model_provider import ModelRequest, OpenAICompatibleModelProvider

    provider = OpenAICompatibleModelProvider(
        name="local_test",
        base_url="http://localhost:8000/v1",
        api_key="dummy",
        model="configured-model",
    )

    response = provider.complete(ModelRequest(messages=[], model="other-model"))

    assert "does not match configured model" in response.error


def test_model_provider_passes_reasoning_and_thinking_options(monkeypatch) -> None:
    from battle_planner.llm_runtime import model_provider
    from battle_planner.llm_runtime.model_provider import ModelRequest, OpenAICompatibleModelProvider

    captured: dict = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            message = type(
                "Message",
                (),
                {
                    "content": '{"agents":[]}',
                    "reasoning_content": "hidden reasoning",
                },
            )()
            choice = type("Choice", (), {"message": message})()
            return type("Response", (), {"choices": [choice]})()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setattr(model_provider, "OpenAI", FakeOpenAI)
    provider = OpenAICompatibleModelProvider(
        name="deepseek_v4_pro",
        base_url="https://api.deepseek.com",
        api_key="dummy",
        model="deepseek-v4-pro",
        reasoning_effort="high",
        thinking_type="enabled",
    )

    provider.complete(ModelRequest(messages=[{"role": "user", "content": "hello"}]))

    assert captured["reasoning_effort"] == "high"
    assert captured["extra_body"] == {"thinking": {"type": "enabled"}}
