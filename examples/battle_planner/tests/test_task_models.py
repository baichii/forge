from __future__ import annotations

import pytest
from battle_planner.model.human import (
    BranchHumanInputSpec,
    PlanHumanInputSpec,
)
from battle_planner.model.task import TaskBranchContextSpec
from battle_planner.orchestration.state.state import build_initial_state
from battle_planner.workspace.local.demo_seed import (
    build_local_task_context,
    build_local_task_context_request,
    build_local_task_plan,
    build_local_task_run,
)


def test_local_demo_seed_builds_task_context_and_task_run() -> None:
    task_plan = build_local_task_plan()
    context_request = build_local_task_context_request()
    task_run = build_local_task_run()
    task_context = task_run.task_context
    state = build_initial_state(task_run)

    assert task_context.plan_id == task_plan.plan_id
    assert task_context.plan_name == task_plan.name
    assert task_context.scenario_name == task_plan.scenario_name
    assert task_context.side == task_plan.side
    assert task_context.opponent_side == task_plan.opponent_side
    assert task_context.human == context_request.plan_human
    assert [item.branch_id for item in task_context.branches] == [
        item.branch_id for item in context_request.branch_humans
    ]
    assert [item.human for item in task_context.branches] == [
        item.human for item in context_request.branch_humans
    ]
    assert isinstance(task_context.human, PlanHumanInputSpec)
    assert isinstance(task_context.branches[0], TaskBranchContextSpec)
    assert isinstance(task_context.branches[0].human, BranchHumanInputSpec)
    assert task_context.branches[0].name == task_plan.branches[0].name
    assert not hasattr(task_context, "objective")
    assert not hasattr(task_context.branches[0], "platform")
    assert PlanHumanInputSpec().risk_style == "balanced"
    assert BranchHumanInputSpec().risk_style == "balanced"
    assert task_run.plan_id == task_plan.plan_id
    assert task_run.task_context.plan_id == task_run.plan_id
    assert task_run.options.max_iterations == 5
    assert task_run.options.sim_runs_per_scheme == 1
    assert state.plan_id == task_run.plan_id
    assert state.context_id == task_run.context_id
    assert state.run_id == task_run.run_id
    assert state.scenario_name == task_plan.scenario_name


def test_local_demo_seed_builds_default_branch_humans() -> None:
    task_plan = build_local_task_plan()
    context_request = build_local_task_context_request()

    assert [branch.branch_id for branch in task_plan.branches] == [1, 2]
    assert [item.branch_id for item in context_request.branch_humans] == [1, 2]


def test_local_demo_seed_can_select_branch_ids() -> None:
    context_request = build_local_task_context_request(branch_ids=[1])
    task_context = build_local_task_context(branch_ids=[1])

    assert [item.branch_id for item in context_request.branch_humans] == [1]
    assert [item.branch_id for item in task_context.branches] == [1]


def test_local_demo_seed_rejects_unknown_branch_ids() -> None:
    with pytest.raises(ValueError, match="do not exist in fixture"):
        build_local_task_context_request(branch_ids=[999])
