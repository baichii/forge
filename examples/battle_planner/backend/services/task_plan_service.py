"""TaskPlan 查询服务。"""

from __future__ import annotations

from battle_planner.model import TaskPlanSpec
from battle_planner.workspace.local.loaders import (
    load_task_plan_config_by_plan_id,
    load_task_plan_configs,
)


class TaskPlanService:
    """读取本地只读任务方案。"""

    def list_plans(self) -> list[TaskPlanSpec]:
        """列出所有本地任务方案。"""

        return load_task_plan_configs()

    def get_plan(self, *, plan_id: str) -> TaskPlanSpec:
        """读取具体任务方案。"""

        return load_task_plan_config_by_plan_id(plan_id)
