from __future__ import annotations

from typing import Callable

from battle_planner.workspace.resource.loader import register_tick_agent_resources

from forge.registration import (
    ModuleCreator,
    register_callback,
    register_env,
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
        "callback/target_statistic",
        register_callback,
        "target_statistic",
        "battle_planner.workspace.resource.callbacks.target_statistic:TargetStatistic",
    )
    register_tick_agent_resources()


__all__ = ["register_battle_planner_modules"]
