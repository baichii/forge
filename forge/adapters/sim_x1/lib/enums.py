from enum import Enum, StrEnum

class SimX1Action(Enum):
    """SimX1 action space"""

    MOVE = "move"
    TURN = "turn"
    PICK_UP = "pick_up"
    DROP = "drop"


class WeaponTarget(StrEnum):
    """定义武器目标类型"""

    AIR = "air"
    GROUND = "ground"
    SEA = "sea"
    HAS_RADDER = "has_radar"  # 测试类型


class UnitType(StrEnum):
    """定义单位类型"""

    AIRCRAFT = "aircraft"
    SHIP = "ship"
    SUBMARINE = "submarine"
    FACILITY = "facility"

