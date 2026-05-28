from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from forge.experimental.acp.specs import AgentCli, AgentEvent, RunRecord, RunStatus, TaskSpec


@dataclass
class CliRunResult:
    run: RunRecord
    events: list[AgentEvent]


def run_cli_agent(task: TaskSpec, *, run_id: str, attempt: int, prompt: str) -> CliRunResult:
    task.cwd.mkdir(parents=True, exist_ok=True)
    run_dir = task.cwd / ".acp" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    event_log_path = run_dir / "events.jsonl"
    command = build_command(task)
    started_at = time.time()
    events: list[AgentEvent] = [AgentEvent(run_id=run_id, seq=0, type="status", text="running")]

    run = RunRecord(
        run_id=run_id,
        task_id=task.task_id,
        attempt=attempt,
        status=RunStatus.running,
        cwd=task.cwd,
        command=command,
        started_at=started_at,
        event_log_path=event_log_path,
    )

    try:
        process = subprocess.Popen(
            command,
            cwd=task.cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(prompt, timeout=task.timeout_seconds)
        run.exit_code = process.returncode
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        run.exit_code = process.returncode
        run.error_message = f"agent timed out after {task.timeout_seconds}s"
        events.append(
            AgentEvent(
                run_id=run_id,
                seq=len(events),
                type="error",
                error_message=run.error_message,
            )
        )
    except Exception as exc:
        stdout = ""
        stderr = ""
        run.exit_code = None
        run.error_message = f"agent failed to start: {exc}"
        events.append(
            AgentEvent(
                run_id=run_id,
                seq=len(events),
                type="error",
                error_message=run.error_message,
            )
        )

    events.extend(_parse_stream(run_id, len(events), "stdout", stdout))
    events.extend(_parse_stream(run_id, len(events), "stderr", stderr))

    if run.exit_code == 0 and run.error_message is None:
        run.status = RunStatus.succeeded
        events.append(AgentEvent(run_id=run_id, seq=len(events), type="status", text="succeeded"))
    else:
        run.status = RunStatus.failed
        if run.error_message is None:
            run.error_message = f"agent exited with code {run.exit_code}"
        events.append(
            AgentEvent(
                run_id=run_id,
                seq=len(events),
                type="error",
                error_message=run.error_message,
            )
        )

    run.ended_at = time.time()
    _write_event_log(event_log_path, events)
    return CliRunResult(run=run, events=events)


def build_command(task: TaskSpec) -> list[str]:
    config = task.agent
    if config.agent == AgentCli.codex:
        command = [
            config.bin,
            "exec",
            "--json",
            "--skip-git-repo-check",
            "--sandbox",
            "workspace-write",
            "-C",
            str(task.cwd),
        ]
        if config.model:
            command.extend(["--model", config.model])
        command.extend(config.extra_args)
        return command

    if config.agent == AgentCli.claude:
        command = [
            config.bin,
            "-p",
            "--input-format",
            "text",
            "--output-format",
            "stream-json",
            "--verbose",
            "--permission-mode",
            "bypassPermissions",
        ]
        if config.model:
            command.extend(["--model", config.model])
        command.extend(config.extra_args)
        return command

    raise ValueError(f"unsupported agent cli: {config.agent}")


def _write_event_log(path: Path, events: list[AgentEvent]) -> None:
    path.write_text(
        "".join(f"{event.model_dump_json()}\n" for event in events),
        encoding="utf-8",
    )


def _parse_stream(run_id: str, start_seq: int, stream: str, content: str) -> list[AgentEvent]:
    events: list[AgentEvent] = []
    for line in content.splitlines():
        seq = start_seq + len(events)
        if not line.strip():
            continue
        if stream == "stderr":
            events.append(
                AgentEvent(
                    run_id=run_id,
                    seq=seq,
                    type="raw",
                    text=line,
                    raw={"stream": stream, "line": line},
                )
            )
            continue
        events.append(_parse_stdout_line(run_id, seq, line))
    return events


def _parse_stdout_line(run_id: str, seq: int, line: str) -> AgentEvent:
    try:
        raw = json.loads(line)
    except json.JSONDecodeError:
        return AgentEvent(
            run_id=run_id,
            seq=seq,
            type="raw",
            text=line,
            raw={"stream": "stdout", "line": line},
        )
    if not isinstance(raw, dict):
        return AgentEvent(run_id=run_id, seq=seq, type="raw", raw=raw)

    event_type = str(raw.get("type") or raw.get("event") or "")
    lowered = event_type.lower()
    text = _first_text(raw, ("text", "delta", "message", "content"))

    if "artifact" in lowered or "file_write" in lowered:
        path = _first_text(raw, ("path", "artifact_path", "file"))
        return AgentEvent(run_id=run_id, seq=seq, type="artifact", artifact_path=path, raw=raw)
    if "thinking" in lowered or "thought" in lowered or "reasoning" in lowered:
        return AgentEvent(run_id=run_id, seq=seq, type="thinking_delta", text=text, raw=raw)
    if "tool_result" in lowered or "tool.result" in lowered:
        return AgentEvent(
            run_id=run_id,
            seq=seq,
            type="tool_result",
            tool_name=_first_text(raw, ("name", "tool_name")),
            tool_output=_stringify(raw.get("output") or raw.get("result")),
            is_error=bool(raw.get("is_error", False)),
            raw=raw,
        )
    if "tool" in lowered and ("call" in lowered or "use" in lowered or "start" in lowered):
        return AgentEvent(
            run_id=run_id,
            seq=seq,
            type="tool_use",
            tool_name=_first_text(raw, ("name", "tool_name")),
            tool_input=raw.get("input") or raw.get("args"),
            raw=raw,
        )
    if "usage" in lowered:
        return AgentEvent(run_id=run_id, seq=seq, type="usage", raw=raw)
    if text and ("message" in lowered or "assistant" in lowered or "delta" in lowered):
        return AgentEvent(run_id=run_id, seq=seq, type="text_delta", text=text, raw=raw)
    return AgentEvent(run_id=run_id, seq=seq, type="raw", text=text, raw=raw)


def _first_text(raw: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = raw.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            nested = _first_text(value, keys)
            if nested:
                return nested
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    return item
                if isinstance(item, dict):
                    nested = _first_text(item, keys)
                    if nested:
                        return nested
    return None


def _stringify(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)
