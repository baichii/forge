from __future__ import annotations

from battle_planner.model import RunIterationOutputSpec
from battle_planner.utils.run_store import LocalRunStore
from battle_planner.workspace.local.run_input_seed import build_local_task_run


def test_local_run_store_reads_run_output(tmp_path) -> None:
    """验证本地 run 缓存可以组装完整输出快照。"""

    store = LocalRunStore(root_dir=tmp_path)
    task_run = build_local_task_run()
    output = RunIterationOutputSpec(iteration_index=0, status="completed")

    store.write_run_info(task_run=task_run)
    store.write_iteration_output(run_id=task_run.run_id, output=output)
    store.mark_run_completed(run_id=task_run.run_id, iteration_count=1)

    store.write_task_context(task_context=task_run.task_context)
    run_output = store.read_run_output(run_id=task_run.run_id)
    runs = store.list_runs()
    contexts = store.list_task_contexts()

    assert run_output.status == "completed"
    assert len(run_output.iterations) == 1
    assert runs[0]["iteration_count"] == 1
    assert runs[0]["created_at"]
    assert contexts[0].context_id == task_run.context_id
    assert contexts[0].meta["created_at"]
    assert "status" not in store.read_run_info(run_id=task_run.run_id)
    assert (tmp_path / "task_contexts" / task_run.context_id / "context.json").exists()
    assert (tmp_path / "task_runs" / task_run.run_id / "run.json").exists()
    assert (tmp_path / "task_runs" / task_run.run_id / "input" / "context.json").exists()
    assert (tmp_path / "task_runs" / task_run.run_id / "input" / "task_run.json").exists()
    assert not (tmp_path / task_run.run_id).exists()
