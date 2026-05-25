from __future__ import annotations

import json
import re
from typing import Any

from battle_planner.agents.base import AgentInputs, AgentRunResult, BasePlanningAgent
from battle_planner.runtime.model_provider import ModelProvider

from forge.core.specs import TickAgentParams, TickAgentSpec


def _looks_like_agent_param_items(value: Any, *, require_shape: bool) -> bool:
    if not isinstance(value, list):
        return False
    if not all(isinstance(item, dict) for item in value):
        return False
    if not require_shape or not value:
        return True
    return all("agent_name" in item and "side" in item for item in value)


def _coerce_agent_param_items(value: Any) -> list[dict[str, Any]] | None:
    if isinstance(value, dict):
        for key in ("agents", "planned_agents", "agent_params", "agent_configs"):
            items = value.get(key)
            if _looks_like_agent_param_items(items, require_shape=False):
                return items
        return None
    if _looks_like_agent_param_items(value, require_shape=True):
        return value
    return None


def _extract_agent_param_items(text: str) -> list[dict[str, Any]] | None:
    decoder = json.JSONDecoder()
    for match in re.finditer(r"[\[{]", text):
        try:
            data, _ = decoder.raw_decode(text[match.start() :])
        except json.JSONDecodeError:
            continue
        items = _coerce_agent_param_items(data)
        if items is not None:
            return items
    return None


class AgentParameterPlanningAgent(BasePlanningAgent[list[TickAgentParams]]):
    name = "agent_parameter_planning"

    def build_messages(self, inputs: AgentInputs) -> list[dict[str, str]]:
        specs_payload = [spec.model_dump() for spec in inputs.data["agent_specs"]]
        return [
            {
                "role": "system",
                "content": (
                    "你是智能体参数规划助手。请只输出 JSON 对象，不要输出 Markdown。"
                    "你的输出第一个字符必须是 {，最后一个字符必须是 }，不要输出任何解释、标题或自然语言。"
                    "JSON 对象必须包含 agents 数组，数组元素包含 "
                    "agent_instance_id、agent_name、side、params。"
                    "agent_name 是 tick agent 类型名称，agent_instance_id 是本次计划中的唯一实例名称。"
                    "side 是本次运行中该智能体实例所属阵营，例如 blue 或 red。"
                    "params 只包含 tick agent 的任务参数，不要把 side 放进 params。"
                    "unit_ids 和 target_ids 是大小写与符号敏感的运行时主键。"
                    "如果输入中给出具体 unit_ids、target_ids，必须逐字符原样复制，不要发明、翻译、改写或替换分隔符。"
                    "首版假设对手不会主动变化。不要展示思考过程。"
                    '输出示例：{"agents":[{"agent_instance_id":"demo_001","agent_name":"air_to_sea_strike_agent",'
                    '"side":"blue","params":{"start_time":120,"end_time":180,"unit_ids":["blue_unit_1"],'
                    '"target_ids":["red_target_1"]}}]}'
                ),
            },
            {
                "role": "user",
                "content": (
                    "根据想定理解、作战方案和 tick agent schema，生成每个 agent 的参数。\n\n"
                    f"想定理解：\n{inputs.data['scenario_understanding_md']}\n\n"
                    f"作战方案：\n{inputs.data['battle_plan_md']}\n\n"
                    f"agent schema JSON：\n{json.dumps(specs_payload, ensure_ascii=False)}"
                ),
            },
        ]

    def _parse_result(
        self,
        *,
        raw_output: str,
        model_error: str | None,
        inputs: AgentInputs,
    ) -> tuple[list[TickAgentParams], bool, str | None]:
        parsed: list[TickAgentParams] | None = None
        error = model_error
        if raw_output and model_error is None:
            raw_items = _extract_agent_param_items(raw_output)
            if raw_items is not None:
                try:
                    parsed = [TickAgentParams.model_validate(item) for item in raw_items]
                except Exception as exc:
                    error = str(exc)
            else:
                error = "model output does not contain agents JSON"

        if parsed is None:
            return [], True, error
        return parsed, False, None

    def trace_output(self, output: list[TickAgentParams]) -> Any:
        return [item.model_dump() for item in output]


def plan_agent_params(
    *,
    scenario_understanding_md: str,
    battle_plan_md: str,
    agent_specs: list[TickAgentSpec],
    model: str | None = None,
    model_provider: ModelProvider | None = None,
) -> tuple[list[TickAgentParams], object]:
    result: AgentRunResult[list[TickAgentParams]] = AgentParameterPlanningAgent(
        model_provider=model_provider
    ).run(
        AgentInputs(
            data={
                "scenario_understanding_md": scenario_understanding_md,
                "battle_plan_md": battle_plan_md,
                "agent_specs": agent_specs,
            },
            model=model,
            tools=[
                {
                    "name": "query_attack_candidates",
                    "description": "查询固定目标打击候选单位；首版作为上下文说明注入。",
                }
            ],
            skills=["读取 tick agent schema 并输出可执行参数 JSON"],
        )
    )
    return result.output, result.trace
