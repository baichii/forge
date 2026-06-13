"""TaskPlan 查询接口。"""

from __future__ import annotations

from battle_planner.backend.services.task_plan_service import TaskPlanService
from battle_planner.model import TaskPlanSpec
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/battle-planner/plans", tags=["battle-planner-plans"])


def _plan_service() -> TaskPlanService:
    return TaskPlanService()


@router.get("", response_model=list[TaskPlanSpec])
def list_plans() -> list[TaskPlanSpec]:
    """列出本地任务方案。"""

    return _plan_service().list_plans()


@router.get("/{plan_id}", response_model=TaskPlanSpec)
def get_plan(plan_id: str) -> TaskPlanSpec:
    """读取具体任务方案。"""

    try:
        return _plan_service().get_plan(plan_id=plan_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}") from exc
