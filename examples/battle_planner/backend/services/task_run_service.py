"""TaskRun 创建服务。"""

from __future__ import annotations

from battle_planner.backend.config import backend_settings
from battle_planner.model import TaskRunCreateRequest, TaskRunSpec
from battle_planner.utils.run_store import LocalRunStore
from battle_planner.utils.snowflake import snowflake


class TaskRunService:
    """将外部 run request 转为内部 TaskRunSpec。"""

    def __init__(self, store: LocalRunStore | None = None):
        self.store = store or LocalRunStore(root_dir=backend_settings.RUNS_DIR)

    def create_task_run(self, request: TaskRunCreateRequest) -> TaskRunSpec:
        """创建内部 TaskRunSpec。"""

        task_context = self.store.read_task_context(context_id=request.context_id)
        run_id = str(snowflake.generate())
        return TaskRunSpec(
            run_id=run_id,
            context_id=task_context.context_id,
            plan_id=task_context.plan_id,
            run_name=request.run_name or f"battle-planner-run-{run_id}",
            task_context=task_context,
            options=request.options.model_copy(deep=True),
        )
