from __future__ import annotations

import subprocess
from pathlib import Path

from forge.experimental.acp.specs import (
    AgentEvent,
    ArtifactKind,
    ArtifactRecord,
    CheckResult,
    EvalCheck,
    EvalResult,
    TaskSpec,
)


def resolve_task_path(cwd: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else cwd / path


def collect_artifacts(
    task: TaskSpec,
    *,
    run_id: str,
    events: list[AgentEvent],
) -> list[ArtifactRecord]:
    records: list[ArtifactRecord] = []
    seen: set[Path] = set()

    def add(path: Path, kind: ArtifactKind = "other") -> None:
        resolved = path.resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        records.append(
            ArtifactRecord(
                task_id=task.task_id,
                run_id=run_id,
                path=resolved,
                kind=kind,
                exists=resolved.exists(),
                size_bytes=resolved.stat().st_size if resolved.exists() else None,
            )
        )

    for expected in task.expected_artifacts:
        add(resolve_task_path(task.cwd, expected.path), expected.kind)
    for event in events:
        if event.type == "artifact" and event.artifact_path:
            add(resolve_task_path(task.cwd, event.artifact_path))
    return records


def evaluate_task(task: TaskSpec, *, run_id: str) -> EvalResult:
    checks: list[CheckResult] = []

    for expected in task.expected_artifacts:
        if expected.required:
            checks.append(_check_file_exists(task.cwd, expected.path, f"artifact:{expected.path}"))

    for check in task.eval_checks:
        checks.append(_run_check(task, check))

    passed = all(check.passed for check in checks)
    failed = [check for check in checks if not check.passed]
    summary = "all checks passed" if passed else "; ".join(check.message for check in failed)
    return EvalResult(
        run_id=run_id,
        task_id=task.task_id,
        passed=passed,
        checks=checks,
        summary=summary,
    )


def _run_check(task: TaskSpec, check: EvalCheck) -> CheckResult:
    if check.kind == "manual":
        return CheckResult(name=check.id, passed=True, message="manual check recorded")
    if check.kind == "file_exists":
        if check.target:
            return _check_file_exists(task.cwd, check.target, check.id)
        required = [artifact for artifact in task.expected_artifacts if artifact.required]
        missing = [
            artifact.path
            for artifact in required
            if not resolve_task_path(task.cwd, artifact.path).exists()
        ]
        return CheckResult(
            name=check.id,
            passed=not missing,
            message="all expected artifacts exist"
            if not missing
            else f"missing expected artifacts: {', '.join(missing)}",
        )
    if check.kind == "command":
        if not check.command:
            return CheckResult(name=check.id, passed=False, message="command check missing command")
        try:
            completed = subprocess.run(
                check.command,
                cwd=task.cwd,
                text=True,
                capture_output=True,
                timeout=task.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return CheckResult(name=check.id, passed=False, message="command timed out")
        except Exception as exc:
            return CheckResult(name=check.id, passed=False, message=f"command failed to start: {exc}")
        return CheckResult(
            name=check.id,
            passed=completed.returncode == 0,
            message="command passed" if completed.returncode == 0 else "command failed",
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    return CheckResult(name=check.id, passed=False, message=f"unsupported check kind: {check.kind}")


def _check_file_exists(cwd: Path, target: str, name: str) -> CheckResult:
    path = resolve_task_path(cwd, target)
    exists = path.exists()
    return CheckResult(
        name=name,
        passed=exists,
        message=f"file exists: {path}" if exists else f"missing file: {path}",
    )
