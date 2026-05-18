from __future__ import annotations

from battle_planner.planning.base import AgentInputs, AgentRunResult, BasePlanningAgent
from battle_planner.runtime.fallback import fallback_markdown


class BattlePlanGenerationAgent(BasePlanningAgent[str]):
    name = "battle_plan_generation"

    def build_messages(self, inputs: AgentInputs) -> list[dict[str, str]]:
        scenario_understanding_md = inputs.data["scenario_understanding_md"]
        return [
            {
                "role": "system",
                "content": (
                    "你是作战方案规划助手。首版假设对手不会主动变化，只围绕目标达成生成粗粒度方案。"
                    "请只输出最终 Markdown，不要展示思考过程。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "基于以下想定理解，模拟生成一个 Markdown 作战方案。"
                    "方案需要包含目标、阶段、使用的智能体能力、关键假设。\n\n"
                    f"{scenario_understanding_md}"
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
                "模拟作战方案",
                "1. 固定红方航母为主要目标。\n2. 使用空对海打击编组执行一次集中打击。\n3. 巡逻能力仅作为说明，不参与首版真实执行。",
            ),
            True,
            model_error,
        )


def generate_battle_plan(scenario_understanding_md: str) -> tuple[str, object]:
    result: AgentRunResult[str] = BattlePlanGenerationAgent().run(
        AgentInputs(
            data={"scenario_understanding_md": scenario_understanding_md},
            skills=["根据想定理解生成粗粒度作战方案"],
        )
    )
    return result.output, result.trace
