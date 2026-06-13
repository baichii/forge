from __future__ import annotations

from battle_planner.backend.app import app
from fastapi.testclient import TestClient


def test_backend_reads_local_task_plans() -> None:
    """验证 backend 能读取本地只读任务方案。"""

    client = TestClient(app)

    plans_response = client.get("/battle-planner/plans")
    plan_id = plans_response.json()[0]["plan_id"]
    plan_response = client.get(f"/battle-planner/plans/{plan_id}")
    missing_response = client.get("/battle-planner/plans/missing-plan")

    assert plans_response.status_code == 200
    assert plan_response.status_code == 200
    assert plan_response.json()["plan_id"] == plan_id
    assert missing_response.status_code == 404
