from __future__ import annotations

from forge.lib.capability import CapabilityQuery, CapabilityResult
from forge.manager.manager import Manager


class CapabilityManager(Manager):
    """Answers capability queries by combining manager-owned state."""

    def reset(self) -> None:
        pass

    async def update(self, **kwargs) -> None:
        pass

    def can(self, query: CapabilityQuery) -> CapabilityResult:
        return CapabilityResult(
            allowed=False,
            reason=f"capability `{query.capability}` is not implemented",
            confidence=0.0,
        )
