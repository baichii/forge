from __future__ import annotations

import pytest
from battle_planner.model.models import (
    HumanInputSpec,
    TaskBranchHumanInputRequest,
    TaskContextCreateRequest,
    TaskPlanSpec,
    build_task_context,
)
from battle_planner.orchestration.state.state import build_initial_state
from battle_planner.workspace.local.demo_seed import (
    build_local_task_context,
    build_local_task_context_request,
    build_local_task_plan,
    build_local_task_run,
)


def test_build_task_context_and_task_run() -> None:
    task_plan = build_local_task_plan()
    context_request = build_local_task_context_request()
    task_run = build_local_task_run()
    task_context = task_run.task_context_snapshot
    state = build_initial_state(task_run)

    assert task_context.plan_snapshot == task_plan
    assert task_context.plan_human == context_request.plan_human
    assert task_context.branch_humans == context_request.branch_humans
    assert task_run.plan_id == task_plan.plan_id
    assert task_run.task_context_snapshot.plan_snapshot.plan_id == task_run.plan_id
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
    assert [item.branch_id for item in task_context.branch_humans] == [1]


def test_local_demo_seed_rejects_unknown_branch_ids() -> None:
    with pytest.raises(ValueError, match="do not exist in fixture"):
        build_local_task_context_request(branch_ids=[999])


def test_build_task_context_rejects_unknown_branch() -> None:
    task_plan = TaskPlanSpec(
        plan_id="2175600675558391812",
        name="航母对抗任务方案",
        scenario_name="zc_lite",
        side="blue",
        branches=[{"branch_id": 1, "name": "空海协同打击"}],
    )
    context_request = TaskContextCreateRequest(
        plan_id="2175600675558391812",
        branch_humans=[
            TaskBranchHumanInputRequest(
                branch_id=999,
                human=HumanInputSpec(summary="bad branch"),
            )
        ],
    )

    with pytest.raises(ValueError, match="unknown branch ids"):
        build_task_context(
            task_plan,
            context_request,
            context_id="2175600675558391811",
        )
