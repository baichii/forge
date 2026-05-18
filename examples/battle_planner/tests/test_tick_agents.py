from __future__ import annotations

import sys
from pathlib import Path

EXAMPLES_ROOT = Path(__file__).resolve().parents[2]
if str(EXAMPLES_ROOT) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_ROOT))


def test_air_to_sea_tick_agent_declaration_and_step() -> None:
    from battle_planner.tick_agents.air_to_sea_strike_tick_agent import declaration
    from battle_planner.tick_agents.base import TickAgentFactory, TickAgentRuntimeContext
    from pysim.schema.enums import ActionType, MissionType

    from forge.utils.specs import TickAgentSpec

    assert isinstance(declaration, TickAgentSpec)
    exported = declaration.export_json_schema()
    assert exported["name"] == "air_to_sea_strike_agent"
    assert exported["entrypoint"] == "battle_planner.tick_agents.air_to_sea_strike_tick_agent:Agent"
    assert "start_time" in exported["params"]
    assert "wp_num" in exported["params"]
    assert exported["status"] == ["running", "finished"]

    agent = TickAgentFactory.create(
        declaration,
        {
            "start_time": 100,
            "end_time": 200,
            "unit_ids": ["blue_air_1"],
            "target_ids": ["red_ship_1"],
            "wp_num": 2,
        },
        runtime_context=TickAgentRuntimeContext(agent_name="test_runner"),
    )

    actions, status, done, info = agent.step({"sim_time": 50})
    assert actions == []
    assert status == {"running": False, "finished": False}
    assert done is False
    assert info["reason"] == "before_start_time"

    actions, status, done, info = agent.step({"sim_time": 120})
    assert actions[0]["type"] == ActionType.MISSION
    assert actions[0]["params"]["type"] == MissionType.AirAttackCommon
    assert actions[0]["params"]["params"]["unit_ids"] == ["blue_air_1"]
    assert actions[0]["params"]["params"]["target_id"] == "red_ship_1"
    assert actions[0]["params"]["params"]["wp_num"] == 2
    assert status == {"running": False, "finished": True}
    assert done is True
    assert info["task_type"] == "NavalAsuWStrike_Air"
    assert info["source"] == "test_runner"

    actions, status, done, info = agent.step({"sim_time": 130})
    assert actions == []
    assert status == {"running": False, "finished": True}
    assert done is True
    assert info["reason"] == "mission_already_dispatched"


def test_naval_to_sea_tick_agent_declaration_and_step() -> None:
    from battle_planner.tick_agents.base import TickAgentFactory
    from battle_planner.tick_agents.naval_to_sea_strike_tick_agent import declaration
    from pysim.schema.enums import ActionType, MissionType

    from forge.utils.specs import TickAgentSpec

    assert isinstance(declaration, TickAgentSpec)
    exported = declaration.export_json_schema()
    assert exported["name"] == "naval_to_sea_strike_agent"
    assert exported["entrypoint"] == "battle_planner.tick_agents.naval_to_sea_strike_tick_agent:Agent"
    assert set(exported["params"]) >= {"start_time", "end_time", "unit_ids", "target_ids", "wp_num", "clear_targets"}
    assert exported["status"] == ["running", "finished"]

    agent = TickAgentFactory.create(
        declaration,
        {
            "start_time": 150,
            "end_time": 260,
            "unit_ids": ["blue_ship_1"],
            "target_ids": ["red_ship_1"],
        },
    )

    actions, status, done, info = agent.step({"sim_time": 180})
    assert actions[0]["type"] == ActionType.MISSION
    assert actions[0]["params"]["type"] == MissionType.MissileAttack
    assert actions[0]["params"]["params"]["target_id"] == "red_ship_1"
    assert actions[0]["params"]["params"]["wp_num"] == 2
    assert status == {"running": False, "finished": True}
    assert done is True
    assert info["task_type"] == "NavalAsuWStrike_Naval"
