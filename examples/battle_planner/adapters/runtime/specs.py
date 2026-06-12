from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EnvRunReport(BaseModel):
    """记录一次 runner 执行中的环境运行事实。"""

    env_name: str
    seed: int | None = None
    max_steps: int | None = None
    step_count: int = 0
    elapsed_seconds: float = 0.0
    stop_reason: str | None = None
    final_sim_time: float | None = None


class TickAgentReport(BaseModel):
    """记录一个 tick-agent 实例的运行摘要和稀疏事件。"""

    agent_instance_id: str
    agent_name: str
    side: str
    status_history: list[dict[str, Any]] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)
    first_active_step: int | None = None
    first_active_sim_time: float | None = None
    finished_step: int | None = None
    finished_sim_time: float | None = None
    action_count: int = 0


class BattlefieldReport(BaseModel):
    """记录环境 输出的战场事件。"""

    step: int
    sim_time: float | None = None
    event_type: str
    side: str | None = None
    unit_id: str | None = None
    info: dict[str, Any] = Field(default_factory=dict)


class RunnerReport(BaseModel):
    """记录 battle-planner runner 生成的结构化运行报告。"""

    env: EnvRunReport
    agents: list[TickAgentReport] = Field(default_factory=list)
    battlefield_events: list[BattlefieldReport] = Field(default_factory=list)
    callbacks: dict[str, Any] = Field(default_factory=dict)
    system_evaluation: dict[str, Any] = Field(default_factory=dict)
