"""推演模型预留。"""

from __future__ import annotations

from typing import Any

from battle_planner.model.evaluation import EvaluationReport, SimulationRunResult
from pydantic import BaseModel, Field


class DeductionSpec(BaseModel):
    """某个可执行方案和仿真环境交互一次的推演记录。
    Notes:
        为matrix预留
    """

    deduction_id: int = Field(description="推演 ID，在所属可执行方案内从 1 开始自增。")
    scheme_id: int = Field(description="来源可执行方案 ID，在所属任务运行内从 1 开始自增。")
    run_id: str = Field(description="来源任务运行 ID。")
    meta: dict[str, Any] = Field(default_factory=dict, description="推演元信息，预留字段。")
