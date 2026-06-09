"""Local demo seed and builders for battle planner development."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from battle_planner.model.human import BranchHumanInputSpec, PlanHumanInputSpec
from battle_planner.model.requests import (
    TaskBranchHumanInputRequest,
    TaskContextCreateRequest,
    TaskRunCreateRequest,
)
from battle_planner.model.source import TaskPlanSpec
from battle_planner.model.task import (
    TaskBranchContextSpec,
    TaskContextSpec,
    TaskRunOptions,
    TaskRunSpec,
)
from battle_planner.workspace.local.loaders import load_task_plan_config
from pydantic import BaseModel, Field


class LocalBranchDemoSeed(BaseModel):
    """Local human input for one task branch."""

    branch_id: int = Field(description="任务方案内的分支 ID。")
    human: BranchHumanInputSpec = Field(default_factory=BranchHumanInputSpec, description="分支人工输入。")


class LocalDemoSeed(BaseModel):
    """Stable local development data used to assemble demo workflow inputs."""

    plan_name: str = Field(default="zc3_lite_carrier_validation")
    plan_id: str = Field(default="2175600675558391808")
    default_branch_ids: tuple[int, ...] = Field(default=(1, 2))
    context_id: str = Field(default="2175600675558391809")
    run_id: str = Field(default="2175600675558391810")
    context_name: str = Field(default="航母对抗任务上下文001")
    run_name: str = Field(default="航母对抗策略迭代运行001")
    plan_human: PlanHumanInputSpec = Field(
        default_factory=lambda: PlanHumanInputSpec(
            goal="先验证任务方案、策略迭代和推演配置的数据链路。",
            constraints=[
                "当前只使用本地任务方案和本地 tick-agent 资源。",
                "优先保证 workflow 输入结构稳定，暂不追求复杂业务覆盖。",
            ],
            risk_points=[
                "分支能力可能与本地 tick-agent 库不完全匹配。",
                "仿真结果先用于链路验证，不作为最终业务评估结论。",
            ],
            notes="时间窗、偏好打法等不确定信息暂时在备注中保留。",
        )
    )
    branch_humans: list[LocalBranchDemoSeed] = Field(
        default_factory=lambda: [
            LocalBranchDemoSeed(
                branch_id=1,
                human=BranchHumanInputSpec(
                    goal="验证空中突击与海对海打击分支能否完成航母毁伤目标。",
                    constraints=[
                        "不要同时优化对手策略。",
                        "武器数量先保守，后续根据仿真反馈调整。",
                    ],
                    risk_points=[
                        "空中突击窗口过短时可能导致毁伤不足。",
                        "舰艇补充打击可能增加我方暴露风险。",
                    ],
                    notes="优先跑通空中突击压制后由舰艇编队补充打击的主链路。",
                ),
            ),
            LocalBranchDemoSeed(
                branch_id=2,
                human=BranchHumanInputSpec(
                    goal="保留潜艇隐蔽打击分支用于能力缺口验证。",
                    constraints=[
                        "当前只要求方案卡片和人工输入可进入数据链路。",
                        "如果本地没有匹配 tick-agent，后续运行阶段应给出提示或跳过。",
                    ],
                    risk_points=[
                        "潜艇分支可能暂时缺少可用 tick-agent。",
                        "能力缺口不应阻断其他可运行分支。",
                    ],
                    notes="该分支用于测试业务方案存在但本地能力暂不完整的情况。",
                ),
            ),
        ]
    )
    run_options: TaskRunOptions = Field(
        default_factory=lambda: TaskRunOptions(
            workflow_name="zc_lite_baseline",
            max_iterations=5,
            sim_runs_per_scheme=1,
            max_retry=1,
            timeout_seconds=None,
            extra={},
        )
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
    """生成本地 TaskPlan。

    Args:
        seed: 本地测试数据。
        branch_ids: 需要校验的分支 ID；不传时使用默认分支。
    """

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
    """生成创建 TaskContext 的本地请求。

    Args:
        seed: 本地测试数据和人工输入。
        branch_ids: 要生成人工输入的分支 ID；不传时使用默认分支。
    """

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
    """生成本地 TaskContext。

    Args:
        seed: 本地测试数据。
        branch_ids: 进入上下文的分支 ID；不传时使用默认分支。
    """

    task_plan = build_local_task_plan(seed, branch_ids=branch_ids)
    request = build_local_task_context_request(seed, branch_ids=branch_ids)
    if request.plan_id != task_plan.plan_id:
        raise ValueError(
            f"request plan_id={request.plan_id!r} does not match plan_id={task_plan.plan_id!r}"
        )

    branch_by_id = {branch.branch_id: branch for branch in task_plan.branches}
    plan_branch_ids = set(branch_by_id)
    unknown_branch_ids = [
        item.branch_id for item in request.branch_humans if item.branch_id not in plan_branch_ids
    ]
    if unknown_branch_ids:
        raise ValueError(f"unknown branch ids for plan {task_plan.plan_id}: {unknown_branch_ids}")
    branch_human_by_id = {item.branch_id: item.human for item in request.branch_humans}

    return TaskContextSpec(
        context_id=seed.context_id,
        plan_id=task_plan.plan_id,
        name=request.name or task_plan.name,
        plan_name=task_plan.name,
        scenario_name=task_plan.scenario_name,
        side=task_plan.side,
        opponent_side=task_plan.opponent_side,
        human=request.plan_human,
        branches=[
            TaskBranchContextSpec(
                branch_id=branch_id,
                name=branch_by_id[branch_id].name,
                description=branch_by_id[branch_id].description,
                human=branch_human_by_id[branch_id],
                meta=branch_by_id[branch_id].meta,
            )
            for branch_id in branch_human_by_id
        ],
        meta=task_plan.meta,
    )


def build_local_task_run_request(seed: LocalDemoSeed = LOCAL_DEMO_SEED) -> TaskRunCreateRequest:
    """生成创建 TaskRun 的本地请求。

    Args:
        seed: 提供 context_id、run_name 和运行参数的本地测试数据。
    """

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
    """生成 workflow 可直接使用的本地 TaskRun。

    Args:
        seed: 本地测试数据。
        branch_ids: 本次运行包含的分支 ID；不传时使用默认分支。
    """

    task_context = build_local_task_context(seed, branch_ids=branch_ids)
    request = build_local_task_run_request(seed)
    if request.context_id != task_context.context_id:
        raise ValueError(
            f"request context_id={request.context_id!r} does not match context_id={task_context.context_id!r}"
        )

    return TaskRunSpec(
        run_id=seed.run_id,
        context_id=task_context.context_id,
        plan_id=task_context.plan_id,
        run_name=request.run_name,
        task_context=task_context,
        options=request.options,
    )
