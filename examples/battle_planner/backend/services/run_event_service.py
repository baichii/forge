"""Run 事件通知服务。"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from battle_planner.backend.config import backend_settings
from battle_planner.model import RunOutputStatus
from battle_planner.utils.run_store import LocalRunStore
from fastapi import Request

TERMINAL_STATUSES: set[RunOutputStatus] = {"completed", "failed", "cancelled"}


class RunEventService:
    """基于本地 run 缓存轮询生成 SSE 通知。"""

    def __init__(self, store: LocalRunStore | None = None, poll_interval_seconds: float | None = None):
        self.store = store or LocalRunStore(root_dir=backend_settings.RUNS_DIR)
        self.poll_interval_seconds = (
            poll_interval_seconds
            if poll_interval_seconds is not None
            else backend_settings.EVENT_POLL_INTERVAL_SECONDS
        )

    async def iter_events(self, *, run_id: str, request: Request | None = None) -> AsyncIterator[dict]:
        """持续生成单个 run 的变化事件。"""

        seen_iterations = self._ready_iteration_indexes(run_id=run_id)
        seen_status = self.store.get_run_status(run_id=run_id)
        if seen_status in TERMINAL_STATUSES:
            yield self._sse_event(self._terminal_event(run_id=run_id, status=seen_status))
            return

        while True:
            if request is not None and await request.is_disconnected():
                return

            current_iterations = self._ready_iteration_indexes(run_id=run_id)
            for iteration_index in sorted(current_iterations - seen_iterations):
                yield self._sse_event(
                    {
                        "type": "iteration_ready",
                        "run_id": run_id,
                        "iteration_index": iteration_index,
                    }
                )
            seen_iterations = current_iterations

            current_status = self.store.get_run_status(run_id=run_id)
            if current_status != seen_status and current_status in TERMINAL_STATUSES:
                yield self._sse_event(self._terminal_event(run_id=run_id, status=current_status))
                return
            seen_status = current_status
            await asyncio.sleep(self.poll_interval_seconds)

    def _ready_iteration_indexes(self, *, run_id: str) -> set[int]:
        return {item.iteration_index for item in self.store.list_iteration_outputs(run_id=run_id)}

    def _terminal_event(self, *, run_id: str, status: RunOutputStatus) -> dict[str, Any]:
        marker = self.store.read_terminal_marker(run_id=run_id)
        event_type = "run_failed" if status == "failed" else f"run_{status}"
        return {
            "type": event_type,
            "run_id": run_id,
            "status": status,
            "reason": marker.get("reason", ""),
            "message": marker.get("message", ""),
        }

    def _sse_event(self, payload: dict[str, Any]) -> dict[str, str]:
        return {
            "event": payload["type"],
            "data": json.dumps(payload, ensure_ascii=False),
        }
