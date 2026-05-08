from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from forge.lib.entity import EntityRef


@dataclass(frozen=True)
class RelationQuery:
    name: str
    source: EntityRef
    target: EntityRef | None = None
    context: Any | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RelationFact:
    name: str
    source: EntityRef
    target: EntityRef | None = None
    value: Any = None
    evidence: dict[str, Any] = field(default_factory=dict)


class RelationProvider(Protocol):
    def query(self, query: RelationQuery) -> RelationFact:
        ...
