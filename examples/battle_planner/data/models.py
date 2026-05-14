from typing import Any

from pydantic import BaseModel, Field



class TickAgentParam(BaseModel):
    """描述tick agent参数
    """
    name: str
    description: str
    type: str
    required: bool = Field(default=True, description="参数是否必填")
    default: Any = Field(description="参数默认值")
    min_value: float | None = Field(default=None, description="数值参数最小值")
    max_value: float | None = Field(default=None, description="数值参数最大值")
    examples: list[Any] = Field(default_factory=list, description="参数示例值")


class TickAgent(BaseModel):
    """同于描述通过step执行的智能体描述, todo: 添加智能体地址"""
    name: str
    description: str
    function_description: str = Field(default="", description="智能体功能说明")
    applicable_scenarios: list[str] = Field(default_factory=list, description="适用场景")
    params: list[TickAgentParam]
    version: str | None


class Strategy(BaseModel):
    name: str
    description: str
    source: TickAgent | None = Field(description="策略关联的tick agent runtime")



class PlanBranch(BaseModel):
    """分支方案，
    """



class Plan(BaseModel):
    """方案"""
    name: str
    description: str
    plan_branches: list[PlanBranch]


class Scenario(BaseModel):
    pass


class EnvInstance(BaseModel):
    env_type: str
    scenario: Scenario
    seed: int


class PlanExecuteResult(BaseModel):
    """方案运行效果"""
    execute_id: int
    plan: Plan
    env_instance: EnvInstance
    events: dict
    statistics: dict


class StrategyParameterSet(BaseModel):
    """一次策略参数填充结果。"""

    iteration: int
    params: dict[str, float | int | str | bool]
    rationale: str


class SimulationResult(BaseModel):
    """fake 仿真输出。"""

    iteration: int
    params: dict[str, float | int | str | bool]
    logs: list[str] = Field(default_factory=list)
    key_events: list[dict[str, float | int | str | bool]] = Field(default_factory=list)
    statistics: dict[str, float | int | str | bool] = Field(default_factory=dict)
    score: float


class StrategyRecommendation(BaseModel):
    """基于仿真结果生成的下一轮修改意见。"""

    iteration: int
    advice: str
    param_adjustments: dict[str, float] = Field(default_factory=dict)
    should_continue: bool = True
    reason: str = ""
