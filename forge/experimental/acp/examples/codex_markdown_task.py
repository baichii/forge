from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from forge.experimental.acp.runner import run_task
from forge.experimental.acp.specs import (
    AgentCli,
    AgentConfig,
    EvalCheck,
    ExpectedArtifact,
    PromptSpec,
    TaskSpec,
)


def build_task() -> TaskSpec:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    cwd = Path("/private/tmp/forge-acp-codex-demo") / timestamp
    model = os.environ.get("ACP_CODEX_MODEL") or None
    return TaskSpec(
        task_id="codex-markdown-demo",
        title="Codex markdown artifact demo",
        cwd=cwd,
        agent=AgentConfig(
            agent=AgentCli.codex,
            bin=os.environ.get("CODEX_BIN", "codex"),
            model=model,
        ),
        prompt=PromptSpec(
            instructions=(
                "You are running as a delegated CLI agent. Create the requested artifact in the "
                "current working directory. Do not modify files outside the working directory."
            ),
            user_request=(
                "Create a concise markdown file named answer.md. It should explain what a CLI "
                "delegate runner does in 3 bullet points."
            ),
        ),
        expected_artifacts=[ExpectedArtifact(path="answer.md", kind="markdown")],
        eval_checks=[
            EvalCheck(
                id="answer-non-empty",
                kind="command",
                command=[
                    sys.executable,
                    "-c",
                    (
                        "from pathlib import Path; p=Path('answer.md'); "
                        "raise SystemExit(0 if p.exists() and p.read_text().strip() else 1)"
                    ),
                ],
            )
        ],
        max_attempts=2,
        timeout_seconds=600,
    )


def main() -> None:
    result = run_task(build_task())
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
