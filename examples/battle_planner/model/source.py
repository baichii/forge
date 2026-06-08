"""本地资源，用于服务模拟"""

from typing import Any

from pydantic import BaseModel, Field


class TickAgentSourceSpec(BaseModel):
    """tick agent 信息"""

    tick_agent_id: str = Field(description="tick agent 唯一标识, 全局唯一")
    name: str = Field(description="tick agent 名称")
    description: str = Field(description="tick agent描述")
    params: dict[str, Any] = Field()
    version: str = Field(description="tick agent版本")


class StrategySourceSpec(BaseModel):
    """本地策略卡片资源"""

    strategy_id: int = Field(description="策略卡片在方案中的唯一id")
    name: str = Field(description="策略卡片在方案上的名字")
    description: str = Field(description="策略卡片在描述")


class SchemeSourceSpec(BaseModel):
    """本地方案资源"""

    scheme_id: int = Field(description="方案唯一标识, 全局唯一")
    name: str = Field(description="方案名称")
    scenario_name: str = Field(description="想定名称或场景标识。")
    side: str = Field(description="执行规范的side， 例如blue/red")
    opponent_side: str = Field(description="对抗阵营")
    strategies: list[StrategySourceSpec] = Field(default_factory=list, description="这个方案配置的策略卡片")
    meta: dict[str, Any] = Field(default_factory=dict, description="方案元信息， 预留字段。")
