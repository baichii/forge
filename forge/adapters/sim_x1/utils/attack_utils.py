"""get this module from gd"""


class AttackUtility:
    """基于实时态势的打击判定，进入到这个判定阶段的都是能力具备的"""

    def can_attack(self, unit, target, manager_hub):
        # todo: 实现打击判定, 统一当manager_hub中，以实现跨sub-agent的状态管理
        return True
