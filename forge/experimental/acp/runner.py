from __future__ import annotations

from uuid import uuid4

from forge.experimental.acp.adaptor import run_cli_agent
from forge.experimental.acp.evaluator import collect_artifacts, evaluate_task
from forge.experimental.acp.prompt import build_initial_prompt, build_repair_prompt
from forge.experimental.acp.specs import (
    ArtifactRecord,
    EvalResult,
    RunRecord,
    RunStatus,
    TaskResult,
    TaskSpec,
)


def run_task(task: TaskSpec) -> TaskResult:
    task.cwd.mkdir(parents=True, exist_ok=True)

    runs: list[RunRecord] = []
    artifacts: list[ArtifactRecord] = []
    evaluations: list[EvalResult] = []
    current_prompt = build_initial_prompt(task)
    final_status = RunStatus.failed

    for attempt in range(1, task.max_attempts + 1):
        run_id = f"{task.task_id}-{uuid4().hex[:12]}"
        cli_result = run_cli_agent(task, run_id=run_id, attempt=attempt, prompt=current_prompt)
        runs.append(cli_result.run)

        attempt_artifacts = collect_artifacts(task, run_id=run_id, events=cli_result.events)
        artifacts.extend(attempt_artifacts)

        evaluation = evaluate_task(task, run_id=run_id)
        evaluations.append(evaluation)

        if cli_result.run.status == RunStatus.succeeded and evaluation.passed:
            final_status = RunStatus.succeeded
            break

        if attempt < task.max_attempts:
            current_prompt = build_repair_prompt(
                task,
                previous_prompt=current_prompt,
                evaluation=evaluation,
                artifacts=attempt_artifacts,
            )

    summary = _summarize(final_status, runs, evaluations)
    return TaskResult(
        task_id=task.task_id,
        status=final_status,
        runs=runs,
        artifacts=artifacts,
        evaluations=evaluations,
        attempts=len(runs),
        summary=summary,
    )


def _summarize(status: RunStatus, runs: list[RunRecord], evaluations: list[EvalResult]) -> str:
    if not runs:
        return "task did not run"
    latest_run = runs[-1]
    latest_eval = evaluations[-1] if evaluations else None
    if status == RunStatus.succeeded:
        return f"task succeeded after {len(runs)} attempt(s)"
    if latest_eval and latest_eval.summary:
        return f"task failed after {len(runs)} attempt(s): {latest_eval.summary}"
    if latest_run.error_message:
        return f"task failed after {len(runs)} attempt(s): {latest_run.error_message}"
    return f"task failed after {len(runs)} attempt(s)"
