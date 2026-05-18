from __future__ import annotations

from typing import Any

from battle_planner.data.demo_models import FakeTickAgentSpec, PlannedAgentParams


def fallback_markdown(title: str, body: str) -> str:
    return f"# {title}\n\n{body}\n"


def fallback_agent_params(agent_specs: list[FakeTickAgentSpec]) -> list[PlannedAgentParams]:
    planned: list[PlannedAgentParams] = []
    for spec in agent_specs:
        params: dict[str, Any] = {param.name: param.default for param in spec.params}
        planned.append(
            PlannedAgentParams(
                agent_name=spec.name,
                params=params,
                rationale="LLM 不可用或输出无法解析，使用 fake agent 默认参数。",
            )
        )
    return planned
