"""Local demo seed and builders for battle planner development."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from battle_planner.model.requests import (
    TaskBranchHumanInputRequest,
    TaskContextCreateRequest,
    TaskRunCreateRequest,
)
from battle_planner.model.source import TaskPlanSpec
from battle_planner.model.task import (
    TaskContextSpec,
    TaskRunSpec,
    build_task_context,
    build_task_run,
)
from battle_planner.model.workflow import HumanInputSpec
from battle_planner.workspace.local.loaders import load_task_plan_config
from pydantic import BaseModel, Field


class LocalBranchDemoSeed(BaseModel):
    """Local human input for one task branch."""

    branch_id: int = Field(description="任务方案内的分支 ID。")
    human: HumanInputSpec = Field(default_factory=HumanInputSpec, description="分支人工输入。")


class LocalDemoSeed(BaseModel):
    """Stable local development data used to assemble demo workflow inputs."""

    plan_name: str = Field(default="zc3_lite_carrier_validation")
    plan_id: str = Field(default="2175600675558391808")
    default_branch_ids: tuple[int, ...] = Field(default=(1, 2))
    context_id: str = Field(default="2175600675558391809")
    run_id: str = Field(default="2175600675558391810")
    context_name: str = Field(default="航母对抗任务上下文001")
    run_name: str = Field(default="航母对抗策略迭代运行001")
    plan_human: HumanInputSpec = Field(
        default_factory=lambda: HumanInputSpec(
            summary="人工希望先验证任务方案、策略迭代和推演配置的数据链路。",
            items=[
                "当前只保留一个策略分支，不考虑备选方案对比。",
                "只评价该策略是否完成摧毁航母目标。",
            ],
        )
    )
    branch_humans: list[LocalBranchDemoSeed] = Field(
        default_factory=lambda: [
            LocalBranchDemoSeed(
                branch_id=1,
                human=HumanInputSpec(
                    summary="人工确认本轮保留空中突击与海对海打击分支。",
                    items=[
                        "不要同时优化对手策略。",
                        "武器数量先保守，后续根据仿真反馈调整。",
                    ],
                ),
            ),
            LocalBranchDemoSeed(
                branch_id=2,
                human=HumanInputSpec(
                    summary="人工希望保留潜艇隐蔽打击分支用于能力缺口验证。",
                    items=[
                        "当前只要求方案卡片和人工输入可进入数据链路。",
                        "如果本地没有匹配 tick-agent，后续运行阶段应给出提示或跳过。",
                    ],
                ),
            ),
        ]
    )
    run_options: dict[str, Any] = Field(
        default_factory=lambda: {
            "workflow_name": "zc_lite_baseline",
            "max_iterations": 5,
            "sim_runs_per_scheme": 1,
            "max_retry": 1,
            "timeout_seconds": None,
            "extra": {},
        }
    )


LOCAL_DEMO_SEED = LocalDemoSeed()


def _resolve_branch_ids(
    seed: LocalDemoSeed,
    branch_ids: Sequence[int] | None,
) -> tuple[int, ...]:
    return tuple(branch_ids) if branch_ids is not None else seed.default_branch_ids


def _validate_branch_ids(
    *,
    seed: LocalDemoSeed,
    task_plan: TaskPlanSpec,
    branch_ids: Sequence[int],
) -> None:
    plan_branch_ids = {branch.branch_id for branch in task_plan.branches}
    seed_branch_ids = {item.branch_id for item in seed.branch_humans}
    unknown_plan_branch_ids = [branch_id for branch_id in branch_ids if branch_id not in plan_branch_ids]
    unknown_seed_branch_ids = [branch_id for branch_id in branch_ids if branch_id not in seed_branch_ids]
    if unknown_plan_branch_ids:
        raise ValueError(
            f"local branch ids {unknown_plan_branch_ids!r} do not exist in fixture {seed.plan_name!r}"
        )
    if unknown_seed_branch_ids:
        raise ValueError(f"local branch ids {unknown_seed_branch_ids!r} do not have demo human input")


def build_local_task_plan(
    seed: LocalDemoSeed = LOCAL_DEMO_SEED,
    *,
    branch_ids: Sequence[int] | None = None,
) -> TaskPlanSpec:
    """Build the local source TaskPlan from the workspace fixture."""

    task_plan = load_task_plan_config(seed.plan_name)
    if task_plan.plan_id != seed.plan_id:
        raise ValueError(
            f"local seed plan_id={seed.plan_id!r} does not match fixture plan_id={task_plan.plan_id!r}"
        )
    _validate_branch_ids(seed=seed, task_plan=task_plan, branch_ids=_resolve_branch_ids(seed, branch_ids))
    return task_plan


def build_local_task_context_request(
    seed: LocalDemoSeed = LOCAL_DEMO_SEED,
    *,
    branch_ids: Sequence[int] | None = None,
) -> TaskContextCreateRequest:
    """Build the local request that creates a TaskContext."""

    task_plan = build_local_task_plan(seed, branch_ids=branch_ids)
    selected_branch_ids = _resolve_branch_ids(seed, branch_ids)
    branch_humans_by_id = {item.branch_id: item.human for item in seed.branch_humans}
    return TaskContextCreateRequest(
        plan_id=task_plan.plan_id,
        name=seed.context_name,
        plan_human=seed.plan_human,
        branch_humans=[
            TaskBranchHumanInputRequest(
                branch_id=branch_id,
                human=branch_humans_by_id[branch_id],
            )
            for branch_id in selected_branch_ids
        ],
    )


def build_local_task_context(
    seed: LocalDemoSeed = LOCAL_DEMO_SEED,
    *,
    branch_ids: Sequence[int] | None = None,
) -> TaskContextSpec:
    """Build the local TaskContext from the local TaskPlan and request."""

    return build_task_context(
        build_local_task_plan(seed, branch_ids=branch_ids),
        build_local_task_context_request(seed, branch_ids=branch_ids),
        context_id=seed.context_id,
    )


def build_local_task_run_request(seed: LocalDemoSeed = LOCAL_DEMO_SEED) -> TaskRunCreateRequest:
    """Build the local request that creates a TaskRun."""

    return TaskRunCreateRequest(
        context_id=seed.context_id,
        run_name=seed.run_name,
        options=seed.run_options,
    )


def build_local_task_run(
    seed: LocalDemoSeed = LOCAL_DEMO_SEED,
    *,
    branch_ids: Sequence[int] | None = None,
) -> TaskRunSpec:
    """Build the local workflow entry TaskRun."""

    return build_task_run(
        build_local_task_context(seed, branch_ids=branch_ids),
        build_local_task_run_request(seed),
        run_id=seed.run_id,
    )
