from __future__ import annotations

import time

from battle_planner.backend.app import app
from battle_planner.backend.config import backend_settings
from battle_planner.conf import LLMMode, settings
from fastapi.testclient import TestClient


def test_backend_starts_run_execution(tmp_path, monkeypatch) -> None:
    """验证 backend 能创建 run 并在后台完成 workflow。"""

    _configure_runtime(tmp_path, monkeypatch)
    client = TestClient(app)
    context_id = _create_context(client)

    run_response = client.post(
        "/battle-planner/runs",
        json={
            "context_id": context_id,
            "run_name": "backend execution smoke",
            "options": {
                "workflow_name": "zc_lite_baseline",
                "max_iterations": 1,
                "sim_runs_per_scheme": 1,
                "max_retry": 1,
                "timeout_seconds": None,
                "extra": {},
            },
        },
    )
    run_id = run_response.json()["run_id"]
    final_payload = _wait_for_status(client, run_id, {"completed", "failed"})

    assert run_response.status_code == 200
    assert run_response.json()["status"] == "running"
    assert final_payload["status"] == "completed"
    assert final_payload["iterations"]
    assert (tmp_path / "task_runs" / run_id / "run.json").exists()
    assert (tmp_path / "task_runs" / run_id / "input" / "context.json").exists()
    assert (tmp_path / "task_runs" / run_id / "input" / "task_run.json").exists()


def test_backend_marks_run_failed_when_workflow_errors(tmp_path, monkeypatch) -> None:
    """验证后台 workflow 异常会写入失败终态。"""

    _configure_runtime(tmp_path, monkeypatch)
    client = TestClient(app)
    context_id = _create_context(client)

    run_response = client.post(
        "/battle-planner/runs",
        json={
            "context_id": context_id,
            "run_name": "backend execution failure smoke",
            "options": {
                "workflow_name": "missing_workflow",
                "max_iterations": 1,
                "sim_runs_per_scheme": 1,
                "max_retry": 1,
                "timeout_seconds": None,
                "extra": {},
            },
        },
    )
    run_id = run_response.json()["run_id"]
    final_payload = _wait_for_status(client, run_id, {"failed"})

    assert run_response.status_code == 200
    assert final_payload["status"] == "failed"


def test_backend_rejects_run_when_capacity_is_full(tmp_path, monkeypatch) -> None:
    """验证 backend 容量满时不会创建 run。"""

    _configure_runtime(tmp_path, monkeypatch)
    monkeypatch.setattr(backend_settings, "EXECUTION_MAX_ACTIVE_RUNS", 0)
    client = TestClient(app)
    context_id = _create_context(client)

    response = client.post(
        "/battle-planner/runs",
        json={
            "context_id": context_id,
            "run_name": "backend execution capacity smoke",
            "options": {
                "workflow_name": "zc_lite_baseline",
                "max_iterations": 1,
                "sim_runs_per_scheme": 1,
                "max_retry": 1,
                "timeout_seconds": None,
                "extra": {},
            },
        },
    )

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "run_capacity_exceeded"
    assert not (tmp_path / "task_runs").exists()


def test_backend_uses_readable_run_name_fallback(tmp_path, monkeypatch) -> None:
    """验证空 run_name 会生成可读名称。"""

    _configure_runtime(tmp_path, monkeypatch)
    client = TestClient(app)
    context_id = _create_context(client)

    response = client.post(
        "/battle-planner/runs",
        json={
            "context_id": context_id,
            "options": {
                "workflow_name": "missing_workflow",
                "max_iterations": 1,
                "sim_runs_per_scheme": 1,
                "max_retry": 1,
                "timeout_seconds": None,
                "extra": {},
            },
        },
    )

    assert response.status_code == 200
    assert "运行" in response.json()["run_name"]


def _configure_runtime(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(backend_settings, "RUNS_DIR", tmp_path)
    monkeypatch.setattr(settings, "LLM_MODE", LLMMode.OFFLINE)
    monkeypatch.setattr(settings, "OUTPUT_SEED", "debug")
    monkeypatch.setattr(settings, "SIM_MAX_DECISION_STEPS", 70)


def _create_context(client: TestClient) -> str:
    response = client.post(
        "/battle-planner/contexts",
        json={"plan_id": "2175600675558391808"},
    )
    return response.json()["context_id"]


def _wait_for_status(client: TestClient, run_id: str, statuses: set[str]) -> dict:
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        payload = client.get(f"/battle-planner/runs/{run_id}").json()
        if payload["status"] in statuses:
            return payload
        time.sleep(0.05)
    return client.get(f"/battle-planner/runs/{run_id}").json()
