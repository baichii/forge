from __future__ import annotations

from random import Random

from battle_planner.data.demo_models import EvaluationReport, SimulationRunResult


class RandomDemoEvaluator:
    """Independent evaluator component for the first end-to-end demo."""

    def __init__(self, seed: int = 20260518):
        self._rng = Random(seed)

    def evaluate(self, result: SimulationRunResult) -> EvaluationReport:
        score = round(self._rng.uniform(45.0, 82.0), 2)
        hard_violations: list[str] = []
        if result.steps == 0:
            hard_violations.append("simulation produced no steps")

        return EvaluationReport(
            score=score,
            hard_violations=hard_violations,
            mission_metrics={
                "sim_decision_steps": result.steps,
                "env_done": result.done,
                "demo_score": score,
            },
            diagnostic_events=[
                {
                    "event": "random_metric_placeholder",
                    "detail": "首版评估指标为随机占位，后续替换为真实毁伤/目标达成指标。",
                }
            ],
            advice="首版只验证全流程，后续需要定义真实目标达成率、损耗、时序和风险指标。",
        )
