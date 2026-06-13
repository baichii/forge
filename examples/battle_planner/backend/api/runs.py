"""Run 查询和事件通知接口。"""

from __future__ import annotations

from battle_planner.backend.services.run_event_service import RunEventService
from battle_planner.backend.services.run_execution_service import RunExecutionService
from battle_planner.backend.services.run_query_service import RunQueryService
from battle_planner.backend.services.run_task_registry import RunCapacityExceeded
from battle_planner.model import RunIterationOutputSpec, RunOutputSpec, TaskRunCreateRequest
from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/battle-planner/runs", tags=["battle-planner-runs"])


def _query_service() -> RunQueryService:
    return RunQueryService()


def _event_service() -> RunEventService:
    return RunEventService()


def _execution_service() -> RunExecutionService:
    return RunExecutionService()


@router.post("", response_model=RunOutputSpec)
def create_run(request: TaskRunCreateRequest) -> RunOutputSpec:
    """创建 run 并提交后台执行。"""

    try:
        return _execution_service().create_and_start_run(request)
    except RunCapacityExceeded as exc:
        raise HTTPException(status_code=429, detail=exc.to_detail()) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Context not found: {request.context_id}") from exc


@router.get("")
def list_runs() -> list[dict]:
    """列出本地 run 缓存。"""

    return _query_service().list_runs()


@router.get("/{run_id}", response_model=RunOutputSpec)
def get_run_output(run_id: str) -> RunOutputSpec:
    """获取 run 完整输出快照。"""

    try:
        return _query_service().get_run_output(run_id=run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}") from exc


@router.get("/{run_id}/iterations/{iteration_index}", response_model=RunIterationOutputSpec)
def get_iteration_output(run_id: str, iteration_index: int) -> RunIterationOutputSpec:
    """获取单轮迭代输出。"""

    try:
        return _query_service().get_iteration_output(
            run_id=run_id,
            iteration_index=iteration_index,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Iteration not found: {run_id}/{iteration_index}",
        ) from exc


@router.get("/{run_id}/events")
async def stream_run_events(request: Request, run_id: str) -> EventSourceResponse:
    """订阅 run 变化通知。"""

    try:
        _query_service().get_run_info(run_id=run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}") from exc
    return EventSourceResponse(_event_service().iter_events(run_id=run_id, request=request))
