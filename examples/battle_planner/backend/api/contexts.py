"""TaskContext 创建和查询接口。"""

from __future__ import annotations

from battle_planner.backend.services.task_context_service import TaskContextService
from battle_planner.model import TaskContextCreateRequest, TaskContextSpec
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/battle-planner/contexts", tags=["battle-planner-contexts"])


def _context_service() -> TaskContextService:
    return TaskContextService()


@router.post("", response_model=TaskContextSpec)
def create_context(request: TaskContextCreateRequest) -> TaskContextSpec:
    """创建任务上下文。"""

    try:
        return _context_service().create_context(request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{context_id}", response_model=TaskContextSpec)
def get_context(context_id: str) -> TaskContextSpec:
    """读取任务上下文。"""

    try:
        return _context_service().get_context(context_id=context_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Context not found: {context_id}") from exc
