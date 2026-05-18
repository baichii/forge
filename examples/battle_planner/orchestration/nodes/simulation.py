from __future__ import annotations

from battle_planner.adapters.zc_drill_env import run_zc_lite_drill_env
from battle_planner.config import config
from battle_planner.orchestration.node_logging import log_node_end, log_node_error, log_node_start
from battle_planner.orchestration.state.state import BattlePlannerState


def simulation_node(state: BattlePlannerState) -> BattlePlannerState:
    log_node_start(
        "simulation", scenario=state.scenario_name, planned_agents=len(state.planned_agent_params)
    )
    try:
        timing = next(
            (item for item in state.planned_agent_params if item.agent_name == "mission_timing_planner"),
            None,
        )
        max_steps = config.simulation.max_decision_steps
        if timing is not None:
            max_steps = int(timing.params.get("max_decision_steps", max_steps))
        state.simulation_result = run_zc_lite_drill_env(
            state.scenario_conf,
            state.planned_agent_params,
            max_decision_steps=max_steps,
        )
        state.cur_stage = "simulation"
        log_node_end(
            "simulation",
            steps=state.simulation_result.steps,
            done=state.simulation_result.done,
            env=state.simulation_result.raw_summary.get("env"),
        )
    except Exception as exc:
        state.mark_error(f"simulation failed: {exc}")
        log_node_error("simulation", state.error or str(exc))
    return state
