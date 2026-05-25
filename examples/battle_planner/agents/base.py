from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from battle_planner.config import config
from battle_planner.data.models import LLMTrace
from battle_planner.runtime.middleware import (
    AgentMiddleware,
    AgentRunContext,
    InputContextMiddleware,
    TraceMetadataMiddleware,
)
from battle_planner.runtime.model_provider import ModelProvider, ModelRequest, build_model_provider
from battle_planner.runtime.trace import build_trace

from forge.core.lib.agent import TaskAgent

TOutput = TypeVar("TOutput")


@dataclass
class AgentInputs:
    data: dict[str, Any]
    model: str | None = None
    tools: list[dict[str, Any]] = field(default_factory=list)
    memory: dict[str, Any] = field(default_factory=dict)
    skills: list[str] = field(default_factory=list)


@dataclass
class AgentRunResult(Generic[TOutput]):
    output: TOutput
    trace: LLMTrace


class BasePlanningAgent(TaskAgent, ABC, Generic[TOutput]):
    name: str = "base_planning_agent"
    max_tokens: int = config.model.max_tokens

    def __init__(
        self,
        *,
        model_provider: ModelProvider | None = None,
        middleware: list[AgentMiddleware] | None = None,
    ):
        self.model_provider = model_provider or build_model_provider()
        self.middleware = middleware or [
            InputContextMiddleware(),
            TraceMetadataMiddleware(),
        ]

    def run(
        self,
        inputs: AgentInputs,
    ) -> AgentRunResult[TOutput]:
        context = AgentRunContext(
            agent_name=self.name,
            inputs=inputs.data,
            tools=inputs.tools,
            memory=inputs.memory,
            skills=inputs.skills,
            messages=self.build_messages(inputs),
        )
        for middleware in self.middleware:
            middleware.before_model(context)

        model_result = self.model_provider.complete(
            ModelRequest(messages=context.messages, max_tokens=self.max_tokens, model=inputs.model)
        )
        for middleware in self.middleware:
            middleware.after_model(context, model_result.content, model_result.error)

        output, fallback_used, error = self._parse_result(
            raw_output=model_result.content,
            model_error=model_result.error,
            inputs=inputs,
        )
        for middleware in self.middleware:
            middleware.after_parse(context, output, fallback_used)

        trace = build_trace(
            node_name=self.name,
            input_messages=context.messages,
            raw_output=model_result.content,
            parsed_output=self.trace_output(output),
            fallback_used=fallback_used,
            error=error,
        )
        return AgentRunResult(output=output, trace=trace)

    @abstractmethod
    def build_messages(self, inputs: AgentInputs) -> list[dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    def _parse_result(
        self,
        *,
        raw_output: str,
        model_error: str | None,
        inputs: AgentInputs,
    ) -> tuple[TOutput, bool, str | None]:
        raise NotImplementedError

    def trace_output(self, output: TOutput) -> Any:
        return output
