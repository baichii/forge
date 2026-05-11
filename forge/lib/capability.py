from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from forge.lib.entity import Entity


@dataclass(frozen=True)
class CapabilityQuery:
    """Question asked by a planner or agent."""

    capability: str
    unit: Entity | str
    target: Entity | str | None = None
    context: Any | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityResult:
    """Result of a capability query"""
    allowed: bool
    reason: str = ""
    confidence: float = 1.0
    priority: float = 1.0
    evidence: dict[str, Any] = field(default_factory=dict)


class ICapabilityProvider(Protocol):
    """Environment-specific capability judgment surface."""

    def can(self, query: CapabilityQuery) -> CapabilityResult:
        ...
