from __future__ import annotations

from battle_planner.workspace.local.loaders import load_task_plan_config
from battle_planner.workspace.local.presets import (
    load_agent_param_presets,
    select_agent_param_preset,
)


def test_workspace_local_loads_demo_resources() -> None:
    """验证本地 workspace 资源可以被加载。"""

    task_plan = load_task_plan_config("zc3_lite_carrier_strike")
    payload = load_agent_param_presets()
    preset = select_agent_param_preset(iteration_index=0)

    assert task_plan.plan_id
    assert [branch.branch_id for branch in task_plan.branches] == [1, 2]
    assert [branch.name for branch in task_plan.branches] == ["空对海打击", "海对海打击"]
    assert payload["presets"]
    assert [branch["branch_id"] for branch in payload["presets"][0]["branches"]] == [1, 2]
    assert preset["agents"]
    assert [item.branch_id for item in preset["branch_executions"]] == [1, 2]
