from __future__ import annotations

import pytest
from battle_planner.model.models import (
    HumanInputSpec,
    TaskBranchHumanInputRequest,
    TaskContextCreateRequest,
    TaskPlanSpec,
    TaskRunCreateRequest,
    build_task_context,
    build_task_run,
)
from battle_planner.orchestration.state.state import build_initial_state


def test_build_task_context_and_task_run() -> None:
    task_plan = TaskPlanSpec(
        plan_id="plan-001",
        name="航母对抗任务方案",
        scenario_name="zc_lite",
        side="blue",
        opponent_side="red",
        objective="摧毁红方航母",
        branches=[
            {
                "branch_id": "branch-001",
                "name": "空海协同打击",
                "description": "空中突击后舰艇补充打击。",
            }
        ],
    )
    context_request = TaskContextCreateRequest(
        plan_id="plan-001",
        name="航母对抗任务上下文",
        plan_human=HumanInputSpec(summary="优先验证数据链路。"),
        branch_humans=[
            TaskBranchHumanInputRequest(
                branch_id="branch-001",
                human=HumanInputSpec(items=["只做单分支验证。"]),
            )
        ],
    )
    task_context = build_task_context(
        task_plan,
        context_request,
        task_context_id="task-context-001",
        created_at="2026-06-09 00:00:00",
    )
    task_run = build_task_run(
        task_context,
        TaskRunCreateRequest(
            task_context_id="task-context-001",
            options={
                "workflow_name": "zc_lite_baseline",
                "max_iterations": 3,
                "sim_runs_per_scheme": 2,
                "max_retry": 1,
            },
        ),
        run_id="run-001",
        created_at="2026-06-09 00:00:01",
    )
    state = build_initial_state(task_run)

    assert task_context.plan_snapshot == task_plan
    assert task_context.plan_human.summary == "优先验证数据链路。"
    assert task_run.options.max_iterations == 3
    assert task_run.options.sim_runs_per_scheme == 2
    assert state.plan_id == "plan-001"
    assert state.task_context_id == "task-context-001"
    assert state.run_id == "run-001"
    assert state.scenario_name == "zc_lite"


def test_build_task_context_rejects_unknown_branch() -> None:
    task_plan = TaskPlanSpec(
        plan_id="plan-001",
        name="航母对抗任务方案",
        scenario_name="zc_lite",
        side="blue",
        branches=[{"branch_id": "branch-001", "name": "空海协同打击"}],
    )
    context_request = TaskContextCreateRequest(
        plan_id="plan-001",
        branch_humans=[
            TaskBranchHumanInputRequest(
                branch_id="missing",
                human=HumanInputSpec(summary="bad branch"),
            )
        ],
    )

    with pytest.raises(ValueError, match="unknown branch ids"):
        build_task_context(
            task_plan,
            context_request,
            task_context_id="task-context-001",
            created_at="2026-06-09 00:00:00",
        )
