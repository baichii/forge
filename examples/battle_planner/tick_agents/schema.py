from __future__ import annotations

from battle_planner.tick_agents.air_to_sea_strike_tick_agent import (
    declaration as air_to_sea_strike_declaration,
)
from battle_planner.tick_agents.naval_to_sea_strike_tick_agent import (
    declaration as naval_to_sea_strike_declaration,
)

from forge.core.specs import TickAgentSpec


def load_tick_agent_specs() -> list[TickAgentSpec]:
    return [
        air_to_sea_strike_declaration,
        naval_to_sea_strike_declaration,
    ]
