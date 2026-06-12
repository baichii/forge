from __future__ import annotations

from battle_planner.model import SimulationRunResult
from battle_planner.orchestration.nodes.result_evaluation import result_evaluation_node
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState


def test_result_evaluation_node_uses_target_outcome_report() -> None:
    """验证评估节点能读取单局仿真报告并生成判定结果。"""

    state = BattlePlannerState(
        simulation_result=SimulationRunResult(
            steps=10,
            done=True,
            raw_summary={"runner_report": _runner_report()},
        )
    )

    result = result_evaluation_node(state)

    assert result.cur_stage == WorkflowStages.RESULT_EVALUATION
    assert result.evaluation_report.objective_achieved is True
    assert result.simulation_result.metrics["requested_weapon_count"] == 4
    assert result.evaluation_summary.case_count == 1
    assert result.evaluation_summary.success_rate == 1


def test_result_evaluation_node_aggregates_multiple_simulation_results() -> None:
    """验证评估节点能处理同一轮内的多次仿真结果。"""

    state = BattlePlannerState(
        simulation_results=[
            SimulationRunResult(
                steps=10,
                done=True,
                raw_summary={"runner_report": _runner_report(alive=False, current_health=0, delta=-1000)},
            ),
            SimulationRunResult(
                steps=10,
                done=True,
                raw_summary={"runner_report": _runner_report(alive=True, current_health=500, delta=-500)},
            ),
        ]
    )

    result = result_evaluation_node(state)

    assert len(result.evaluation_reports) == 2
    assert result.evaluation_report == result.evaluation_reports[0]
    assert result.evaluation_summary.case_count == 2
    assert result.evaluation_summary.success_count == 1
    assert result.evaluation_summary.success_rate == 0.5
    assert result.evaluation_summary.mean_score == 69
    assert result.evaluation_summary.recommended_simulation_index == 0
    assert result.simulation_results[1].metrics["target_damage_ratio"] == 0.5
    assert result.evaluation_reports[1].findings[0].code == "target_not_destroyed"


def _runner_report(*, alive: bool = False, current_health: int = 0, delta: int = -1000) -> dict:
    target_id = "red_CV16 “辽宁”号001型航空母舰_1"
    return {
        "agents": [
            {
                "agent_instance_id": "naval_001",
                "agent_name": "naval_to_sea_strike_agent",
                "side": "blue",
                "action_count": 1,
                "events": [
                    {
                        "step": 3,
                        "sim_time": 60,
                        "raw_actions": [
                            {
                                "params": {
                                    "type": "MissileAttack",
                                    "params": {
                                        "unit_ids": ["ship_1"],
                                        "target_id": target_id,
                                        "wp_num": 4,
                                    },
                                }
                            }
                        ],
                    }
                ],
            }
        ],
        "callbacks": {
            "target_statistic_carrier": {
                target_id: {
                    "alive": alive,
                    "initial": {"health": 1000, "health_percent": 1.0},
                    "current": {"health": current_health, "health_percent": current_health / 1000},
                    "delta": {"health": delta, "health_percent": delta / 1000},
                }
            }
        },
    }
