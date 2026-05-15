"""
处理战斗策略规划的Agent
"""

from dataclasses import dataclass
from typing import Any

from battle_planner.data.models import (
    Strategy,
    StrategyParameterSet,
    StrategyRecommendation,
    TickAgent,
)


@dataclass
class StrategyPlanAgentConfig:
    adjustment_step: float = 0.12


class StrategyPlanAgent:
    def __init__(self, config: StrategyPlanAgentConfig):
        self.config = config

    def _clamp_param(self, name: str, value: float, tick_agent: TickAgent) -> float:
        for param in tick_agent.params:
            if param.name == name:
                if param.min_value is not None:
                    value = max(float(param.min_value), value)
                if param.max_value is not None:
                    value = min(float(param.max_value), value)
                break
        return round(value, 3)

    def invoke(
        self,
        strategy: Strategy,
        tick_agent: TickAgent,
        iteration: int,
        previous_params: StrategyParameterSet | None = None,
        recommendation: StrategyRecommendation | None = None,
    ) -> StrategyParameterSet:
        params: dict[str, Any] = {param.name: param.default for param in tick_agent.params}

        rationale = "使用 tick agent 默认参数生成第一轮方案。"
        if previous_params is not None:
            params.update(previous_params.params)
            rationale = "基于上一轮参数和 summary 修改意见生成下一轮方案。"

        if recommendation is not None:
            for name, delta in recommendation.param_adjustments.items():
                if name not in params:
                    continue
                try:
                    current = float(params[name])
                except (TypeError, ValueError):
                    continue
                params[name] = self._clamp_param(name, current + delta, tick_agent)
            rationale = f"{rationale} 修改意见: {recommendation.advice}"

        return StrategyParameterSet(
            iteration=iteration,
            params=params,
            rationale=f"{strategy.name}: {rationale}",
        )

    def plan_strategy(self, strategy: str) -> str:
        """根据输入的策略描述，生成优化后的策略方案
        Args:
            strategy: 原始策略描述
        Returns:
            优化后的策略方案
        """
        return f"fake strategy plan for: {strategy}"
