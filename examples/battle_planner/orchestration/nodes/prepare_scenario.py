from __future__ import annotations

from battle_planner.adapters.scenario_loader import load_zc_lite_scenario, summarize_scenario
from battle_planner.orchestration.node_logging import log_node_end, log_node_start
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.tools import describe_demo_tools


def prepare_scenario_node(state: BattlePlannerState) -> BattlePlannerState:
    log_node_start("prepare_scenario")
    scenario_conf = load_zc_lite_scenario()
    state.scenario_conf = scenario_conf
    state.scenario_name = scenario_conf["name"]
    state.scenario_conf_summary = summarize_scenario(scenario_conf)
    state.available_tools = describe_demo_tools()
    state.cur_stage = "prepare_scenario"
    log_node_end(
        "prepare_scenario",
        scenario=state.scenario_name,
        sides=list(state.scenario_conf_summary.get("sides", {}).keys()),
        tools=len(state.available_tools),
    )
    return state
