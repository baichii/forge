from __future__ import annotations

from battle_planner.workspace.local.loaders import (
    load_task_plan_config,
    resolve_task_plan_config_path,
)
from battle_planner.workspace.local.presets import (
    load_display_agent_param_presets,
    resolve_display_preset_file,
    select_display_agent_param_preset,
)


def test_load_task_plan_config_from_workspace_local() -> None:
    path = resolve_task_plan_config_path("zc3_lite_carrier_validation")
    task_plan = load_task_plan_config("zc3_lite_carrier_validation")

    assert "workspace/local/task_plans" in path.as_posix()
    assert task_plan.plan_id
    assert task_plan.branches


def test_load_display_presets_from_workspace_local() -> None:
    path = resolve_display_preset_file()
    payload = load_display_agent_param_presets()
    preset = select_display_agent_param_preset(iteration_index=0)

    assert "workspace/local/runtime_presets" in path.as_posix()
    assert payload["presets"]
    assert preset["preset_id"]
    assert preset["agents"]
