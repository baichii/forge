from __future__ import annotations

from battle_planner.data.models import SimulationRunResult
from battle_planner.orchestration.nodes.evaluation import evaluation_node
from battle_planner.orchestration.state.state import BattlePlannerState


def test_evaluation_node_uses_target_outcome_report() -> None:
    state = BattlePlannerState(
        simulation_result=SimulationRunResult(
            scenario_name="zc3_lite",
            steps=10,
            done=True,
            raw_summary={"runner_report": _runner_report()},
        )
    )

    result = evaluation_node(state)

    assert result.cur_stage == "evaluation"
    assert result.evaluation_report.mission_metrics["objective_achieved"] is True
    assert result.evaluation_report.mission_metrics["requested_weapon_count"] == 4


def _runner_report() -> dict:
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
                    "alive": False,
                    "initial": {"health": 1000, "health_percent": 1.0},
                    "current": {"health": 0, "health_percent": 0.0},
                    "delta": {"health": -1000, "health_percent": -1.0},
                }
            }
        },
    }
