import sqlite3

from forge.logger import logger
from battle_planner.data.models import PlanExecuteResult


class SqliteClient:

    def __init__(self, db_path: str = "replay.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    async def initialize_tables(self):
        pass

    async def initial_plan_execute_result(self):
        pass

    async def get_plan_execute_result(self):
        pass

    async def save_plan_execute_result(self):
        pass
