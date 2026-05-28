from pathlib import Path

from forge.experimental.acp.specs import (
    AgentCli,
    AgentConfig,
    ExpectedArtifact,
    PromptSpec,
    TaskSpec,
)


def test_expected_artifact_path_is_model_field(tmp_path: Path) -> None:
    artifact = ExpectedArtifact(path="answer.md", kind="markdown")

    assert artifact.path == "answer.md"
    assert ExpectedArtifact.model_fields["path"]


def test_task_spec_imports_and_defaults(tmp_path: Path) -> None:
    task = TaskSpec(
        task_id="demo",
        title="Demo",
        cwd=tmp_path,
        agent=AgentConfig(agent=AgentCli.codex, bin="codex"),
        prompt=PromptSpec(instructions="Do it", user_request="Write answer.md"),
    )

    assert task.timeout_seconds == 600
    assert task.max_attempts == 2
