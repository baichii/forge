"""Run 后台执行调度服务。"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from battle_planner.backend.config import backend_settings
from battle_planner.model import RunOutputSpec, TaskRunCreateRequest, TaskRunSpec
from battle_planner.orchestration.run_entropy import RunEntropy, RunEntropyError
from battle_planner.utils.run_store import LocalRunStore

from .run_task_registry import RUN_TASK_REGISTRY
from .task_run_service import TaskRunService

EXECUTOR = ThreadPoolExecutor(
    max_workers=backend_settings.EXECUTION_MAX_WORKERS,
    thread_name_prefix="battle-planner-run",
)


class RunExecutionService:
    """进程内后台执行 workflow。"""

    def __init__(
        self,
        store: LocalRunStore | None = None,
        task_run_service: TaskRunService | None = None,
    ):
        self.store = store or LocalRunStore(root_dir=backend_settings.RUNS_DIR)
        self.task_run_service = task_run_service or TaskRunService(store=self.store)

    def create_and_start_run(self, request: TaskRunCreateRequest) -> RunOutputSpec:
        """创建 run 并提交后台执行。"""

        task_run = self.task_run_service.create_task_run(request)
        RUN_TASK_REGISTRY.reserve(run_id=task_run.run_id)
        try:
            self.store.write_run_info(task_run=task_run)
            future = EXECUTOR.submit(self._execute_run, task_run.model_copy(deep=True))
            RUN_TASK_REGISTRY.attach_future(run_id=task_run.run_id, future=future)
        except Exception:
            RUN_TASK_REGISTRY.release(run_id=task_run.run_id)
            raise
        return self.store.read_run_output(run_id=task_run.run_id)

    def _execute_run(self, task_run: TaskRunSpec) -> None:
        start_time = time.monotonic()
        completed_iterations = 0
        try:
            run_entropy = RunEntropy(workflow_name=task_run.options.workflow_name or None)
            iteration_outputs = run_entropy.run_iterations(task_run)
            while True:
                if _is_timeout(start_time=start_time, timeout_seconds=task_run.options.timeout_seconds):
                    self.store.mark_run_failed(
                        run_id=task_run.run_id,
                        reason="timeout",
                        message="run exceeded timeout_seconds",
                        last_iteration_index=completed_iterations - 1 if completed_iterations > 0 else None,
                    )
                    return

                try:
                    iteration_output = next(iteration_outputs)
                except StopIteration:
                    break

                self.store.write_iteration_output(
                    run_id=task_run.run_id,
                    output=iteration_output,
                )
                completed_iterations += 1

            self.store.mark_run_completed(
                run_id=task_run.run_id,
                iteration_count=completed_iterations,
            )
        except RunEntropyError as exc:
            self.store.mark_run_failed(
                run_id=task_run.run_id,
                reason=exc.reason,
                message=exc.message,
                last_iteration_index=exc.last_iteration_index,
            )
        except Exception as exc:
            self.store.mark_run_failed(
                run_id=task_run.run_id,
                reason="workflow_exception",
                message=str(exc),
                last_iteration_index=completed_iterations - 1 if completed_iterations > 0 else None,
            )


def _is_timeout(*, start_time: float, timeout_seconds: int | None) -> bool:
    if timeout_seconds is None:
        return False
    return time.monotonic() - start_time >= timeout_seconds
