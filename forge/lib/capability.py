from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from forge.lib.entity import Entity
    from forge.manager.hub import ManagerHub


@dataclass(frozen=True)
class CapabilityQuery:
    """Question asked by a planner or agent."""

    capability: str
    unit: Entity | str
    target: Entity | str | None = None
    context: Any | None = None
    params: dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        return f"CapabilityQuery(capability={self.capability}, unit={self.unit}, target={self.target})"


@dataclass(frozen=True)
class CapabilityResult:
    """Result of a capability query"""

    allowed: bool
    reason: str = ""
    confidence: float = 1.0
    priority: float = 1.0
    evidence: dict[str, Any] = field(default_factory=dict)


class ICapabilityProvider(Protocol):
    """Environment-specific capability judgment surface.

    forge.lib不再管理具体的能力，仅定义能力查询接口

    fixme: 持续实时进行能力评估在rts场景是不切实际的，频繁的距离结算会占用大量的时间，需要设计一个更新策略
           c1: callback实现，通过事件触发，效率更高，但TickAgent的接口要大改，需要加入足够多的hook捕获事件
           c2: 传统实现，定时更新，设置不同的更新间隔

    """

    def __init__(self, manager_hub: ManagerHub):
        self.manager_hub = manager_hub

    def can(self, query: CapabilityQuery) -> CapabilityResult:
        """判定当前时刻是否可以执行某种能力, 考虑单位自身属性和环境因素, 例如距离, 视野等"""
        ...

    def has(self, query: CapabilityQuery) -> bool:
        """判定是否具备某种能力, 仅考虑单位自身属性, 例如单位类型, tag判定"""
        ...
