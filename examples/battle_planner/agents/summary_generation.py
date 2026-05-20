from __future__ import annotations

from battle_planner.agents.base import AgentInputs, AgentRunResult, BasePlanningAgent
from battle_planner.data.models import EvaluationReport, PlannedAgentParams, SimulationRunResult
from battle_planner.runtime.fallback import fallback_markdown


class SummaryAgent(BasePlanningAgent[str]):
    name = "summary"

    def build_messages(self, inputs: AgentInputs) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": "你是作战方案复盘助手，请只输出最终 Markdown，不要展示思考过程。",
            },
            {
                "role": "user",
                "content": (
                    "请基于以下信息输出总结：\n\n"
                    f"想定理解：\n{inputs.data['scenario_understanding_md']}\n\n"
                    f"作战方案：\n{inputs.data['battle_plan_md']}\n\n"
                    f"智能体参数：\n{[item.model_dump() for item in inputs.data['planned_agent_params']]}\n\n"
                    f"仿真结果：\n{inputs.data['simulation_result'].model_dump()}\n\n"
                    f"评估报告：\n{inputs.data['evaluation_report'].model_dump()}"
                ),
            },
        ]

    def parse_or_fallback(
        self,
        *,
        raw_output: str,
        model_error: str | None,
        inputs: AgentInputs,
    ) -> tuple[str, bool, str | None]:
        if raw_output and model_error is None:
            return raw_output, False, None
        simulation_result = inputs.data["simulation_result"]
        evaluation_report = inputs.data["evaluation_report"]
        return (
            fallback_markdown(
                "Demo 总结",
                (
                    f"真实环境执行 {simulation_result.steps} 个决策步，"
                    f"独立评估占位分数为 {evaluation_report.score}。"
                    "本轮重点验证流程结构，不评价方案效果。"
                ),
            ),
            True,
            model_error,
        )


def generate_summary(
    *,
    scenario_understanding_md: str,
    battle_plan_md: str,
    planned_agent_params: list[PlannedAgentParams],
    simulation_result: SimulationRunResult,
    evaluation_report: EvaluationReport,
) -> tuple[str, object]:
    result: AgentRunResult[str] = SummaryAgent().run(
        AgentInputs(
            data={
                "scenario_understanding_md": scenario_understanding_md,
                "battle_plan_md": battle_plan_md,
                "planned_agent_params": planned_agent_params,
                "simulation_result": simulation_result,
                "evaluation_report": evaluation_report,
            },
            memory={
                "previous_iteration": "首版 demo 暂无历史迭代，仅记录当前执行结果。",
            },
            skills=["读取仿真和评估结果并生成 Markdown 复盘"],
        )
    )
    return result.output, result.trace
