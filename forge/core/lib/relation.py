from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from forge.core.lib.entity import Entity


@dataclass(frozen=True)
class RelationQuery:
    """"""

    relation: str
    source: Entity | str
    target: Entity | str | None | Any = None  # 关系定义
    context: Any | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RelationResult:
    """"""

    allowed: bool
    reason: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


class RelationProvider(Protocol):
    """用于描述非capability范畴的关系, 主要用于展示和推理, 不直接影响智能体的决策"""

    def query(self, query: RelationQuery) -> RelationResult: ...
