from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

ArtifactKind = Literal["html", "markdown", "json", "code", "image", "other"]


class AgentCli(StrEnum):
    """本次agent cli工具"""

    codex = "codex"
    claude = "claude"


class RunStatus(StrEnum):
    """一次acp调用的运行状态"""

    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"


class AgentConfig(BaseModel):
    """agent cli 调用流程"""

    agent: AgentCli
    bin: str
    model: str | None = None
    extra_args: list[str] = Field(default_factory=list)


class ToolHint(BaseModel):
    """注入给agent cli的工具说明"""

    name: str
    description: str
    command_example: str


class PromptSpec(BaseModel):
    """
    一次任务发送给agent cli 的prompt
    """

    instructions: str
    user_request: str
    context: str = ""
    tools: list[ToolHint] = Field(default_factory=list)

    def render(self) -> str:
        parts: list[str] = []

        parts.append(f"# Instructions:\n{self.instructions}")

        if self.tools:
            tool_lines = []
            for tool in self.tools:
                tool_lines.append(
                    f"## {tool.name}\n{tool.description}\n\nExample:\n```bash\n{tool.command_example}\n```"
                )
            parts.append("# Available Tools\n\n" + "\n\n".join(tool_lines))

        if self.context:
            parts.append(f"# Context\n\n{self.context}")

        parts.append(f"# User Request\n\n{self.user_request}")

        return "\n\n---\n\n".join(parts)


class ExpectedArtifact(BaseModel):
    """期望agent cli输出的结果类型"""

    path: str
    kind: ArtifactKind = "other"
    required: bool = True


class EvalCheck(BaseModel):
    """agent cli输出结果的评估项"""

    id: str
    kind: Literal["file_exists", "command", "manual"]
    target: str | None = None
    command: list[str] | None = None


class TaskSpec(BaseModel):
    """任务定义"""

    task_id: str
    title: str
    cwd: Path
    agent: AgentConfig
    prompt: PromptSpec
    expected_artifacts: list[ExpectedArtifact] = Field(default_factory=list)
    eval_checks: list[EvalCheck] = Field(default_factory=list)
    max_attempts: int = 2
    timeout_seconds: int = 600


class AgentEvent(BaseModel):
    """
    agent cli 事件
    """

    run_id: str
    seq: int
    type: Literal[
        "status",
        "text_delta",
        "thinking_delta",
        "tool_use",
        "tool_result",
        "artifact",
        "usage",
        "error",
        "raw",
    ]

    # 通用文本
    text: str | None = None

    # 工具调用相关
    tool_name: str | None = None
    tool_input: Any | None = None
    tool_output: str | None = None
    is_error: bool | None = None

    # 产物相关
    artifact_path: str | None = None

    # 错误相关
    error_message: str | None = None

    # 保留原始事件，方便排查 parser 问题
    raw: Any | None = None


class RunRecord(BaseModel):
    """
    一次 agent 子进程运行记录。

    一个 Task 可能会有多次 Run：
    - 第一次执行
    - 评估失败后的修复执行
    """

    run_id: str
    task_id: str
    attempt: int
    status: RunStatus
    cwd: Path
    command: list[str]

    started_at: float | None = None
    ended_at: float | None = None

    exit_code: int | None = None
    error_message: str | None = None

    # 事件日志路径，一般是 .runner/runs/<run_id>/events.jsonl
    event_log_path: Path


class ArtifactRecord(BaseModel):
    """
    实际收集到的产物记录。

    可以来自：
    - expected_artifacts 中声明的路径
    - 扫描 cwd 后发现的新文件
    - agent 显式上报的 artifact 事件
    """

    task_id: str
    run_id: str
    path: Path
    kind: ArtifactKind = "other"
    exists: bool
    size_bytes: int | None = None


class CheckResult(BaseModel):
    """
    单个检查项结果。
    最小版本先支持 file_exists / command 两类就够了。
    """

    name: str
    passed: bool
    message: str = ""
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""


class EvalResult(BaseModel):
    """
    一次 run 的评估结果。

    """

    run_id: str
    task_id: str
    passed: bool
    checks: list[CheckResult] = Field(default_factory=list)
    summary: str = ""


class RetryDecision(BaseModel):
    """
    是否需要重试，以及重试时给 agent 的修复提示。

    注意：重试不是简单重复原 prompt。
    更好的方式是把失败原因注入进去，让 agent 在同一个 cwd 里修复。
    """

    should_retry: bool
    reason: str
    repair_prompt: str | None = None


class TaskResult(BaseModel):
    """一个任务的最终结果"""

    task_id: str
    status: RunStatus
    runs: list[RunRecord] = Field(default_factory=list)
    artifacts: list[ArtifactRecord] = Field(default_factory=list)
    evaluations: list[EvalResult] = Field(default_factory=list)
    attempts: int = 0
    summary: str = ""

    @property
    def result(self) -> bool:
        return self.status == RunStatus.succeeded
