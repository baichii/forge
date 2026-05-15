"""
base enums

Note:
    1. 不再尝试建立通用的枚举类型，在各自环境的adaptor中进行定义
    2. 原生非类型检索不再强行通过类型映射来实现，通过tag+condition解析进行,以实现更复杂的属性/能力检索
    3. 基于tag的检索还在测试中 [evil]
"""

import enum


class UnitType(enum.StrEnum):
    """单位类型"""

    Aircraft = enum.auto()
    Facility = enum.auto()
    Ship = enum.auto()
    Submarine = enum.auto()
    Satellite = enum.auto()
    Weapon = enum.auto()
    Null = enum.auto()


class WweaponTargetTag:
    """目标检索tag"""

    ...
