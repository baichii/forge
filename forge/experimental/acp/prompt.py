from __future__ import annotations

from forge.experimental.acp.specs import ArtifactRecord, EvalResult, TaskSpec


def build_initial_prompt(task: TaskSpec) -> str:
    return task.prompt.render()


def build_repair_prompt(
    task: TaskSpec,
    *,
    previous_prompt: str,
    evaluation: EvalResult,
    artifacts: list[ArtifactRecord],
) -> str:
    missing_required = [
        artifact.path
        for artifact in artifacts
        if not artifact.exists
        and any(
            expected.required and artifact.path.as_posix().endswith(expected.path)
            for expected in task.expected_artifacts
        )
    ]
    failed_checks = [check for check in evaluation.checks if not check.passed]

    parts = [
        previous_prompt,
        "# Repair Request",
        (
            "The previous agent run did not satisfy the task checks. Stay in the same working "
            "directory and fix the existing output instead of starting a new unrelated task."
        ),
    ]
    if evaluation.summary:
        parts.append(f"## Evaluation Summary\n{evaluation.summary}")
    if missing_required:
        parts.append(
            "## Missing Required Artifacts\n" + "\n".join(f"- {path}" for path in missing_required)
        )
    if failed_checks:
        lines: list[str] = []
        for check in failed_checks:
            lines.append(f"- {check.name}: {check.message}")
            if check.exit_code is not None:
                lines.append(f"  exit_code: {check.exit_code}")
            if check.stdout:
                lines.append(f"  stdout: {check.stdout[-1000:]}")
            if check.stderr:
                lines.append(f"  stderr: {check.stderr[-1000:]}")
        parts.append("## Failed Checks\n" + "\n".join(lines))
    parts.append("# User Request\nPlease repair the task output so all required artifacts and checks pass.")
    return "\n\n---\n\n".join(parts)
