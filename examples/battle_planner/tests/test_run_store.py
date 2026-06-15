from __future__ import annotations

from battle_planner.model import RunIterationOutputSpec, RunMetricAggregateSpec
from battle_planner.utils.run_store import LocalRunStore
from battle_planner.workspace.local.run_input_seed import build_local_task_run


def test_local_run_store_reads_run_output(tmp_path) -> None:
    """验证本地 run 缓存可以组装完整输出快照。"""

    store = LocalRunStore(root_dir=tmp_path)
    task_run = build_local_task_run()
    output = RunIterationOutputSpec(
        iteration_index=0,
        status="completed",
        metric_aggregates=[
            RunMetricAggregateSpec(
                key="target_damage_ratio",
                name="目标毁伤比例",
                description="每个目标单位的毁伤比例。",
                mean=0.75,
                min=0.5,
                max=1.0,
                std=0.25,
            )
        ],
    )

    store.write_run_info(task_run=task_run)
    running_output = store.read_run_output(run_id=task_run.run_id)
    store.write_iteration_output(run_id=task_run.run_id, output=output)
    store.mark_run_completed(run_id=task_run.run_id, iteration_count=1)

    store.write_task_context(task_context=task_run.task_context)
    run_output = store.read_run_output(run_id=task_run.run_id)
    runs = store.list_runs()
    contexts = store.list_task_contexts()

    assert running_output.status == "running"
    assert running_output.started_at
    assert running_output.ended_at is None
    assert run_output.status == "completed"
    assert run_output.started_at == running_output.started_at
    assert run_output.ended_at
    assert len(run_output.iterations) == 1
    assert run_output.iterations[0].metric_aggregates[0].key == "target_damage_ratio"
    assert run_output.iterations[0].metric_aggregates[0].name == "目标毁伤比例"
    assert run_output.metric_trends[0].key == "target_damage_ratio"
    assert run_output.metric_trends[0].name == "目标毁伤比例"
    assert run_output.metric_trends[0].points[0].mean == 0.75
    assert runs[0]["iteration_count"] == 1
    assert runs[0]["created_at"]
    assert runs[0]["started_at"]
    assert contexts[0].context_id == task_run.context_id
    assert contexts[0].meta["created_at"]
    assert "status" not in store.read_run_info(run_id=task_run.run_id)
    assert store.read_terminal_marker(run_id=task_run.run_id)["ended_at"] == run_output.ended_at
    assert (tmp_path / "task_contexts" / task_run.context_id / "context.json").exists()
    assert (tmp_path / "task_runs" / task_run.run_id / "run.json").exists()
    assert (tmp_path / "task_runs" / task_run.run_id / "input" / "context.json").exists()
    assert (tmp_path / "task_runs" / task_run.run_id / "input" / "task_run.json").exists()
    assert not (tmp_path / task_run.run_id).exists()
