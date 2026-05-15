from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from forge.lib.capability import ICapabilityProvider, CapabilityQuery, CapabilityResult
from forge.adapters.sim_x1.lib.entity import Entity
from forge.adapters.sim_x1.lib.enums import UnitType, WeaponTarget
from forge.adapters.sim_x1.utils.attack_utils import AttackUtility

if TYPE_CHECKING:
    from forge.manager import ManagerHub


class Capability(enum.StrEnum):
    """能力定义，用于测试"""

    CommonAttack = enum.auto()  # 面对面
    AirAttack = enum.auto()  # 空对面
    AirIntercept = enum.auto()  # 空对空


class CapabilityProvider(ICapabilityProvider):
    def __init__(self, manager_hub: ManagerHub):
        super().__init__(manager_hub)

    def can(self, query: CapabilityQuery):
        if query.capability == Capability.CommonAttack:
            return self._can_common_attack(query)
        elif query == Capability.AirAttack:
            pass

    def has(self, query: CapabilityQuery) -> bool:
        if query.capability == Capability.CommonAttack:
            return self._has_common_attack(query)
        elif query.capability == Capability.AirAttack:
            return self._has_air_attack(query)
        else:
            raise NotImplementedError(f"不支持的能力查询, {query}")

    def _has_common_attack(self, query: CapabilityQuery):
        """判定是否具备能力"""
        flag = True
        unit: Entity = query.unit
        if flag and unit.type != UnitType.AIRCRAFT:
            flag = False
        weapon_target_tags = set()
        if flag and unit.weapons.has_attack(target_tags=weapon_target_tags):
            flag = False
        return flag

    def _can_common_attack(self, query: CapabilityQuery) -> CapabilityResult:
        """判定当前是否可以进执行能力"""
        has_flag = self._has_common_attack(query)
        unit: Entity = query.unit

        if not has_flag:
            return CapabilityResult(allowed=False, reason="不具备攻击能力")

        # 态势分析
        if AttackUtility.can_attack(unit, query.target, self.manager_hub):
            return CapabilityResult(allowed=True)
        else:
            return CapabilityResult(allowed=False, reason="无法攻击目标")

    def _has_air_attack(self, query: CapabilityQuery) -> bool:
        """判定是否具备能力"""
        flag = True
        unit: Entity = query.unit
        if flag and unit.type == UnitType.AIRCRAFT:
            flag = False
        weapon_target_tags = set()
        if flag and not unit.weapons.has_attack(target_tags=weapon_target_tags):
            flag = False
        return flag
