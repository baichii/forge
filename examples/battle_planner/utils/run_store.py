"""本地 run 数据缓存工具。

Notes:
    当前只缓存每轮 RunIterationOutputSpec，供后续 backend 读取。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from battle_planner.conf import settings
from battle_planner.model import RunIterationOutputSpec, RunOutputStatus
from battle_planner.model.task import TaskRunSpec

TERMINAL_MARKERS = {
    "completed": "_COMPLETED",
    "failed": "_FAILED",
    "cancelled": "_CANCELLED",
}


class LocalRunStore:
    """按 run_id 缓存本地运行产物。"""

    def __init__(self, root_dir: Path | None = None):
        self.root_dir = root_dir or settings.RUNS_DIR

    def write_run_info(
        self,
        *,
        task_run: TaskRunSpec,
    ) -> Path:
        """缓存运行级基础信息。"""

        run_dir = self._run_dir(run_id=task_run.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        self._clear_terminal_markers(run_dir)
        run_path = run_dir / "run.json"
        run_path.write_text(
            json.dumps(_build_run_info(task_run), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return run_path

    def read_run_info(self, *, run_id: str) -> dict:
        """读取运行级基础信息。"""

        return json.loads((self._run_dir(run_id=run_id) / "run.json").read_text(encoding="utf-8"))

    def write_iteration_output(
        self,
        *,
        run_id: str,
        output: RunIterationOutputSpec,
    ) -> Path:
        """缓存单轮迭代输出。"""

        iteration_dir = self._iteration_dir(
            run_id=run_id,
            iteration_index=output.iteration_index,
        )
        iteration_dir.mkdir(parents=True, exist_ok=True)
        output_path = iteration_dir / "output.json"
        output_path.write_text(
            json.dumps(output.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (iteration_dir / "_READY").write_text("", encoding="utf-8")
        return output_path

    def read_iteration_output(
        self,
        *,
        run_id: str,
        iteration_index: int,
    ) -> RunIterationOutputSpec:
        """读取单轮迭代输出。"""

        output_path = (
            self._iteration_dir(
                run_id=run_id,
                iteration_index=iteration_index,
            )
            / "output.json"
        )
        return RunIterationOutputSpec.model_validate_json(output_path.read_text(encoding="utf-8"))

    def mark_run_completed(
        self,
        *,
        run_id: str,
        iteration_count: int | None = None,
    ) -> Path:
        """写入 run 成功终态 marker。"""

        return self._write_terminal_marker(
            run_id=run_id,
            status="completed",
            payload={
                "reason": "workflow_completed",
                "iteration_count": iteration_count,
            },
        )

    def mark_run_failed(
        self,
        *,
        run_id: str,
        reason: str = "workflow_error",
        message: str = "",
        last_iteration_index: int | None = None,
    ) -> Path:
        """写入 run 失败终态 marker。"""

        return self._write_terminal_marker(
            run_id=run_id,
            status="failed",
            payload={
                "reason": reason,
                "message": message,
                "last_iteration_index": last_iteration_index,
            },
        )

    def get_run_status(self, *, run_id: str) -> RunOutputStatus:
        """根据 marker 和 run.json 推导当前 run 状态。"""

        run_dir = self._run_dir(run_id=run_id)
        if (run_dir / TERMINAL_MARKERS["failed"]).exists():
            return "failed"
        if (run_dir / TERMINAL_MARKERS["cancelled"]).exists():
            return "cancelled"
        if (run_dir / TERMINAL_MARKERS["completed"]).exists():
            return "completed"
        if (run_dir / "run.json").exists():
            return "running"
        return "created"

    def _iteration_dir(self, *, run_id: str, iteration_index: int) -> Path:
        return self._run_dir(run_id=run_id) / "iterations" / str(iteration_index)

    def _run_dir(self, *, run_id: str) -> Path:
        return self.root_dir / run_id

    def _write_terminal_marker(
        self,
        *,
        run_id: str,
        status: RunOutputStatus,
        payload: dict[str, Any],
    ) -> Path:
        run_dir = self._run_dir(run_id=run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        self._clear_terminal_markers(run_dir)
        marker_path = run_dir / TERMINAL_MARKERS[status]
        marker_payload = {
            "status": status,
            "created_at": datetime.now().astimezone().isoformat(),
            **payload,
        }
        marker_path.write_text(
            json.dumps(marker_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return marker_path

    def _clear_terminal_markers(self, run_dir: Path) -> None:
        for marker_name in TERMINAL_MARKERS.values():
            marker_path = run_dir / marker_name
            if marker_path.exists():
                marker_path.unlink()


def _build_run_info(task_run: TaskRunSpec) -> dict:
    task_context = task_run.task_context
    return {
        "run_id": task_run.run_id,
        "run_name": task_run.run_name,
        "context_id": task_run.context_id,
        "context_name": task_context.name,
        "plan_id": task_run.plan_id,
        "plan_name": task_context.plan_name,
        "scenario_name": task_context.scenario_name,
        "objective": task_context.human.goal,
        "max_iterations": task_run.options.max_iterations,
        "meta": task_run.meta,
    }
