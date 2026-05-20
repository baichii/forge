from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from forge.adapters.sim_x1.lib.entity import Entity

if TYPE_CHECKING:
    from forge.core.manager import ManagerHub


@dataclass
class WeaponSpec:
    """定义一个武器的属性"""

    name: str
    num: int
    range: Any
    target_tags: set[str]  # 目标tag类型
    params: dict[str, Any] = None  # 其他扩展属性


class Weapon:
    def __init__(self, entity: Entity, weapon_spec: WeaponSpec, manager_hub: ManagerHub):
        self.entity = entity
        self.weapon_spec = weapon_spec
        self.manager_hub = manager_hub

    def has_attack(self, target_tags: set[str | int]) -> bool:
        weapon_target_tags = set(self.weapon_spec.target_tags).intersection(target_tags)
        has_weapon = len(weapon_target_tags) > 0
        return has_weapon and self.weapon_spec.num > 0

    @property
    def name(self):
        return self.weapon_spec.name

    @property
    def range(self):
        # fixme: 在实际场景中，range大概率是一个实时计算的函数，需要结合单位属性和场景属性进行计算，不太适合作为属性
        return self.weapon_spec.range

    @property
    def num(self):
        return self.weapon_spec.num


class Weapons:
    """描述一组武器, 例如一个单位的所有武器"""

    def __init__(self, weapons):
        self.weapons = weapons

    def has_attack(self, target_tags: set[str | int]) -> bool:
        for weapon in self.weapons:
            if weapon.has_attack(target_tags):
                return True
        return False
