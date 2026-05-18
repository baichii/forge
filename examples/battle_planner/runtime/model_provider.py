from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from battle_planner.config import config
from openai import OpenAI


@dataclass
class ModelRequest:
    messages: list[dict[str, str]]
    max_tokens: int = 1024


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
    ):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key or "dummy"
        self.model = model
        self.timeout = timeout

    def complete(self, request: ModelRequest) -> ModelResponse:
        if not self.model or not self.base_url:
            return ModelResponse(
                content="",
                model=self.model,
                provider=self.name,
                error=f"{self.name} model or base_url is not configured",
            )

        try:
            client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)
            response = client.chat.completions.create(
                model=self.model,
                messages=request.messages,
                max_tokens=request.max_tokens,
            )
            message = response.choices[0].message
            content = message.content or getattr(message, "reasoning", "") or ""
            lowered = content.lower()
            if "thinking process" in lowered or "step-by-step" in lowered:
                return ModelResponse(
                    content=content,
                    model=self.model,
                    provider=self.name,
                    error="model exposed reasoning text",
                )
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

    def complete(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(content="", provider=self.name, error="offline model provider")


def build_model_provider() -> ModelProvider:
    api = config.api
    provider = config.system.model_provider

    if provider == "offline":
        return OfflineModelProvider()
    if provider == "openai":
        return OpenAICompatibleModelProvider(
            name="openai",
            base_url=api.openai_api_url,
            api_key=api.openai_api_key,
            model=api.openai_model,
        )
    if provider == "local":
        return OpenAICompatibleModelProvider(
            name="local",
            base_url=api.local_openai_api_url,
            api_key=api.local_openai_api_key,
            model=api.local_openai_model,
        )

    if api.local_openai_api_url and api.local_openai_model:
        return OpenAICompatibleModelProvider(
            name="local",
            base_url=api.local_openai_api_url,
            api_key=api.local_openai_api_key,
            model=api.local_openai_model,
        )
    if api.openai_api_url and api.openai_model:
        return OpenAICompatibleModelProvider(
            name="openai",
            base_url=api.openai_api_url,
            api_key=api.openai_api_key,
            model=api.openai_model,
        )
    return OfflineModelProvider()
