from __future__ import annotations

from battle_planner.backend.app import app
from battle_planner.backend.config import backend_settings
from fastapi.testclient import TestClient


def test_backend_creates_task_context(tmp_path, monkeypatch) -> None:
    """验证 backend 能从请求创建任务上下文。"""

    monkeypatch.setattr(backend_settings, "RUNS_DIR", tmp_path)
    client = TestClient(app)

    response = client.post(
        "/battle-planner/contexts",
        json={"plan_id": "2175600675558391808"},
    )
    context_id = response.json()["context_id"]
    read_response = client.get(f"/battle-planner/contexts/{context_id}")
    list_response = client.get("/battle-planner/contexts")

    assert response.status_code == 200
    assert read_response.status_code == 200
    assert list_response.status_code == 200
    assert read_response.json()["plan_id"] == "2175600675558391808"
    assert list_response.json()[0]["context_id"] == context_id
    assert list_response.json()[0]["name"]
    assert (tmp_path / "task_contexts" / context_id / "context.json").exists()


def test_backend_rejects_unknown_task_plan(tmp_path, monkeypatch) -> None:
    """验证未知 plan_id 不会生成上下文。"""

    monkeypatch.setattr(backend_settings, "RUNS_DIR", tmp_path)
    client = TestClient(app)

    response = client.post(
        "/battle-planner/contexts",
        json={"plan_id": "missing-plan"},
    )

    assert response.status_code == 404
