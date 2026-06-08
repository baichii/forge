from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from battle_planner.config import LLMMode, config
from openai import OpenAI


@dataclass
class ModelRequest:
    messages: list[dict[str, str]]
    max_tokens: int = 2048
    model: str | None = None


@dataclass
class ModelResponse:
    content: str
    model: str = ""
    provider: str = ""
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.content)


class ModelProvider(ABC):
    name: str

    @abstractmethod
    def complete(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError


class OpenAICompatibleModelProvider(ModelProvider):
    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 8.0,
        reasoning_effort: str = "",
        thinking_type: str = "",
    ):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key or "dummy"
        self.model = model
        self.timeout = timeout
        self.reasoning_effort = reasoning_effort
        self.thinking_type = thinking_type

    def complete(self, request: ModelRequest) -> ModelResponse:
        if not self.model or not self.base_url:
            return ModelResponse(
                content="",
                model=self.model,
                provider=self.name,
                error=f"{self.name} model or base_url is not configured",
            )
        if request.model is not None and request.model != self.model:
            return ModelResponse(
                content="",
                model=self.model,
                provider=self.name,
                error=(
                    f"requested model `{request.model}` does not match configured "
                    f"model `{self.model}` for profile `{self.name}`"
                ),
            )

        try:
            client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)
            request_kwargs = {
                "model": self.model,
                "messages": request.messages,
                "max_tokens": request.max_tokens,
            }
            if self.reasoning_effort:
                request_kwargs["reasoning_effort"] = self.reasoning_effort
            if self.thinking_type:
                request_kwargs["extra_body"] = {"thinking": {"type": self.thinking_type}}
            response = client.chat.completions.create(**request_kwargs)
            message = response.choices[0].message
            content = message.content or ""
            return ModelResponse(content=content, model=self.model, provider=self.name)
        except Exception as exc:
            return ModelResponse(
                content="",
                model=self.model,
                provider=self.name,
                error=str(exc),
            )


class OfflineModelProvider(ModelProvider):
    name = "offline"
    model = "offline"

    def complete(self, request: ModelRequest) -> ModelResponse:
        if request.model is not None and request.model != self.model:
            return ModelResponse(
                content="",
                model=self.model,
                provider=self.name,
                error=(
                    f"requested model `{request.model}` does not match configured "
                    f"model `{self.model}` for profile `{self.name}`"
                ),
            )
        return ModelResponse(
            content="", model=self.model, provider=self.name, error="offline model provider"
        )


def build_model_provider() -> ModelProvider:
    if config.runtime.llm_mode == LLMMode.OFFLINE:
        return OfflineModelProvider()
    if config.runtime.llm_mode == LLMMode.REPLAY:
        raise ValueError("LLM_MODE=replay is not implemented by model provider yet")

    model_config = config.model
    profile = model_config.active_profile
    provider = profile.provider

    if provider in {"openai", "by", "deepseek"}:
        return OpenAICompatibleModelProvider(
            name=profile.name,
            base_url=profile.api_url,
            api_key=profile.api_key,
            model=profile.model_name,
            timeout=model_config.timeout_seconds,
            reasoning_effort=profile.reasoning_effort,
            thinking_type=profile.thinking_type,
        )
    raise ValueError(f"Unsupported MODEL provider `{provider}` for profile `{profile.name}`")
