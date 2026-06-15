from __future__ import annotations

from battle_planner.model import SimulationRunResult
from battle_planner.orchestration.nodes.result_evaluation import result_evaluation_node
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState


def test_result_evaluation_node_collects_callback_metrics_without_report() -> None:
    """验证评估节点只收集 callback 指标，不生成硬编码评估报告。"""

    state = BattlePlannerState(
        simulation_result=SimulationRunResult(
            steps=10,
            done=True,
            raw_summary={"runner_report": _runner_report(damage_ratio={"target_a": 1.0})},
        )
    )

    result = result_evaluation_node(state)

    assert result.cur_stage == WorkflowStages.RESULT_EVALUATION
    assert result.evaluation_report is None
    assert result.evaluation_reports == []
    assert result.simulation_results == [result.simulation_result]
    assert result.simulation_result.metrics["target_destroyed_count"] == 1
    assert result.simulation_result.metrics["target_damage_ratio"] == {"target_a": 1.0}
    assert result.evaluation_summary.case_count == 1
    assert result.evaluation_summary.metric_summary["target_damage_ratio"]["name"] == "目标毁伤比例"


def test_result_evaluation_node_aggregates_multiple_simulation_results() -> None:
    """验证评估节点按 callback declaration 聚合多局指标。"""

    state = BattlePlannerState(
        simulation_results=[
            SimulationRunResult(
                steps=10,
                done=True,
                raw_summary={"runner_report": _runner_report(damage_ratio={"target_a": 1.0})},
            ),
            SimulationRunResult(
                steps=10,
                done=True,
                raw_summary={"runner_report": _runner_report(damage_ratio={"target_a": 0.5})},
            ),
        ]
    )

    result = result_evaluation_node(state)

    assert result.evaluation_report is None
    assert result.evaluation_summary.case_count == 2
    assert result.simulation_results[1].metrics["target_damage_ratio"] == {"target_a": 0.5}
    assert result.evaluation_summary.metric_summary["target_damage_ratio"]["mean"] == 0.75
    assert not hasattr(result.evaluation_summary, "success_rate")
    assert not hasattr(result.evaluation_summary, "mean_score")


def test_result_evaluation_node_uses_declared_agg_metrics() -> None:
    """验证评估聚合只处理声明允许的 callback 指标。"""

    result = result_evaluation_node(
        BattlePlannerState(
            simulation_results=[
                SimulationRunResult(
                    steps=1,
                    done=True,
                    metrics={"requested_weapon_count": 6, "env_done": True, "unknown_metric": 100},
                    raw_summary={
                        "runner_report": _runner_report(
                            destroyed_count=1,
                            damage_ratio={"target_a": 0.2, "target_b": 0.4, "nested": {"x": 1}},
                        )
                    },
                ),
                SimulationRunResult(
                    steps=1,
                    done=True,
                    raw_summary={
                        "runner_report": _runner_report(
                            destroyed_count=2,
                            damage_ratio={"target_a": 0.6, "target_b": 0.8, "flag": True},
                        )
                    },
                ),
            ]
        )
    )
    summary = result.evaluation_summary

    assert summary.metric_summary["target_destroyed_count"]["mean"] == 1.5
    assert summary.metric_summary["target_damage_ratio"]["mean"] == 0.5
    assert summary.metric_summary["target_damage_ratio"]["key"] == "target_damage_ratio"
    assert summary.metric_summary["target_damage_ratio"]["name"] == "目标毁伤比例"
    assert "requested_weapon_count" not in summary.metric_summary
    assert "env_done" not in summary.metric_summary
    assert "unknown_metric" not in summary.metric_summary


def _runner_report(
    *,
    damage_ratio: dict[str, object],
    target_count: int = 1,
    destroyed_count: int = 1,
) -> dict:
    return {
        "agents": [
            {
                "agent_instance_id": "naval_001",
                "agent_name": "naval_to_sea_strike_agent",
                "side": "blue",
                "action_count": 1,
            }
        ],
        "callbacks": {
            "target_statistic_carrier": {
                "schema_version": "callback_eval.v0",
                "callback_instance_id": "target_statistic_carrier",
                "callback_name": "target_statistic",
                "metrics": {
                    "target_count": target_count,
                    "target_destroyed_count": destroyed_count,
                    "target_damage_ratio": damage_ratio,
                    "not_declared_metric": 999,
                },
                "payload": {
                    "targets": {
                        "target_a": {
                            "alive": destroyed_count == 0,
                            "initial": {"health": 1000, "health_percent": 1.0},
                            "current": {"health": 0, "health_percent": 0.0},
                            "delta": {"health": -1000, "health_percent": -1.0},
                        }
                    }
                },
            }
        },
    }
