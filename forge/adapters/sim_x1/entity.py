from forge.lib.entity import Entity as BaseEntity


class Entity(BaseEntity):

    def __init__(self, entity_dict: dict):
        super().__init__(entity_dict)

    @property
    def position(self):
        return self._position

    @property
    def weapons(self):
        return self._weapons
