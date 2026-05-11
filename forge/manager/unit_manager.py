from __future__ import annotations

from typing import TYPE_CHECKING

from forge.lib.entity import Entity
from forge.manager.manager import Manager

if TYPE_CHECKING:
    from forge.manager.hub import ManagerHub


class UnitManager(Manager):
    """ 维护己方单位信息
    """

    def __init__(self, agent: object, config: dict, manager_hub: ManagerHub):
        super().__init__(agent, config, manager_hub)
        self.units: dict[str, Entity] = {}

    def reset(self) -> None:
        self.units.clear()

    async def update(self, unit_infos: dict[str, dict]) -> None:
        for unit_id, unit_info in unit_infos.items():
            if unit_id in self.units:
                self.units[unit_id].update(unit_info)
            else:
                self.units[unit_id] = Entity(unit_info)

    def get_unit_by_id(self, unit_id: str) -> Entity | None:
        return self.units.get(unit_id)

    def get_unit_by_type(self, type, subtype=None, category=None) -> list[Entity]:
        result = []
        for unit in self.units.values():
            if unit.type == type and (subtype is None or unit.subtype == subtype) and (category is None or unit.category == category):
                result.append(unit)
        return result

    def get(self, condition) -> list[Entity]:
        """条件查询"""
        pass
