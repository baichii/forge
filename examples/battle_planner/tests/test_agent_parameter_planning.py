from __future__ import annotations

from battle_planner.agents.agent_parameter_planning import _extract_agent_param_items


def test_extract_agent_param_items_skips_non_agent_arrays() -> None:
    raw_output = """
候选目标：["red_carrier_1"]
{"agents":[{"agent_instance_id":"air_001","agent_name":"air_to_sea_strike_agent","side":"blue","params":{"unit_ids":["blue_air_1"],"target_ids":["red_carrier_1"]}}]}
"""

    items = _extract_agent_param_items(raw_output)

    assert items == [
        {
            "agent_instance_id": "air_001",
            "agent_name": "air_to_sea_strike_agent",
            "side": "blue",
            "params": {
                "unit_ids": ["blue_air_1"],
                "target_ids": ["red_carrier_1"],
            },
        }
    ]
