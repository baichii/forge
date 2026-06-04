from __future__ import annotations

from battle_planner.adapters.runtime.scenario_loader import render_scenario_summary_md
from battle_planner.agents.base import AgentInputs, AgentRunResult, BasePlanningAgent
from battle_planner.agents.context import render_knowledge_pack_md
from battle_planner.model.models import PlannerKnowledgePack
from battle_planner.llm_runtime.fallback import fallback_markdown


class ScenarioUnderstandingAgent(BasePlanningAgent[str]):
    name = "scenario_understanding"

    def build_messages(self, inputs: AgentInputs) -> list[dict[str, str]]:
        if "knowledge_pack" in inputs.data:
            planning_context_md = render_knowledge_pack_md(inputs.data["knowledge_pack"])
        else:
            planning_context_md = render_scenario_summary_md(inputs.data["summary"])
        return [
            {
                "role": "system",
                "content": "你是作战方案规划助手，请只输出最终 Markdown，不要展示思考过程。",
            },
            {
                "role": "user",
                "content": (
                    "请理解以下规划知识包，输出包含任务背景、双方力量、目标假设、"
                    "可用智能体能力、约束条件、初步作战方向的 Markdown。\n\n"
                    f"{planning_context_md}"
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
        if "knowledge_pack" in inputs.data:
            return _fallback_scenario_understanding(inputs.data["knowledge_pack"]), True, model_error
        return (
            fallback_markdown(
                "想定理解",
                "LLM 不可用，使用模板理解：蓝方围绕红方航母目标进行固定目标打击，对手首版假设不主动变化。",
            ),
            True,
            model_error,
        )


def understand_scenario(
    summary: dict | None = None,
    *,
    knowledge_pack: PlannerKnowledgePack | None = None,
) -> tuple[str, object]:
    data = {"knowledge_pack": knowledge_pack} if knowledge_pack is not None else {"summary": summary or {}}
    result: AgentRunResult[str] = ScenarioUnderstandingAgent().run(
        AgentInputs(
            data=data,
            skills=["理解想定并形成 Markdown 作战背景摘要"],
        )
    )
    return result.output, result.trace


def _fallback_scenario_understanding(knowledge_pack: PlannerKnowledgePack) -> str:
    goal = knowledge_pack.planning_goal
    capability_lines = [
        f"- {cap.agent_name}: {cap.capability}，{cap.subject} -> {cap.target}"
        for cap in knowledge_pack.capability_catalog
    ]
    return "\n".join(
        [
            "# 想定理解",
            "",
            "## 任务目标",
            f"- 作战目标：{goal.objective}",
            f"- 优化目标：{goal.optimization_objective}",
            "",
            "## 场景假设",
            *[f"- {item}" for item in goal.scenario_assumptions],
            "",
            "## 可用能力",
            *capability_lines,
            "",
            "## 限制条件",
            *[f"- {item}" for item in goal.constraints],
            "",
            "## 初步作战方向",
            "- 使用空对海打击任务和舰对海打击任务共同围绕红方航母形成打击方案。",
            "- 首版规划以武器消耗最小为优化目标，优先选择满足摧毁目标的最小任务编组。",
        ]
    )
