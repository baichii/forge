from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from forge.lib.entity import EntityRef


@dataclass(frozen=True)
class CapabilityQuery:
    """Question asked by a planner or agent."""

    capability: str
    unit: EntityRef
    target: EntityRef | None = None
    context: Any | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityResult:
    allowed: bool
    reason: str = ""
    confidence: float = 1.0
    evidence: dict[str, Any] = field(default_factory=dict)


class CapabilityProvider(Protocol):
    """Environment-specific capability judgement surface."""

    def can(self, query: CapabilityQuery) -> CapabilityResult:
        ...
