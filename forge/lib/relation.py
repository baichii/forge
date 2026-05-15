from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from forge.lib.entity import Entity


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
    """用于描述非capability范畴的关系"""

    def query(self, query: RelationQuery) -> RelationResult: ...
