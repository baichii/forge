"""Run 查询服务。"""

from __future__ import annotations

from battle_planner.backend.config import backend_settings
from battle_planner.model import RunIterationOutputSpec, RunOutputSpec
from battle_planner.utils.run_store import LocalRunStore


class RunQueryService:
    """封装 run 缓存读取和快照组装。"""

    def __init__(self, store: LocalRunStore | None = None):
        self.store = store or LocalRunStore(root_dir=backend_settings.RUNS_DIR)

    def list_runs(self) -> list[dict]:
        """列出本地 run 缓存。"""

        return self.store.list_runs()

    def get_run_info(self, *, run_id: str) -> dict:
        """读取 run 基础信息。"""

        return self.store.read_run_info(run_id=run_id)

    def get_run_output(self, *, run_id: str) -> RunOutputSpec:
        """读取 run 完整输出快照。"""

        return self.store.read_run_output(run_id=run_id)

    def get_iteration_output(
        self,
        *,
        run_id: str,
        iteration_index: int,
    ) -> RunIterationOutputSpec:
        """读取单轮迭代输出。"""

        for output in self.store.list_iteration_outputs(run_id=run_id):
            if output.iteration_index == iteration_index:
                return output
        raise FileNotFoundError(f"Iteration not ready: {run_id}/{iteration_index}")
