from __future__ import annotations

from battle_planner.workspace.resource.loader import (
    iter_tick_agent_resources,
    load_tick_agent_specs,
    register_tick_agent_resources,
)

from forge.core.specs import TickAgentParams
from forge.registration import make_tick_agent, registry


def test_tick_agent_resources_use_relative_entrypoints() -> None:
    descriptors = iter_tick_agent_resources()

    assert {descriptor.name for descriptor in descriptors} == {
        "air_to_sea_strike_agent",
        "naval_to_sea_strike_agent",
    }
    assert all(descriptor.relative_entrypoint == "agent:Agent" for descriptor in descriptors)
    assert all(descriptor.resolved_entrypoint.startswith("battle_planner.") for descriptor in descriptors)


def test_load_tick_agent_specs_returns_resolved_entrypoints() -> None:
    specs = load_tick_agent_specs()

    assert {spec.name for spec in specs} == {"air_to_sea_strike_agent", "naval_to_sea_strike_agent"}
    assert all(spec.entrypoint.startswith("battle_planner.workspace.resource.") for spec in specs)


def test_register_tick_agent_resources_registers_makeable_agents() -> None:
    registry.pop("tick_agent/air_to_sea_strike_agent", None)
    registry.pop("tick_agent/naval_to_sea_strike_agent", None)

    register_tick_agent_resources()

    agent = make_tick_agent(
        "air_to_sea_strike_agent",
        params=TickAgentParams(
            agent_name="air_to_sea_strike_agent",
            side="blue",
            params={
                "start_time": 0,
                "end_time": 1,
                "unit_ids": ["blue_air_1"],
                "target_ids": ["red_ship_1"],
            },
        ),
    )

    assert type(agent).__module__ == "battle_planner.workspace.resource.tick_agents.air_to_sea_strike.agent"
    assert agent.declaration.entrypoint == "agent:Agent"
