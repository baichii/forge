from __future__ import annotations

from battle_planner.model import (
    EvaluationReport,
    LLMTrace,
    PlannerKnowledgePack,
    PlanningGoal,
    SimulationRunResult,
)
from battle_planner.orchestration.state.state import BattlePlannerState

from forge.core.specs import CallbackParams, TickAgentParams

TARGET_CARRIER_ID = "red_CV16 “辽宁”号001型航空母舰_1"
TARGET_STATISTIC_CALLBACK_ID = "target_statistic_carrier"


def test_summary_node_evaluates_target_alive_with_agent_actions(monkeypatch) -> None:
    result = _run_summary_node(
        monkeypatch,
        _make_state(target_alive=True, action_count=2, health_delta=-200),
    )

    evaluation = result.summary_evaluation

    assert evaluation.objective_achieved is False


def test_summary_node_evaluates_target_destroyed_with_agent_actions(monkeypatch) -> None:
    result = _run_summary_node(
        monkeypatch,
        _make_state(target_alive=False, action_count=3, health_delta=-1000),
    )

    evaluation = result.summary_evaluation

    assert evaluation.objective_achieved is True


def test_summary_node_marks_inactive_agent(monkeypatch) -> None:
    result = _run_summary_node(
        monkeypatch,
        _make_state(target_alive=True, action_count=0, health_delta=0),
    )

    evaluation = result.summary_evaluation

    assert evaluation.inactive_agents == ["air_001"]


def test_summary_node_writes_summary_evaluation(monkeypatch) -> None:
    result = _run_summary_node(
        monkeypatch,
        _make_state(target_alive=True, action_count=2, health_delta=-200),
    )

    assert result.summary_md == "summary from fake"
    assert result.cur_stage == "complete"


def _run_summary_node(monkeypatch, state: BattlePlannerState) -> BattlePlannerState:
    import battle_planner.orchestration.nodes.summary as summary_module

    def fake_generate_summary(**kwargs):
        return "summary from fake", LLMTrace(node_name="summary")

    monkeypatch.setattr(summary_module, "generate_summary", fake_generate_summary)
    return summary_module.summary_node(state)


def _make_state(*, target_alive: bool, action_count: int, health_delta: int) -> BattlePlannerState:
    current_health = 0 if not target_alive else 1000 + health_delta
    return BattlePlannerState(
        iteration_index=1,
        planner_knowledge_pack=PlannerKnowledgePack(
            planning_goal=PlanningGoal(
                objective="摧毁红方航母",
                optimization_objective="以最小武器消耗摧毁航母",
            )
        ),
        scenario_understanding_md="红方航母为关键目标。",
        battle_plan_md="使用空中突击和海对海打击。",
        callback_params=[_make_target_statistic_callback()],
        planned_agent_params=[
            TickAgentParams(
                agent_instance_id="air_001",
                agent_name="air_to_sea_strike_agent",
                side="blue",
                params={
                    "unit_ids": ["blue_air_1"],
                    "target_ids": [TARGET_CARRIER_ID],
                    "wp_num": 2,
                },
            )
        ],
        simulation_result=SimulationRunResult(
            scenario_name="zc3_lite",
            steps=10,
            done=not target_alive,
            raw_summary={
                "runner_report": _runner_report(
                    target_alive=target_alive,
                    current_health=current_health,
                    health_delta=health_delta,
                    action_count=action_count,
                )
            },
        ),
        evaluation_report=EvaluationReport(score=75.0),
    )


def _make_target_statistic_callback() -> CallbackParams:
    return CallbackParams(
        name="target_statistic",
        callback_instance_id=TARGET_STATISTIC_CALLBACK_ID,
        params={
            "side": "red",
            "target_ids": [TARGET_CARRIER_ID],
        },
    )


def _runner_report(
    *,
    target_alive: bool,
    current_health: int,
    health_delta: int,
    action_count: int,
) -> dict:
    return {
        "agents": [
            {
                "agent_instance_id": "air_001",
                "agent_name": "air_to_sea_strike_agent",
                "side": "blue",
                "action_count": action_count,
                "first_active_step": 1 if action_count else None,
                "finished_step": 5 if action_count else None,
            }
        ],
        "callbacks": {
            TARGET_STATISTIC_CALLBACK_ID: {
                TARGET_CARRIER_ID: {
                    "alive": target_alive,
                    "initial": {
                        "health": 1000,
                        "health_percent": 1.0,
                    },
                    "current": {
                        "health": current_health,
                        "health_percent": current_health / 1000,
                    },
                    "delta": {
                        "health": health_delta,
                        "health_percent": health_delta / 1000,
                    },
                }
            }
        },
    }
