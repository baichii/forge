from __future__ import annotations

from typing import Any

from battle_planner.agents.base import AgentInputs, AgentRunResult, BasePlanningAgent
from battle_planner.agents.context import render_knowledge_pack_md
from battle_planner.agents.history_context import render_history_for_planning
from battle_planner.data.models import PlannerKnowledgePack
from battle_planner.runtime.fallback import fallback_markdown


class BattlePlanGenerationAgent(BasePlanningAgent[str]):
    name = "battle_plan_generation"

    def build_messages(self, inputs: AgentInputs) -> list[dict[str, str]]:
        scenario_understanding_md = inputs.data["scenario_understanding_md"]
        history_context = render_history_for_planning(inputs.data.get("history") or [])
        knowledge_context = ""
        if inputs.data.get("knowledge_pack") is not None:
            knowledge_context = (
                f"\n\n规划知识包：\n{render_knowledge_pack_md(inputs.data['knowledge_pack'])}"
            )
        return [
            {
                "role": "system",
                "content": (
                    "你是作战方案规划助手。首版假设对手不会主动变化，只围绕目标达成生成粗粒度方案。"
                    "请围绕摧毁红方航母和武器消耗最小生成方案。请只输出最终 Markdown，不要展示思考过程。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "基于以下想定理解，模拟生成一个 Markdown 作战方案。"
                    "方案需要包含目标、阶段、使用的智能体能力、任务参数建议、武器消耗控制、关键假设。\n\n"
                    f"{scenario_understanding_md}"
                    f"{knowledge_context}"
                    f"{history_context}"
                ),
            },
        ]

    def _parse_result(
        self,
        *,
        raw_output: str,
        model_error: str | None,
        inputs: AgentInputs,
    ) -> tuple[str, bool, str | None]:
        if raw_output and model_error is None:
            return raw_output, False, None
        if inputs.data.get("knowledge_pack") is not None:
            return _fallback_battle_plan(inputs.data["knowledge_pack"]), True, model_error
        return (
            fallback_markdown(
                "模拟作战方案",
                "1. 固定红方航母为主要目标。\n2. 使用空对海打击编组执行一次集中打击。\n3. 巡逻能力仅作为说明，不参与首版真实执行。",
            ),
            True,
            model_error,
        )


def generate_battle_plan(
    scenario_understanding_md: str,
    *,
    knowledge_pack: PlannerKnowledgePack | None = None,
    history: list[dict[str, Any]] | None = None,
) -> tuple[str, object]:
    result: AgentRunResult[str] = BattlePlanGenerationAgent().run(
        AgentInputs(
            data={
                "scenario_understanding_md": scenario_understanding_md,
                "knowledge_pack": knowledge_pack,
                "history": history or [],
            },
            skills=["根据想定理解生成粗粒度作战方案"],
        )
    )
    return result.output, result.trace


def _fallback_battle_plan(knowledge_pack: PlannerKnowledgePack) -> str:
    goal = knowledge_pack.planning_goal
    mission_lines = [
        f"- {cap.agent_name}: action={cap.action_type}, subject={cap.subject}, target={cap.target}"
        for cap in knowledge_pack.capability_catalog
    ]
    return "\n".join(
        [
            "# 模拟作战方案",
            "",
            "## 目标",
            f"- {goal.objective}",
            f"- 优化目标：{goal.optimization_objective}",
            "",
            "## 关键假设",
            *[f"- {item}" for item in goal.scenario_assumptions],
            "",
            "## 作战阶段",
            "1. 目标确认：以红方航母作为唯一关键目标。",
            "2. 空对海打击：派出蓝方舰载机执行空对海打击任务。",
            "3. 舰对海打击：蓝方舰艇使用舰载导弹补充打击同一目标。",
            "4. 武器消耗控制：先按最小武器数分配，后续根据评估结果增加弹药。",
            "",
            "## 使用智能体能力",
            *mission_lines,
            "",
            "## 参数建议",
            "- activation_time: 120",
            "- target_ids: ['red_CV16 “辽宁”号001型航空母舰_1']",
            "- weapon_per_target: 2",
        ]
    )
