from __future__ import annotations

from forge.core.lib.relation import RelationResult, RelationQuery
from forge.core.manager.manager import Manager


class RelationManager(Manager):
    """Answers relation queries from explicit, indexed, or derived facts."""

    def reset(self) -> None:
        pass

    async def update(self, **kwargs) -> None:
        pass

    def query(self, query: RelationQuery) -> RelationResult:
        return RelationResult(
            reason="dummy",
            evidence={"reason": f"relation `{query.name}` is not implemented"},
        )
