from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from forge.lib.capability import ICapabilityProvider, CapabilityQuery, CapabilityResult
from forge.adapters.sim_x1.entity import Entity


if TYPE_CHECKING:
    from forge.manager import ManagerHub


class Capability(enum.StrEnum):
    CommonAttack = enum.auto()
    AirAttack = enum.auto()



class CapabilityProvider(ICapabilityProvider):

    def __init__(self, manager_hub:ManagerHub):
        self.manager_hub = manager_hub


    def can(self, query: CapabilityQuery):
        if query.capability == Capability.CommonAttack:
            pass
        elif query == Capability.AirAttack:
            pass

    def _can_air_attack(self, query: CapabilityQuery):
        """判定是否可以空中打击"""
        flag = True
        unit: Entity = CapabilityQuery.unit
        if flag and unit.type == UnitType.Aircraft:
            flag = False
        if flag and unit.weapons
        return flag

