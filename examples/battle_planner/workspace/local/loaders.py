from __future__ import annotations

from pathlib import Path

from battle_planner.model import TaskPlanSpec

BATTLE_PLANNER_ROOT = Path(__file__).resolve().parents[2]
LOCAL_WORKSPACE_DIR = BATTLE_PLANNER_ROOT / "workspace" / "local"
TASK_PLAN_CONFIG_DIR = LOCAL_WORKSPACE_DIR / "task_plans"


def resolve_task_plan_config_path(name: str | Path) -> Path:
    path = Path(name)
    if path.is_absolute():
        return path
    if path.suffix != ".json":
        path = path.with_suffix(".json")
    return TASK_PLAN_CONFIG_DIR / path


def load_task_plan_config(name: str | Path) -> TaskPlanSpec:
    path = resolve_task_plan_config_path(name)
    return TaskPlanSpec.model_validate_json(path.read_text(encoding="utf-8"))


def load_task_plan_configs() -> list[TaskPlanSpec]:
    """读取所有本地任务方案。"""

    return [load_task_plan_config(path) for path in sorted(TASK_PLAN_CONFIG_DIR.glob("*.json"))]


def load_task_plan_config_by_plan_id(plan_id: str) -> TaskPlanSpec:
    """按 plan_id 读取本地任务方案。"""

    for task_plan in load_task_plan_configs():
        if task_plan.plan_id == plan_id:
            return task_plan
    raise FileNotFoundError(f"Task plan not found: {plan_id}")
