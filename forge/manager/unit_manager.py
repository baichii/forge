from __future__ import annotations

from typing import Any, Iterable

from forge.lib.entity import EntityRef, EntitySnapshot
from forge.manager.manager import Manager


class UnitManager(Manager):
    """Maintains entity facts and latest snapshots."""

    def __init__(self, agent: object, config: dict, manager_hub):
        super().__init__(agent, config, manager_hub)
        self.units: dict[str, EntitySnapshot] = {}

    def reset(self) -> None:
        self.units.clear()

    async def update(self, **kwargs) -> None:
        snapshots = kwargs.get("units") or kwargs.get("entities") or []
        self.update_units(snapshots)

    def update_units(self, snapshots: Iterable[EntitySnapshot | dict[str, Any]]) -> None:
        for snapshot in snapshots:
            entity_snapshot = self._coerce_snapshot(snapshot)
            self.units[entity_snapshot.ref.entity_id] = entity_snapshot

    def get(self, entity_ref: EntityRef | str) -> EntitySnapshot | None:
        entity_id = entity_ref.entity_id if isinstance(entity_ref, EntityRef) else entity_ref
        return self.units.get(entity_id)

    def _coerce_snapshot(self, snapshot: EntitySnapshot | dict[str, Any]) -> EntitySnapshot:
        if isinstance(snapshot, EntitySnapshot):
            return snapshot
        ref = snapshot.get("ref")
        if not isinstance(ref, EntityRef):
            ref = EntityRef(
                entity_id=str(snapshot["entity_id"]),
                entity_type=snapshot.get("entity_type"),
                env_id=snapshot.get("env_id"),
            )
        return EntitySnapshot(
            ref=ref,
            attributes=dict(snapshot.get("attributes", {})),
            raw=snapshot,
        )
