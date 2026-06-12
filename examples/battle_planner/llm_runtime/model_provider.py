from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from battle_planner.conf import LLMMode, Settings, settings
from openai import OpenAI
from pydantic import BaseModel, Field


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


class ModelProfile(BaseModel):
    """模型服务 profile，由 conf.Settings 解析。"""

    name: str = Field(description="模型配置名称。")
    provider: str = Field(description="模型服务类型。")
    api_url: str = Field(default="", description="兼容 OpenAI 接口的 API Base URL。")
    api_key: str = Field(default="", description="兼容 OpenAI 接口的 API Key。")
    model_name: str = Field(default="", description="实际请求模型服务时使用的模型名称。")
    reasoning_effort: str = Field(default="", description="可选的推理强度配置。")
    thinking_type: str = Field(default="", description="可选的 thinking.type 配置。")


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


def build_model_provider(settings_obj: Settings | None = None) -> ModelProvider:
    active_settings = settings_obj or settings
    if active_settings.LLM_MODE == LLMMode.OFFLINE:
        raise ValueError("LLM_MODE=offline uses run_output_seed and must not build a model provider")

    profile = _load_model_profile(active_settings)
    provider = profile.provider

    if provider in {"openai", "by", "deepseek"}:
        return OpenAICompatibleModelProvider(
            name=profile.name,
            base_url=profile.api_url,
            api_key=profile.api_key,
            model=profile.model_name,
            timeout=active_settings.LLM_TIMEOUT_SECONDS,
            reasoning_effort=profile.reasoning_effort,
            thinking_type=profile.thinking_type,
        )
    raise ValueError(f"Unsupported MODEL provider `{provider}` for profile `{profile.name}`")


def _load_model_profile(settings_obj: Settings) -> ModelProfile:
    selected = settings_obj.MODEL
    if selected not in settings_obj.model_profile_names:
        raise ValueError(f"MODEL profile `{selected}` is not configured")
    prefix = f"MODEL_{selected.upper().replace('-', '_')}"
    return ModelProfile(
        name=selected,
        provider=str(getattr(settings_obj, f"{prefix}_PROVIDER", "")),
        api_url=str(getattr(settings_obj, f"{prefix}_API_URL", "")),
        api_key=str(getattr(settings_obj, f"{prefix}_API_KEY", "dummy")),
        model_name=str(getattr(settings_obj, f"{prefix}_MODEL_NAME", "")),
        reasoning_effort=str(getattr(settings_obj, f"{prefix}_REASONING_EFFORT", "")),
        thinking_type=str(getattr(settings_obj, f"{prefix}_THINKING_TYPE", "")),
    )
