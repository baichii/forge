from __future__ import annotations

from forge.lib.relation import RelationFact, RelationQuery
from forge.manager.manager import Manager


class RelationManager(Manager):
    """Answers relation queries from explicit, indexed, or derived facts."""

    def reset(self) -> None:
        pass

    async def update(self, **kwargs) -> None:
        pass

    def query(self, query: RelationQuery) -> RelationFact:
        return RelationFact(
            name=query.name,
            source=query.source,
            target=query.target,
            value=None,
            evidence={"reason": f"relation `{query.name}` is not implemented"},
        )
