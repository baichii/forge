import uuid
from typing import Any
from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field


class WorkflowState(StrEnum):
    """定义业务状态推进情况状态"""
    START = "start"
    COMPLETE = "complete"
    ERROR = "error"
    INTERRUPTED = "interrupted"
    STRATEGY_PLANNED = "strategy_planned"
    SIM_FINISHED = "sim_finished"


class StrategyPlanningState(BaseModel):
    """
    策略迭代状态记录

    """

    # Workflow state management
    cur_stage: WorkflowState = WorkflowState.START
    previous_state: WorkflowState | None = None
    start_time: datetime | None = None
    last_update_time: datetime | None = None
    stage_times: dict[str, datetime] = Field(default_factory=dict)

    # Error handling and recovery
    error: str | None = None
    error_count: int = 0
    retry_count: dict[str, int] = Field(default_factory=dict)

    # Interruption handling
    interrupted: bool = False
    interruption_reason: str | None = None
    checkpoint_id: str | None = None

    # Progress tracking
    progress: float = 0.0  # 0.0 to 1.0
    stage_progress: dict[str, float] = Field(default_factory=dict)

    # Parallel execution tracking
    parallel_tasks: list[str] = Field(default_factory=list)
    completed_tasks: list[str] = Field(default_factory=list)
    task_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

