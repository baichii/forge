if __name__ == "__main__":
    from enum import Enum

    class SimX1Action(Enum):
        """SimX1 action space"""

        MOVE = "move"
        TURN = "turn"
        PICK_UP = "pick_up"
        DROP = "drop"