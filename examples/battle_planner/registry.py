from __future__ import annotations

from typing import Callable

from forge.registration import (
    ModuleCreator,
    register_callback,
    register_env,
    register_tick_agent,
    registry,
)


def _register_once(
    module_id: str,
    register_fn: Callable[[str, ModuleCreator | str], ModuleCreator],
    name: str,
    entry_point: ModuleCreator | str,
) -> None:
    if module_id in registry:
        return
    register_fn(name, entry_point)


def register_battle_planner_modules() -> None:
    """Register battle-planner modules without importing implementation classes."""

    _register_once(
        "env/pysim",
        register_env,
        "pysim",
        "battle_planner.adapters.runtime.env_wrappers:make_pysim_env",
    )
    _register_once(
        "tick_agent/air_to_sea_strike_agent",
        register_tick_agent,
        "air_to_sea_strike_agent",
        "battle_planner.tick_agents.air_to_sea_strike_tick_agent:Agent",
    )
    _register_once(
        "tick_agent/naval_to_sea_strike_agent",
        register_tick_agent,
        "naval_to_sea_strike_agent",
        "battle_planner.tick_agents.naval_to_sea_strike_tick_agent:Agent",
    )
    _register_once(
        "callback/step_metric",
        register_callback,
        "step_metric",
        "battle_planner.evaluation.callbacks:StepMetricCallback",
    )
    _register_once(
        "callback/target_statistic",
        register_callback,
        "target_statistic",
        "battle_planner.evaluation.callbacks:TargetStatistic",
    )


__all__ = ["register_battle_planner_modules"]
