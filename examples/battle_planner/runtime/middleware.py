from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class AgentRunContext:
    agent_name: str
    inputs: dict[str, Any]
    messages: list[dict[str, str]] = field(default_factory=list)
    tools: list[dict[str, Any]] = field(default_factory=list)
    memory: dict[str, Any] = field(default_factory=dict)
    skills: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentMiddleware(Protocol):
    name: str

    def before_model(self, context: AgentRunContext) -> None: ...

    def after_model(self, context: AgentRunContext, raw_output: str, error: str | None) -> None: ...

    def after_parse(self, context: AgentRunContext, parsed_output: Any, fallback_used: bool) -> None: ...


class BaseAgentMiddleware:
    name = "base"

    def before_model(self, context: AgentRunContext) -> None:
        pass

    def after_model(self, context: AgentRunContext, raw_output: str, error: str | None) -> None:
        pass

    def after_parse(self, context: AgentRunContext, parsed_output: Any, fallback_used: bool) -> None:
        pass


class InputContextMiddleware(BaseAgentMiddleware):
    """Adds tool/memory/skill information to the prompt when available."""

    name = "input_context"

    def before_model(self, context: AgentRunContext) -> None:
        context_parts: list[str] = []
        if context.tools:
            context_parts.append(f"可用工具：{context.tools}")
        if context.skills:
            context_parts.append(f"可用技能：{context.skills}")
        if context.memory:
            context_parts.append(f"记忆摘要：{context.memory}")
        if not context_parts:
            return

        content = "\n".join(context_parts)
        if context.messages and context.messages[0].get("role") == "system":
            context.messages[0]["content"] = f"{context.messages[0]['content']}\n\n{content}"
            return

        context.messages.insert(
            0,
            {
                "role": "system",
                "content": content,
            },
        )


class TraceMetadataMiddleware(BaseAgentMiddleware):
    """Stores middleware hook metadata for later trace expansion."""

    name = "trace_metadata"

    def before_model(self, context: AgentRunContext) -> None:
        context.metadata.setdefault("middleware", []).append(f"{self.name}.before_model")

    def after_model(self, context: AgentRunContext, raw_output: str, error: str | None) -> None:
        context.metadata.setdefault("middleware", []).append(f"{self.name}.after_model")
        context.metadata["raw_output_chars"] = len(raw_output)
        context.metadata["model_error"] = error

    def after_parse(self, context: AgentRunContext, parsed_output: Any, fallback_used: bool) -> None:
        context.metadata.setdefault("middleware", []).append(f"{self.name}.after_parse")
        context.metadata["fallback_used"] = fallback_used
