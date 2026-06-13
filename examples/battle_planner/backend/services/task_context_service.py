"""TaskContext 创建和缓存服务。"""

from __future__ import annotations

from datetime import datetime

from battle_planner.backend.config import backend_settings
from battle_planner.backend.schemas import TaskContextListItemView
from battle_planner.model import (
    BranchHumanInputSpec,
    TaskBranchContextSpec,
    TaskContextCreateRequest,
    TaskContextSpec,
)
from battle_planner.utils.run_store import LocalRunStore
from battle_planner.utils.snowflake import snowflake
from battle_planner.workspace.local.loaders import load_task_plan_config_by_plan_id


class TaskContextService:
    """将外部 context request 转为内部 TaskContextSpec。"""

    def __init__(self, store: LocalRunStore | None = None):
        self.store = store or LocalRunStore(root_dir=backend_settings.RUNS_DIR)

    def create_context(self, request: TaskContextCreateRequest) -> TaskContextSpec:
        """创建并缓存任务上下文。"""

        task_plan = load_task_plan_config_by_plan_id(request.plan_id)
        branch_human_by_id = _branch_human_by_id(request)
        selected_branch_ids = list(branch_human_by_id) or [
            branch.branch_id for branch in task_plan.branches
        ]
        branch_by_id = {branch.branch_id: branch for branch in task_plan.branches}
        unknown_branch_ids = [
            branch_id for branch_id in selected_branch_ids if branch_id not in branch_by_id
        ]
        if unknown_branch_ids:
            raise ValueError(f"unknown branch ids for plan {task_plan.plan_id}: {unknown_branch_ids}")

        plan_human = request.plan_human.model_copy(deep=True)
        if not plan_human.goal:
            plan_human.goal = task_plan.objective
        if not plan_human.constraints:
            plan_human.constraints = list(task_plan.constraints)

        task_context = TaskContextSpec(
            context_id=str(snowflake.generate()),
            plan_id=task_plan.plan_id,
            name=request.name or task_plan.name,
            plan_name=task_plan.name,
            scenario_name=task_plan.scenario_name,
            side=task_plan.side,
            opponent_side=task_plan.opponent_side,
            human=plan_human,
            branches=[
                TaskBranchContextSpec(
                    branch_id=branch_id,
                    name=branch_by_id[branch_id].name,
                    description=branch_by_id[branch_id].description,
                    human=branch_human_by_id.get(branch_id, BranchHumanInputSpec()),
                    meta=branch_by_id[branch_id].meta,
                )
                for branch_id in selected_branch_ids
            ],
            meta=_with_created_at(task_plan.meta),
        )
        self.store.write_task_context(task_context=task_context)
        return task_context

    def list_contexts(self) -> list[TaskContextListItemView]:
        """列出已保存的任务上下文。"""

        return [_build_context_list_item(task_context) for task_context in self.store.list_task_contexts()]

    def get_context(self, *, context_id: str) -> TaskContextSpec:
        """读取任务上下文。"""

        return self.store.read_task_context(context_id=context_id)


def _branch_human_by_id(request: TaskContextCreateRequest) -> dict[int, BranchHumanInputSpec]:
    branch_human_by_id: dict[int, BranchHumanInputSpec] = {}
    for item in request.branch_humans:
        if item.branch_id in branch_human_by_id:
            raise ValueError(f"duplicated branch id: {item.branch_id}")
        branch_human_by_id[item.branch_id] = item.human
    return branch_human_by_id


def _with_created_at(meta: dict | None) -> dict:
    payload = dict(meta) if isinstance(meta, dict) else {}
    if not payload.get("created_at"):
        payload["created_at"] = datetime.now().astimezone().isoformat()
    return payload


def _build_context_list_item(task_context: TaskContextSpec) -> TaskContextListItemView:
    meta = task_context.meta if isinstance(task_context.meta, dict) else {}
    return TaskContextListItemView(
        context_id=task_context.context_id,
        name=task_context.name,
        plan_id=task_context.plan_id,
        plan_name=task_context.plan_name,
        scenario_name=task_context.scenario_name,
        branch_count=len(task_context.branches),
        created_at=str(meta.get("created_at", "")),
    )
