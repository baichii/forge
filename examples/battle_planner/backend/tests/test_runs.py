from __future__ import annotations

import asyncio
import json

from battle_planner.backend.app import app
from battle_planner.backend.config import backend_settings
from battle_planner.backend.services.run_event_service import RunEventService
from battle_planner.model import RunIterationOutputSpec
from battle_planner.utils.run_store import LocalRunStore
from battle_planner.workspace.local.run_input_seed import build_local_task_run
from fastapi.testclient import TestClient


def test_backend_reads_run_cache(tmp_path, monkeypatch) -> None:
    """验证 backend 能读取本地 run 缓存。"""

    task_run = _write_demo_run(tmp_path)
    monkeypatch.setattr(backend_settings, "RUNS_DIR", tmp_path)
    client = TestClient(app)

    runs_response = client.get("/battle-planner/runs")
    run_response = client.get(f"/battle-planner/runs/{task_run.run_id}")
    iteration_response = client.get(f"/battle-planner/runs/{task_run.run_id}/iterations/0")
    missing_response = client.get("/battle-planner/runs/missing-run")

    assert runs_response.status_code == 200
    assert runs_response.json()[0]["run_id"] == task_run.run_id
    assert runs_response.json()[0]["run_name"]
    assert runs_response.json()[0]["created_at"]
    assert run_response.json()["status"] == "completed"
    assert iteration_response.json()["iteration_index"] == 0
    assert missing_response.status_code == 404


def test_run_event_service_notifies_iteration_and_terminal(tmp_path) -> None:
    """验证 SSE 服务能生成轮次和终态通知。"""

    task_run = build_local_task_run()
    store = LocalRunStore(root_dir=tmp_path)
    store.write_run_info(task_run=task_run)

    iteration_event = asyncio.run(_next_iteration_event(store, task_run.run_id))
    store.mark_run_completed(run_id=task_run.run_id, iteration_count=1)
    terminal_event = asyncio.run(_next_terminal_event(store, task_run.run_id))

    assert iteration_event["event"] == "iteration_ready"
    assert json.loads(iteration_event["data"])["iteration_index"] == 0
    assert terminal_event["event"] == "run_completed"


def _write_demo_run(tmp_path):
    task_run = build_local_task_run()
    store = LocalRunStore(root_dir=tmp_path)
    store.write_run_info(task_run=task_run)
    store.write_iteration_output(
        run_id=task_run.run_id,
        output=RunIterationOutputSpec(iteration_index=0, status="completed"),
    )
    store.mark_run_completed(run_id=task_run.run_id, iteration_count=1)
    return task_run


async def _next_iteration_event(store: LocalRunStore, run_id: str) -> dict:
    service = RunEventService(store=store, poll_interval_seconds=0.01)
    events = service.iter_events(run_id=run_id)
    event_task = asyncio.create_task(anext(events))
    await asyncio.sleep(0.02)
    store.write_iteration_output(
        run_id=run_id,
        output=RunIterationOutputSpec(iteration_index=0, status="completed"),
    )
    event = await asyncio.wait_for(event_task, timeout=1)
    await events.aclose()
    return event


async def _next_terminal_event(store: LocalRunStore, run_id: str) -> dict:
    service = RunEventService(store=store, poll_interval_seconds=0.01)
    events = service.iter_events(run_id=run_id)
    event = await anext(events)
    await events.aclose()
    return event
