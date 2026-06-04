from __future__ import annotations

from battle_planner.agents.base import AgentInputs, AgentRunResult, BasePlanningAgent
from battle_planner.model.models import EvaluationReport, SimulationRunResult, SummaryEvaluation
from battle_planner.llm_runtime.fallback import fallback_markdown

from forge.core.specs import TickAgentParams


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
                    f"评估报告：\n{inputs.data['evaluation_report'].model_dump()}\n\n"
                    f"报告理解反馈：\n{inputs.data['summary_evaluation'].model_dump()}"
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
        simulation_result = inputs.data["simulation_result"]
        evaluation_report = inputs.data["evaluation_report"]
        summary_evaluation = inputs.data["summary_evaluation"]
        return (
            fallback_markdown(
                "Demo 总结",
                _fallback_summary_body(
                    simulation_result=simulation_result,
                    evaluation_report=evaluation_report,
                    summary_evaluation=summary_evaluation,
                ),
            ),
            True,
            model_error,
        )


def generate_summary(
    *,
    scenario_understanding_md: str,
    battle_plan_md: str,
    planned_agent_params: list[TickAgentParams],
    simulation_result: SimulationRunResult,
    evaluation_report: EvaluationReport,
    summary_evaluation: SummaryEvaluation,
) -> tuple[str, object]:
    result: AgentRunResult[str] = SummaryAgent().run(
        AgentInputs(
            data={
                "scenario_understanding_md": scenario_understanding_md,
                "battle_plan_md": battle_plan_md,
                "planned_agent_params": planned_agent_params,
                "simulation_result": simulation_result,
                "evaluation_report": evaluation_report,
                "summary_evaluation": summary_evaluation,
            },
            memory={
                "summary_evaluation": summary_evaluation.model_dump(mode="json"),
            },
            skills=["读取仿真和评估结果并生成 Markdown 复盘"],
        )
    )
    return result.output, result.trace


def _fallback_summary_body(
    *,
    simulation_result: SimulationRunResult,
    evaluation_report: EvaluationReport,
    summary_evaluation: SummaryEvaluation,
) -> str:
    objective_line = "作战目标已达成。" if summary_evaluation.objective_achieved else "作战目标尚未达成。"
    target_lines = [
        (
            f"- {item.target_id}: alive={item.alive}, "
            f"initial_health={item.initial_health}, current_health={item.current_health}, "
            f"health_delta={item.health_delta}, health_percent_delta={item.health_percent_delta}"
        )
        for item in summary_evaluation.target_status
    ]
    agent_lines = [
        (
            f"- {item.agent_instance_id}({item.agent_name}): "
            f"action_count={item.action_count}, executed={item.executed}, issue={item.issue or '无'}"
        )
        for item in summary_evaluation.agent_execution
    ]
    warning_lines = [f"- {item}" for item in summary_evaluation.warnings] or ["- 无"]
    requested_weapon_count = evaluation_report.mission_metrics.get("requested_weapon_count", 0)
    next_advice = evaluation_report.advice or summary_evaluation.advice
    return "\n".join(
        [
            (
                f"真实环境执行 {simulation_result.steps} 个决策步，"
                f"真实评估分数为 {evaluation_report.score}，"
                f"请求火力数为 {requested_weapon_count}。"
            ),
            objective_line,
            "",
            "## 目标状态",
            *(target_lines or ["- 未获取到目标统计结果。"]),
            "",
            "## Agent 执行",
            *(agent_lines or ["- 未获取到 agent 执行统计。"]),
            "",
            "## 风险提示",
            *warning_lines,
            "",
            "## 下一轮建议",
            next_advice,
        ]
    )
