"""TaskPlan -> TaskContext -> TaskRun 的核心实体和转换函数。"""

from __future__ import annotations

from typing import Any, Literal

from battle_planner.conf import settings
from battle_planner.model.requests import (
    TaskBranchHumanInputRequest,
    TaskContextCreateRequest,
    TaskRunCreateRequest,
)
from battle_planner.model.source import TaskPlanSpec
from battle_planner.model.workflow import HumanInputSpec
from pydantic import BaseModel, Field


class TaskRunOptions(BaseModel):
    """一次完整策略迭代运行的配置。"""

    workflow_name: str = Field(default=settings.WORKFLOW_NAME, description="要构建的 workflow 名称。")
    max_iterations: int = Field(default=5, description="最大迭代轮数。")
    sim_runs_per_scheme: int = Field(default=1, description="每版方案的仿真次数。")
    max_retry: int = Field(default=1, description="最大重试次数。")
    timeout_seconds: int | None = Field(default=None, description="运行超时时间，单位秒。")
    extra: dict[str, Any] = Field(default_factory=dict, description="workflow 对外暴露的其他约束配置。")


class TaskContextSpec(BaseModel):
    """任务上下文，作为 LLM 策略迭代的输入上下文。"""

    task_context_id: str = Field(description="任务上下文唯一 ID。")
    plan_id: str = Field(description="来源任务方案 ID。")
    name: str = Field(default="", description="任务上下文名称。")
    plan_snapshot: TaskPlanSpec = Field(description="创建上下文时的任务方案快照。")
    plan_human: HumanInputSpec = Field(default_factory=HumanInputSpec, description="任务方案层人工输入。")
    branch_humans: list[TaskBranchHumanInputRequest] = Field(
        default_factory=list, description="任务分支人工输入。"
    )
    created_at: str = Field(description="创建时间。")
    meta: dict[str, Any] = Field(default_factory=dict, description="任务上下文元信息，预留字段。")


class TaskRunSpec(BaseModel):
    """一次完整策略迭代运行。"""

    run_id: str = Field(description="任务运行唯一 ID。")
    task_context_id: str = Field(description="任务上下文 ID。")
    plan_id: str = Field(description="来源任务方案 ID。")
    task_context_snapshot: TaskContextSpec = Field(description="创建运行时的任务上下文快照。")
    options: TaskRunOptions = Field(default_factory=TaskRunOptions, description="运行配置。")
    status: Literal["created", "running", "completed", "failed"] = Field(
        default="created", description="任务运行状态。"
    )
    created_at: str = Field(description="创建时间。")
    updated_at: str | None = Field(default=None, description="更新时间。")
    meta: dict[str, Any] = Field(default_factory=dict, description="任务运行元信息，预留字段。")


def build_task_context(
    plan: TaskPlanSpec,
    request: TaskContextCreateRequest,
    *,
    task_context_id: str,
    created_at: str,
) -> TaskContextSpec:
    """由任务方案和人工输入请求构建任务上下文。"""

    if request.plan_id != plan.plan_id:
        raise ValueError(f"request plan_id={request.plan_id!r} does not match plan_id={plan.plan_id!r}")

    plan_branch_ids = {branch.branch_id for branch in plan.branches}
    unknown_branch_ids = [
        item.branch_id for item in request.branch_humans if item.branch_id not in plan_branch_ids
    ]
    if unknown_branch_ids:
        raise ValueError(f"unknown branch ids for plan {plan.plan_id}: {unknown_branch_ids}")

    return TaskContextSpec(
        task_context_id=task_context_id,
        plan_id=plan.plan_id,
        name=request.name or plan.name,
        plan_snapshot=plan,
        plan_human=request.plan_human,
        branch_humans=request.branch_humans,
        created_at=created_at,
        meta={"raw_payload": request.raw_payload} if request.raw_payload else {},
    )


def build_task_run(
    context: TaskContextSpec,
    request: TaskRunCreateRequest,
    *,
    run_id: str,
    created_at: str,
) -> TaskRunSpec:
    """由任务上下文和运行请求构建任务运行。"""

    if request.task_context_id != context.task_context_id:
        raise ValueError(
            f"request task_context_id={request.task_context_id!r} does not match "
            f"task_context_id={context.task_context_id!r}"
        )

    return TaskRunSpec(
        run_id=run_id,
        task_context_id=context.task_context_id,
        plan_id=context.plan_id,
        task_context_snapshot=context,
        options=TaskRunOptions.model_validate(request.options),
        created_at=created_at,
        meta={
            key: value
            for key, value in {
                "run_name": request.run_name,
                "raw_payload": request.raw_payload,
            }.items()
            if value
        },
    )
