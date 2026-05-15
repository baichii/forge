from __future__ import annotations


class Entity(object):
    """实体对象

    定位:
        1. 用于持久化长期决策需要的信息
        2. 当前时刻单位快照
        3. 3层类型判定, type-subtype-category, 适用于单位定义

    Note:
        1. entity不一定是单位，还可能是area、position、group

    """

    def __init__(self, entity_dict: dict):
        self._entity_dict = entity_dict
        self.update(self._entity_dict)

    def update(self, entity_dict: dict):
        self._update_initial(entity_dict)
        self._update_snapshot(entity_dict)

    def _update_initial(self, entity_dict: dict):
        """初始化初始信息"""

    def _update_snapshot(self, entity_dict: dict):
        """更新快照"""
        self._entity_dict = entity_dict
        for key, value in entity_dict.items():
            setattr(self, "_" + key, value)

    def __getattr__(self, item: str):
        return self._entity_dict.get("_" + item, None)

    @property
    def id(self):
        """全局单位检索属性，用于和env直接交付"""
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def subtype(self):
        return self._subtype

    @property
    def category(self):
        return self._category
