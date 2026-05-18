from __future__ import annotations

import json
import re
from typing import Any

from battle_planner.data.demo_models import FakeTickAgentSpec, PlannedAgentParams
from battle_planner.planning.base import AgentInputs, AgentRunResult, BasePlanningAgent
from battle_planner.runtime.fallback import fallback_agent_params


def _extract_json_array(text: str) -> list[dict[str, Any]] | None:
    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list):
        return None
    return data


class AgentParameterPlanningAgent(BasePlanningAgent[list[PlannedAgentParams]]):
    name = "agent_parameter_planning"

    def build_messages(self, inputs: AgentInputs) -> list[dict[str, str]]:
        specs_payload = [spec.model_dump() for spec in inputs.data["agent_specs"]]
        return [
            {
                "role": "system",
                "content": (
                    "你是智能体参数规划助手。请只输出 JSON 数组，数组元素包含 "
                    "agent_name、params、rationale。首版假设对手不会主动变化。不要展示思考过程。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "根据想定理解、作战方案和 fake agent schema，生成每个 agent 的参数。\n\n"
                    f"想定理解：\n{inputs.data['scenario_understanding_md']}\n\n"
                    f"作战方案：\n{inputs.data['battle_plan_md']}\n\n"
                    f"agent schema JSON：\n{json.dumps(specs_payload, ensure_ascii=False)}"
                ),
            },
        ]

    def parse_or_fallback(
        self,
        *,
        raw_output: str,
        model_error: str | None,
        inputs: AgentInputs,
    ) -> tuple[list[PlannedAgentParams], bool, str | None]:
        parsed: list[PlannedAgentParams] | None = None
        error = model_error
        if raw_output and model_error is None:
            raw_items = _extract_json_array(raw_output)
            if raw_items is not None:
                try:
                    parsed = [PlannedAgentParams.model_validate(item) for item in raw_items]
                except Exception as exc:
                    error = str(exc)
            else:
                error = "model output does not contain a JSON array"

        if parsed is None:
            return fallback_agent_params(inputs.data["agent_specs"]), True, error
        return parsed, False, None

    def trace_output(self, output: list[PlannedAgentParams]) -> Any:
        return [item.model_dump() for item in output]


def plan_agent_params(
    *,
    scenario_understanding_md: str,
    battle_plan_md: str,
    agent_specs: list[FakeTickAgentSpec],
) -> tuple[list[PlannedAgentParams], object]:
    result: AgentRunResult[list[PlannedAgentParams]] = AgentParameterPlanningAgent().run(
        AgentInputs(
            data={
                "scenario_understanding_md": scenario_understanding_md,
                "battle_plan_md": battle_plan_md,
                "agent_specs": agent_specs,
            },
            tools=[
                {
                    "name": "query_attack_candidates",
                    "description": "查询固定目标打击候选单位；首版作为上下文说明注入。",
                }
            ],
            skills=["读取 fake agent schema 并输出可执行参数 JSON"],
        )
    )
    return result.output, result.trace
