"""基于 fake 仿真输出生成下一轮参数修改意见。"""

from dataclasses import dataclass

from battle_planner.data.models import SimulationResult, StrategyRecommendation


@dataclass
class SummaryPlanAgentConfig:
    target_score: float = 88.0
    adjustment_step: float = 0.12


class SummaryPlanAgent:
    def __init__(self, config: SummaryPlanAgentConfig):
        self.config = config

    def invoke(
        self,
        result: SimulationResult,
        best_result: SimulationResult | None,
        max_iterations: int,
    ) -> StrategyRecommendation:
        stats = result.statistics
        avg_risk = float(stats.get("avg_risk", 0.0))
        avg_cohesion = float(stats.get("avg_cohesion", 0.0))
        avg_pressure = float(stats.get("avg_pressure", 0.0))
        event_names = [str(event.get("event")) for event in result.key_events]
        overextend_count = event_names.count("overextend")
        formation_drift_count = event_names.count("formation_drift")

        adjustments: dict[str, float] = {}
        advice_parts: list[str] = []

        if avg_risk > 0.35 or overextend_count > 0:
            adjustments["aggression"] = -self.config.adjustment_step
            adjustments["retreat_threshold"] = self.config.adjustment_step
            advice_parts.append("出现过度推进或风险偏高，降低进攻倾向并提高撤退阈值")
        elif avg_pressure < 0.68:
            adjustments["aggression"] = self.config.adjustment_step
            advice_parts.append("压制不足，提高进攻倾向")

        if avg_cohesion < 0.92 or formation_drift_count > 0:
            current_gap = float(result.params.get("formation_gap", 0.55))
            direction = -1.0 if current_gap > 0.45 else 1.0
            adjustments["formation_gap"] = direction * min(self.config.adjustment_step, 0.08)
            advice_parts.append("出现队形漂移或协同不足，将队形间隔向 0.45 收敛")

        if not adjustments and result.score < self.config.target_score:
            adjustments["aggression"] = self.config.adjustment_step / 2
            advice_parts.append("未达目标分数，小幅提高进攻倾向继续探索")

        if not advice_parts:
            advice_parts.append("当前参数较稳定，仅保留作为候选最优方案")

        best_score = best_result.score if best_result else result.score
        should_continue = (
            result.iteration < max_iterations
            and result.score < self.config.target_score
            and bool(adjustments)
        )

        return StrategyRecommendation(
            iteration=result.iteration,
            advice="；".join(advice_parts),
            param_adjustments=adjustments,
            should_continue=should_continue,
            reason=(
                f"score={result.score}, best_score={best_score}, "
                f"target_score={self.config.target_score}"
            ),
        )
