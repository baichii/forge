from __future__ import annotations

from battle_planner.adapters.scenario_loader import render_scenario_summary_md
from battle_planner.planning.base import AgentInputs, AgentRunResult, BasePlanningAgent
from battle_planner.runtime.fallback import fallback_markdown


class ScenarioUnderstandingAgent(BasePlanningAgent[str]):
    name = "scenario_understanding"

    def build_messages(self, inputs: AgentInputs) -> list[dict[str, str]]:
        summary_md = render_scenario_summary_md(inputs.data["summary"])
        return [
            {
                "role": "system",
                "content": "你是作战方案规划助手，请只输出最终 Markdown，不要展示思考过程。",
            },
            {
                "role": "user",
                "content": (
                    "请理解以下想定摘要，输出包含任务背景、双方力量、目标假设、"
                    "约束条件、初步作战方向的 Markdown。\n\n"
                    f"{summary_md}"
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
        return (
            fallback_markdown(
                "想定理解",
                "LLM 不可用，使用模板理解：蓝方围绕红方航母目标进行固定目标打击，对手首版假设不主动变化。",
            ),
            True,
            model_error,
        )


def understand_scenario(summary: dict) -> tuple[str, object]:
    result: AgentRunResult[str] = ScenarioUnderstandingAgent().run(
        AgentInputs(
            data={"summary": summary},
            skills=["理解想定并形成 Markdown 作战背景摘要"],
        )
    )
    return result.output, result.trace
