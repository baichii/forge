"""TaskContext 创建和缓存服务。"""

from __future__ import annotations

from battle_planner.backend.config import backend_settings
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
            meta=task_plan.meta,
        )
        self.store.write_task_context(task_context=task_context)
        return task_context

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
