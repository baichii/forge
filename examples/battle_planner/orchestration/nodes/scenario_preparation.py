from __future__ import annotations

from battle_planner.adapters.runtime.scenario_loader import load_zc_lite_scenario, summarize_scenario
from battle_planner.agents.context import build_zc_lite_knowledge_pack, describe_demo_tools
from battle_planner.orchestration.event import EventLevels, EventPhases, EventTypes, event_handler
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.workspace.local.plan_presets import load_plan_preset


def scenario_preparation_node(state: BattlePlannerState) -> BattlePlannerState:
    node_name = WorkflowStages.SCENARIO_PREPARATION
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.START,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
    )
    scenario_conf = load_zc_lite_scenario()
    plan_preset = load_plan_preset(
        state.plan_id, scenario_name=state.scenario_name or scenario_conf["name"]
    )
    state.scenario_conf = scenario_conf
    state.scenario_name = scenario_conf["name"]
    state.scenario_conf_summary = summarize_scenario(scenario_conf)
    state.planner_knowledge_pack = build_zc_lite_knowledge_pack(scenario_conf)
    state.available_tools = describe_demo_tools()
    state.callback_params = plan_preset.callback_params
    state.cur_stage = node_name
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.END,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
        payload={
            "scenario": state.scenario_name,
            "sides": list(state.scenario_conf_summary.get("sides", {}).keys()),
            "capabilities": len(state.planner_knowledge_pack.agent_capability_notes),
            "tools": len(state.available_tools),
        },
    )
    return state
