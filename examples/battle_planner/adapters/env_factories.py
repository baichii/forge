from __future__ import annotations

from typing import Any

from battle_planner.adapters.scenario_loader import ensure_pythonlib_path, load_zc_lite_scenario


def make_pysim_env(
    *,
    scenario_conf: dict[str, Any] | None = None,
    subscribe_cont: bool = True,
    render_mode: str | None = "",
):
    """Create a pysim environment."""
    ensure_pythonlib_path()
    from pysim import Sim

    return Sim(
        scenario_conf or load_zc_lite_scenario(),
        subscribe_cont=subscribe_cont,
        render_mode=render_mode,
    )
