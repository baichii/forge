from __future__ import annotations

from battle_planner.orchestration.node_logging import log_node_end


def test_planned_agents_log_keeps_full_agent_params(capsys) -> None:
    log_node_end(
        "agent_parameter_planning",
        fallback=False,
        planned_agents=[
            {
                "agent_instance_id": "air_001",
                "agent_name": "air_to_sea_strike_agent",
                "agent_params": {
                    "start_time": 120,
                    "end_time": 180,
                    "unit_ids": [
                        "blue_F/A-18F型“超级大黄蜂”战斗机_14",
                        "blue_F/A-18F型“超级大黄蜂”战斗机_15",
                    ],
                    "target_ids": ["red_CV16 “辽宁”号001型航空母舰_1"],
                    "wp_num": 2,
                    "clear_targets": True,
                },
            }
        ],
        error=None,
    )

    output = capsys.readouterr().out

    assert "blue_F/A-18F型“超级大黄蜂”战斗机_15" in output
    assert "red_CV16 “辽宁”号001型航空母舰_1" in output
    assert "unit_ids..." not in output
