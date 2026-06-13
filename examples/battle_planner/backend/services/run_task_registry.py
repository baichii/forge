"""Run 后台任务登记表。"""

from __future__ import annotations

from concurrent.futures import Future
from threading import Lock

from battle_planner.backend.config import backend_settings


class RunCapacityExceeded(RuntimeError):
    """运行中任务数量超过 backend 容量。"""

    def __init__(self, *, active_runs: int, max_active_runs: int):
        self.active_runs = active_runs
        self.max_active_runs = max_active_runs
        super().__init__("run execution capacity exceeded")

    def to_detail(self) -> dict:
        """转换为接口错误详情。"""

        return {
            "code": "run_capacity_exceeded",
            "message": "当前推演任务已满，请稍后再试。",
            "active_runs": self.active_runs,
            "max_active_runs": self.max_active_runs,
        }


class RunTaskRegistry:
    """记录当前 backend 进程内正在执行的 run。"""

    def __init__(self):
        self._active_runs: dict[str, Future | None] = {}
        self._lock = Lock()

    def reserve(self, *, run_id: str) -> None:
        """为 run 占用一个执行名额。"""

        with self._lock:
            self._prune_done_locked()
            active_runs = len(self._active_runs)
            max_active_runs = backend_settings.EXECUTION_MAX_ACTIVE_RUNS
            if active_runs >= max_active_runs:
                raise RunCapacityExceeded(
                    active_runs=active_runs,
                    max_active_runs=max_active_runs,
                )
            self._active_runs[run_id] = None

    def attach_future(self, *, run_id: str, future: Future) -> None:
        """绑定后台执行 future，完成后自动释放名额。"""

        with self._lock:
            self._active_runs[run_id] = future
        future.add_done_callback(lambda _future: self.release(run_id=run_id))

    def release(self, *, run_id: str) -> None:
        """释放 run 执行名额。"""

        with self._lock:
            self._active_runs.pop(run_id, None)

    def active_count(self) -> int:
        """返回当前运行中任务数量。"""

        with self._lock:
            self._prune_done_locked()
            return len(self._active_runs)

    def _prune_done_locked(self) -> None:
        done_run_ids = [
            run_id for run_id, future in self._active_runs.items() if future is not None and future.done()
        ]
        for run_id in done_run_ids:
            self._active_runs.pop(run_id, None)


RUN_TASK_REGISTRY = RunTaskRegistry()
