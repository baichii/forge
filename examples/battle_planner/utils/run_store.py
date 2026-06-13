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
from battle_planner.model import (
    RunIterationOutputSpec,
    RunOutputSpec,
    RunOutputStatus,
    TaskContextSpec,
)
from battle_planner.model.task import TaskRunSpec

TERMINAL_MARKERS = {
    "completed": "_COMPLETED",
    "failed": "_FAILED",
    "cancelled": "_CANCELLED",
}
TASK_CONTEXTS_DIR_NAME = "task_contexts"
TASK_RUNS_DIR_NAME = "task_runs"


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
        task_run_meta = _with_created_at(task_run.meta)
        task_run_payload = task_run.model_dump(mode="json")
        task_run_payload["meta"] = task_run_meta
        run_path.write_text(
            json.dumps(_build_run_info(task_run, meta=task_run_meta), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        input_dir = run_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        (input_dir / "context.json").write_text(
            json.dumps(task_run.task_context.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (input_dir / "task_run.json").write_text(
            json.dumps(task_run_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return run_path

    def read_run_info(self, *, run_id: str) -> dict:
        """读取运行级基础信息。"""

        return json.loads((self._run_dir(run_id=run_id) / "run.json").read_text(encoding="utf-8"))

    def write_task_context(self, *, task_context: TaskContextSpec) -> Path:
        """缓存任务上下文。"""

        context_dir = self._context_dir(context_id=task_context.context_id)
        context_dir.mkdir(parents=True, exist_ok=True)
        context_path = context_dir / "context.json"
        context_payload = task_context.model_dump(mode="json")
        context_payload["meta"] = _with_created_at(context_payload.get("meta"))
        context_path.write_text(
            json.dumps(context_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return context_path

    def read_task_context(self, *, context_id: str) -> TaskContextSpec:
        """读取任务上下文。"""

        context_path = self._context_dir(context_id=context_id) / "context.json"
        return TaskContextSpec.model_validate_json(context_path.read_text(encoding="utf-8"))

    def list_task_contexts(self) -> list[TaskContextSpec]:
        """列出本地已保存的任务上下文。"""

        task_contexts_dir = self.root_dir / TASK_CONTEXTS_DIR_NAME
        if not task_contexts_dir.exists():
            return []

        contexts: list[TaskContextSpec] = []
        for context_dir in sorted(item for item in task_contexts_dir.iterdir() if item.is_dir()):
            context_path = context_dir / "context.json"
            if not context_path.exists():
                continue
            task_context = TaskContextSpec.model_validate_json(context_path.read_text(encoding="utf-8"))
            contexts.append(task_context)
        return sorted(contexts, key=lambda item: _created_at_from_meta(item.meta), reverse=True)

    def list_runs(self) -> list[dict[str, Any]]:
        """列出本地已缓存的 run 基础信息。"""

        task_runs_dir = self._task_runs_dir()
        if not task_runs_dir.exists():
            return []

        runs: list[dict[str, Any]] = []
        for run_dir in sorted(item for item in task_runs_dir.iterdir() if item.is_dir()):
            run_path = run_dir / "run.json"
            if not run_path.exists():
                continue
            run_id = run_dir.name
            run_info = json.loads(run_path.read_text(encoding="utf-8"))
            runs.append(
                {
                    **run_info,
                    "status": self.get_run_status(run_id=run_id),
                    "iteration_count": len(self.list_iteration_outputs(run_id=run_id)),
                }
            )
        return sorted(runs, key=lambda item: str(item.get("created_at", "")), reverse=True)

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

    def list_iteration_outputs(self, *, run_id: str) -> list[RunIterationOutputSpec]:
        """读取某个 run 下所有已完成写入的轮次输出。"""

        iterations_dir = self._run_dir(run_id=run_id) / "iterations"
        if not iterations_dir.exists():
            return []

        outputs: list[RunIterationOutputSpec] = []
        for iteration_dir in sorted(
            (item for item in iterations_dir.iterdir() if item.is_dir() and item.name.isdigit()),
            key=lambda item: int(item.name),
        ):
            if not (iteration_dir / "_READY").exists():
                continue
            outputs.append(
                self.read_iteration_output(
                    run_id=run_id,
                    iteration_index=int(iteration_dir.name),
                )
            )
        return outputs

    def read_run_output(self, *, run_id: str) -> RunOutputSpec:
        """组装某个 run 的完整查询快照。"""

        run_info = self.read_run_info(run_id=run_id)
        return RunOutputSpec(
            **run_info,
            status=self.get_run_status(run_id=run_id),
            iterations=self.list_iteration_outputs(run_id=run_id),
        )

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

    def read_terminal_marker(self, *, run_id: str) -> dict[str, Any]:
        """读取 run 终态 marker 信息。"""

        run_dir = self._run_dir(run_id=run_id)
        for status in ("failed", "cancelled", "completed"):
            marker_path = run_dir / TERMINAL_MARKERS[status]
            if marker_path.exists():
                return json.loads(marker_path.read_text(encoding="utf-8"))
        return {}

    def _iteration_dir(self, *, run_id: str, iteration_index: int) -> Path:
        return self._run_dir(run_id=run_id) / "iterations" / str(iteration_index)

    def _run_dir(self, *, run_id: str) -> Path:
        return self._task_runs_dir() / run_id

    def _context_dir(self, *, context_id: str) -> Path:
        return self.root_dir / TASK_CONTEXTS_DIR_NAME / context_id

    def _task_runs_dir(self) -> Path:
        return self.root_dir / TASK_RUNS_DIR_NAME

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


def _build_run_info(task_run: TaskRunSpec, *, meta: dict[str, Any] | None = None) -> dict:
    task_context = task_run.task_context
    meta = _with_created_at(meta if meta is not None else task_run.meta)
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
        "created_at": meta["created_at"],
        "meta": meta,
    }


def _with_created_at(meta: Any) -> dict[str, Any]:
    payload = dict(meta) if isinstance(meta, dict) else {}
    if not payload.get("created_at"):
        payload["created_at"] = _now_iso()
    return payload


def _created_at_from_meta(meta: Any) -> str:
    return str(meta.get("created_at", "")) if isinstance(meta, dict) else ""


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat()
