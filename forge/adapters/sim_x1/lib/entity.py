from forge.lib.entity import Entity as BaseEntity
from forge.adapters.sim_x1.lib.weapon import Weapon, Weapons


class Entity(BaseEntity):
    def __init__(self, entity_dict: dict):
        super().__init__(entity_dict)

    @property
    def position(self):
        return self._position

    @property
    def weapons(self) -> Weapons:
        return self._weapons

    @property
    def weapon_target_tags(self) -> set[str | int]:
        """作为被攻击目标时的tag类型"""
        return self._weapon_target_tags

    @property
    def search_target_tags(self) -> set[str | int]:
        """作为被搜索目标是的tags"""
        return self._search_target_tags
