from typing import Any
from pydantic import BaseModel, Field, field_validator



class TickAgentParam(BaseModel):
    """描述tick agent参数
    """
    name: str
    description: str
    type: str
    required: bool = Field(default=True, description="参数是否必填")
    default: Any = Field(description="参数默认值")


class TickAgent(BaseModel):
    """同于描述通过step执行的智能体描述, todo: 添加智能体地址"""
    name: str
    description: str
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
