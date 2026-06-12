from __future__ import annotations

from battle_planner.orchestration.nodes.scenario_preparation import scenario_preparation_node
from battle_planner.orchestration.state.state import BattlePlannerState
from battle_planner.workspace.local.plan_presets import ZC3_LITE_PLAN_ID, load_plan_preset


def test_scenario_preparation_node_injects_plan_preset_callback_params() -> None:
    """验证场景准备节点能注入 plan 预定义 callback 参数。"""

    result = scenario_preparation_node(BattlePlannerState(plan_id=ZC3_LITE_PLAN_ID))
    preset = load_plan_preset(ZC3_LITE_PLAN_ID)

    assert result.scenario_name == "zc3_lite"
    assert result.callback_params == preset.callback_params
