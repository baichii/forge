from __future__ import annotations


def test_air_to_sea_tick_agent_declaration_and_step() -> None:
    from battle_planner.registry import register_battle_planner_modules
    from battle_planner.tick_agents.air_to_sea_strike_tick_agent import declaration
    from pysim.schema.enums import ActionType, MissionType

    from forge.core.specs import TickAgentParams, TickAgentSpec
    from forge.registration import make_tick_agent

    assert isinstance(declaration, TickAgentSpec)
    exported = declaration.model_dump()
    assert exported["name"] == "air_to_sea_strike_agent"
    assert exported["entrypoint"] == "battle_planner.tick_agents.air_to_sea_strike_tick_agent:Agent"
    assert "start_time" in exported["params"]
    assert "wp_num" in exported["params"]
    assert exported["status"] == ["running", "finished"]

    register_battle_planner_modules()
    agent = make_tick_agent(
        declaration.name,
        params=TickAgentParams(
            agent_instance_id="air_test_001",
            agent_name=declaration.name,
            side="blue",
            params={
                "start_time": 100,
                "end_time": 200,
                "unit_ids": ["blue_air_1"],
                "target_ids": ["red_ship_1"],
                "wp_num": 2,
            },
        ),
    )
    assert agent.id == "air_test_001"
    assert agent.name == "air_to_sea_strike_agent"

    actions, status, done, info = agent.step({"sim_time": 50})
    assert actions == []
    assert status == {"running": False, "finished": False}
    assert done is False
    assert info["reason"] == "before_start_time"

    actions, status, done, info = agent.step({"sim_time": 120})
    assert actions[0]["type"] == ActionType.MISSION
    assert actions[0]["side"] == "blue"
    assert actions[0]["params"]["type"] == MissionType.AirAttackCommon
    assert actions[0]["params"]["params"]["unit_ids"] == ["blue_air_1"]
    assert actions[0]["params"]["params"]["target_id"] == "red_ship_1"
    assert actions[0]["params"]["params"]["wp_num"] == 2
    assert status == {"running": False, "finished": True}
    assert done is True
    assert info["task_type"] == "NavalAsuWStrike_Air"
    assert info["source"] == "air_to_sea_strike_agent"

    actions, status, done, info = agent.step({"sim_time": 130})
    assert actions == []
    assert status == {"running": False, "finished": True}
    assert done is True
    assert info["reason"] == "mission_already_dispatched"


def test_naval_to_sea_tick_agent_declaration_and_step() -> None:
    from battle_planner.registry import register_battle_planner_modules
    from battle_planner.tick_agents.naval_to_sea_strike_tick_agent import declaration
    from pysim.schema.enums import ActionType, MissionType

    from forge.core.specs import TickAgentParams, TickAgentSpec
    from forge.registration import make_tick_agent

    assert isinstance(declaration, TickAgentSpec)
    exported = declaration.model_dump()
    assert exported["name"] == "naval_to_sea_strike_agent"
    assert exported["entrypoint"] == "battle_planner.tick_agents.naval_to_sea_strike_tick_agent:Agent"
    assert set(exported["params"]) >= {
        "start_time",
        "end_time",
        "unit_ids",
        "target_ids",
        "wp_num",
        "clear_targets",
    }
    assert exported["status"] == ["running", "finished"]

    register_battle_planner_modules()
    agent = make_tick_agent(
        declaration.name,
        params=TickAgentParams(
            agent_instance_id="naval_test_001",
            agent_name=declaration.name,
            side="blue",
            params={
                "start_time": 150,
                "end_time": 260,
                "unit_ids": ["blue_ship_1"],
                "target_ids": ["red_ship_1"],
            },
        ),
    )
    assert agent.id == "naval_test_001"
    assert agent.name == "naval_to_sea_strike_agent"

    actions, status, done, info = agent.step({"sim_time": 180})
    assert actions[0]["type"] == ActionType.MISSION
    assert actions[0]["side"] == "blue"
    assert actions[0]["params"]["type"] == MissionType.MissileAttack
    assert actions[0]["params"]["params"]["target_id"] == "red_ship_1"
    assert actions[0]["params"]["params"]["wp_num"] == 2
    assert status == {"running": False, "finished": True}
    assert done is True
    assert info["task_type"] == "NavalAsuWStrike_Naval"
