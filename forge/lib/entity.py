from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class EntityRef:
    """Stable reference to an environment-owned entity."""

    entity_id: str
    entity_type: str | None = None
    env_id: str | None = None


@dataclass
class EntitySnapshot:
    """Environment-normalized entity facts."""

    ref: EntityRef
    attributes: dict[str, Any] = field(default_factory=dict)
    raw: Mapping[str, Any] | None = None
