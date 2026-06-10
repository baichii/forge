from __future__ import annotations

from battle_planner.adapters.runtime.scenario_loader import load_zc_lite_scenario, summarize_scenario
from battle_planner.agents.context import build_zc_lite_knowledge_pack, describe_demo_tools
from battle_planner.orchestration.event import EventLevels, EventPhases, EventTypes, event_handler
from battle_planner.orchestration.stages import WorkflowStages
from battle_planner.orchestration.state.state import BattlePlannerState

from forge.core.specs import CallbackParams

_TARGET_CARRIER_ID = "red_CV16 “辽宁”号001型航空母舰_1"
_TARGET_STATISTIC_CALLBACK_ID = "target_statistic_carrier"


def prepare_scenario_node(state: BattlePlannerState) -> BattlePlannerState:
    node_name = WorkflowStages.SCENARIO_PREPARATION
    event_handler(
        EventTypes.LOG,
        node=node_name,
        phase=EventPhases.START,
        level=EventLevels.NODE,
        iteration_index=state.iteration_index,
    )
    scenario_conf = load_zc_lite_scenario()
    state.scenario_conf = scenario_conf
    state.scenario_name = scenario_conf["name"]
    state.scenario_conf_summary = summarize_scenario(scenario_conf)
    state.planner_knowledge_pack = build_zc_lite_knowledge_pack(scenario_conf)
    state.available_tools = describe_demo_tools()
    state.callback_params = _build_zc_lite_callback_params()
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


def _build_zc_lite_callback_params() -> list[CallbackParams]:
    """构建 zc_lite 想定的 callback 参数。

    Returns:
        zc_lite workflow 当前需要注入的 callback 参数列表。
    """

    return [
        CallbackParams(
            name="target_statistic",
            callback_instance_id=_TARGET_STATISTIC_CALLBACK_ID,
            params={
                "side": "red",
                "target_ids": [_TARGET_CARRIER_ID],
            },
        )
    ]
