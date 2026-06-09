from __future__ import annotations

from battle_planner.workspace.local.loaders import load_task_plan_config
from battle_planner.workspace.local.presets import (
    load_display_agent_param_presets,
    select_display_agent_param_preset,
)


def test_workspace_local_loads_demo_resources() -> None:
    task_plan = load_task_plan_config("zc3_lite_carrier_validation")
    payload = load_display_agent_param_presets()
    preset = select_display_agent_param_preset(iteration_index=0)

    assert task_plan.plan_id
    assert [branch.branch_id for branch in task_plan.branches] == [1, 2]
    assert payload["presets"]
    assert preset["agents"]
