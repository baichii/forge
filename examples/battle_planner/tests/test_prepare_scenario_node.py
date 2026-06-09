from __future__ import annotations

from battle_planner.orchestration.nodes.prepare_scenario import prepare_scenario_node
from battle_planner.orchestration.state.state import BattlePlannerState


def test_prepare_scenario_node_injects_zc_lite_callback_params() -> None:
    result = prepare_scenario_node(BattlePlannerState())

    assert result.scenario_name == "zc3_lite"
    assert result.callback_params
    assert result.callback_params[0].name == "target_statistic"
    assert result.callback_params[0].callback_instance_id == "target_statistic_carrier"
    assert result.callback_params[0].params["target_ids"] == ["red_CV16 “辽宁”号001型航空母舰_1"]
