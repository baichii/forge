"""以接近 OpenCode TUI 的形式查看事件流。

这个文件同时保留少量纯渲染测试。手动查看事件时运行：

    uv run python forge/tests/experimental/test_opencode_event.py

默认会自动跟随第一个出现消息事件的 session。需要指定 session 或查看原始事件时：

    uv run python forge/tests/experimental/test_opencode_event.py --session-id ses_xxx
    uv run python forge/tests/experimental/test_opencode_event.py --raw --all-sessions
"""

from __future__ import annotations

import argparse
import asyncio
import io
import json
import sys
from pprint import pprint
from typing import Any, TextIO

from opencode_ai import AsyncOpencode


class Ansi:
    """终端颜色。"""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    CLEAR_LINE = "\r\033[2K"


def _event_dict(event: Any) -> dict[str, Any]:
    """将 SDK Model 和测试字典统一转换成普通字典。"""

    if isinstance(event, dict):
        return event
    if hasattr(event, "model_dump"):
        # OpenCode 新增 part 类型时，SDK 的联合类型可能暂时落后；关闭序列化告警仍可取得原始字段。
        return event.model_dump(by_alias=True, warnings=False)
    if hasattr(event, "to_dict"):
        return event.to_dict()
    raise TypeError(f"不支持的事件类型: {type(event)!r}")


def _session_id(payload: dict[str, Any]) -> str | None:
    properties = payload.get("properties") or {}
    part = properties.get("part") or {}
    info = properties.get("info") or {}
    return (
        part.get("sessionID")
        or part.get("session_id")
        or info.get("sessionID")
        or info.get("session_id")
        or properties.get("sessionID")
        or properties.get("session_id")
    )


def _duration(state: dict[str, Any]) -> str:
    time_info = state.get("time") or {}
    start = time_info.get("start")
    end = time_info.get("end")
    if not isinstance(start, int | float) or not isinstance(end, int | float):
        return ""
    seconds = max(0.0, (end - start) / 1000)
    return f" {seconds:.1f}s"


def _compact_input(value: Any, limit: int = 160) -> str:
    if value in (None, {}, []):
        return ""
    rendered = json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)
    rendered = " ".join(rendered.split())
    if len(rendered) > limit:
        return f"{rendered[: limit - 1]}…"
    return rendered


class OpenCodeEventRenderer:
    """将高频 OpenCode 事件聚合成可读的终端时间线。"""

    def __init__(
        self,
        *,
        session_id: str | None = None,
        all_sessions: bool = False,
        raw: bool = False,
        show_tool_output: bool = False,
        color: bool = True,
        stream: TextIO | None = None,
    ) -> None:
        self.stream = stream or sys.stdout
        self.session_id = session_id
        self.all_sessions = all_sessions
        self.raw = raw
        self.show_tool_output = show_tool_output
        self.color = color and bool(getattr(self.stream, "isatty", lambda: False)())
        self.messages: dict[str, dict[str, Any]] = {}
        self.text_by_part: dict[str, str] = {}
        self.tool_status_by_part: dict[str, str] = {}
        self.reasoning_parts: set[str] = set()
        self.header_messages: set[str] = set()
        self.open_text_message: str | None = None
        self.transient_tool_part: str | None = None

    def handle(self, event: Any) -> None:
        """处理一个 SDK 事件。"""

        payload = _event_dict(event)
        if self.raw:
            pprint(payload, stream=self.stream, sort_dicts=False)
            return

        event_type = payload.get("type", "unknown")
        event_session_id = _session_id(payload)
        if event_type.startswith("message."):
            if not self._accept_session(event_session_id):
                return
        elif event_session_id and not self._matches_session(event_session_id):
            return

        if event_type == "message.updated":
            self._handle_message(payload)
        elif event_type == "message.part.updated":
            self._handle_part(payload)
        elif event_type == "permission.updated":
            self._handle_permission(payload)
        elif event_type == "session.error":
            self._handle_session_error(payload)
        elif event_type == "session.idle":
            self._end_text()
            self._finish_transient()
            self._line(self._styled("○ session idle", Ansi.DIM))

    def _accept_session(self, event_session_id: str | None) -> bool:
        if self.all_sessions:
            return True
        if self.session_id is None and event_session_id:
            self.session_id = event_session_id
            self._line(self._styled(f"following session {event_session_id}", Ansi.DIM))
        return self._matches_session(event_session_id)

    def _matches_session(self, event_session_id: str | None) -> bool:
        return self.all_sessions or self.session_id is None or event_session_id == self.session_id

    def _handle_message(self, payload: dict[str, Any]) -> None:
        info = (payload.get("properties") or {}).get("info") or {}
        message_id = info.get("id")
        if message_id:
            self.messages[message_id] = info
        error = info.get("error")
        if error:
            self._end_text()
            self._finish_transient()
            self._line(self._styled(f"message error: {_compact_input(error, 500)}", Ansi.RED))

    def _handle_part(self, payload: dict[str, Any]) -> None:
        part = (payload.get("properties") or {}).get("part") or {}
        part_type = part.get("type")
        if part_type == "text":
            self._handle_text(part)
        elif part_type == "reasoning":
            self._handle_reasoning(part)
        elif part_type == "tool":
            self._handle_tool(part)
        elif part_type == "step-finish":
            self._handle_step_finish(part)
        elif part_type == "file":
            self._end_text()
            filename = part.get("filename") or part.get("url") or "file"
            self._line(self._styled(f"  attachment {filename}", Ansi.DIM))
        elif part_type == "patch":
            self._end_text()
            files = ", ".join(part.get("files") or [])
            self._line(self._styled(f"  patch {files}", Ansi.GREEN))

    def _handle_text(self, part: dict[str, Any]) -> None:
        if part.get("synthetic"):
            return

        part_id = str(part.get("id", ""))
        message_id = str(part.get("messageID") or part.get("message_id") or "")
        text = str(part.get("text") or "")
        previous = self.text_by_part.get(part_id, "")
        if text == previous:
            return

        self._finish_transient()
        self._ensure_message_header(message_id)
        if text.startswith(previous):
            delta = text[len(previous) :]
        else:
            self._end_text()
            self._line(self._styled("  text revised", Ansi.DIM))
            delta = text

        self.stream.write(delta)
        self.stream.flush()
        self.text_by_part[part_id] = text
        self.open_text_message = message_id

        time_info = part.get("time") or {}
        if time_info.get("end") is not None:
            self._end_text()

    def _handle_reasoning(self, part: dict[str, Any]) -> None:
        """默认折叠推理正文，只显示一次状态提示。"""

        part_id = str(part.get("id", ""))
        if part_id in self.reasoning_parts:
            return
        self.reasoning_parts.add(part_id)
        message_id = str(part.get("messageID") or part.get("message_id") or "")
        self._finish_transient()
        self._ensure_message_header(message_id)
        self._line(self._styled("  ◇ thinking…", Ansi.DIM))

    def _ensure_message_header(self, message_id: str) -> None:
        if message_id in self.header_messages:
            return
        self._end_text()
        info = self.messages.get(message_id, {})
        role = info.get("role", "assistant")
        if role == "user":
            label = self._styled("you", Ansi.BLUE, Ansi.BOLD)
        else:
            details = [
                info.get("agent") or info.get("mode"),
                info.get("modelID") or info.get("api_model_id"),
            ]
            suffix = " · ".join(str(item) for item in details if item)
            label = "assistant" if not suffix else f"assistant · {suffix}"
            label = self._styled(label, Ansi.MAGENTA, Ansi.BOLD)
        self._line("")
        self._line(label)
        self.header_messages.add(message_id)

    def _handle_tool(self, part: dict[str, Any]) -> None:
        self._end_text()
        part_id = str(part.get("id", ""))
        state = part.get("state") or {}
        status = str(state.get("status", "unknown"))
        previous_status = self.tool_status_by_part.get(part_id)
        if status == previous_status:
            return
        self.tool_status_by_part[part_id] = status

        tool = str(part.get("tool") or "tool")
        title = str(state.get("title") or tool)
        if title == tool:
            compact_input = _compact_input(state.get("input"))
            if compact_input:
                title = f"{tool} {compact_input}"

        if status == "pending":
            return
        if status == "running":
            self._show_running_tool(part_id, title)
            return

        self._finish_transient(rewrite=part_id == self.transient_tool_part)
        if status == "completed":
            self._line(self._styled(f"  ✓ {title}{_duration(state)}", Ansi.GREEN))
            if self.show_tool_output:
                self._show_output(str(state.get("output") or ""))
        elif status == "error":
            self._line(self._styled(f"  ✗ {title}{_duration(state)}", Ansi.RED))
            self._show_output(str(state.get("error") or "unknown tool error"))

    def _show_running_tool(self, part_id: str, title: str) -> None:
        self._finish_transient()
        line = self._styled(f"  ● {title}", Ansi.CYAN)
        if self.color:
            self.stream.write(f"{Ansi.CLEAR_LINE}{line}")
            self.stream.flush()
            self.transient_tool_part = part_id
        else:
            self._line(line)

    def _show_output(self, output: str, max_lines: int = 8, max_chars: int = 1200) -> None:
        output = output.strip()
        if not output:
            return
        clipped = output[:max_chars]
        lines = clipped.splitlines()
        visible = lines[:max_lines]
        for line in visible:
            self._line(self._styled(f"      {line}", Ansi.DIM))
        if len(lines) > max_lines or len(output) > max_chars:
            self._line(self._styled("      … output truncated", Ansi.DIM))

    def _handle_step_finish(self, part: dict[str, Any]) -> None:
        self._end_text()
        self._finish_transient()
        tokens = part.get("tokens") or {}
        total = tokens.get("total")
        if total is None:
            total = sum(float(tokens.get(name) or 0) for name in ("input", "output", "reasoning"))
        cost = float(part.get("cost") or 0)
        reason = part.get("reason")
        fields = [f"{int(total):,} tokens", f"${cost:.4f}"]
        if reason:
            fields.append(str(reason))
        self._line(self._styled(f"  ─ {' · '.join(fields)}", Ansi.DIM))

    def _handle_permission(self, payload: dict[str, Any]) -> None:
        self._end_text()
        self._finish_transient()
        properties = payload.get("properties") or {}
        title = properties.get("title") or "permission required"
        self._line(self._styled(f"  ! {title}", Ansi.YELLOW))

    def _handle_session_error(self, payload: dict[str, Any]) -> None:
        self._end_text()
        self._finish_transient()
        error = (payload.get("properties") or {}).get("error") or "unknown session error"
        self._line(self._styled(f"session error: {_compact_input(error, 500)}", Ansi.RED))

    def _end_text(self) -> None:
        if self.open_text_message is not None:
            last_text = next(reversed(self.text_by_part.values()), "")
            if not last_text.endswith("\n"):
                self.stream.write("\n")
                self.stream.flush()
            self.open_text_message = None

    def _finish_transient(self, *, rewrite: bool = False) -> None:
        if self.transient_tool_part is None:
            return
        if rewrite and self.color:
            self.stream.write(Ansi.CLEAR_LINE)
        else:
            self.stream.write("\n")
        self.stream.flush()
        self.transient_tool_part = None

    def _styled(self, text: str, *styles: str) -> str:
        if not self.color:
            return text
        return f"{''.join(styles)}{text}{Ansi.RESET}"

    def _line(self, text: str) -> None:
        self._end_text()
        self.stream.write(f"{text}\n")
        self.stream.flush()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="以精简 TUI 形式查看 OpenCode 事件流")
    parser.add_argument("--base-url", default="http://127.0.0.1:4096")
    parser.add_argument("--session-id", help="只查看指定 session；默认自动跟随首个消息 session")
    parser.add_argument("--all-sessions", action="store_true", help="同时查看所有 session")
    parser.add_argument("--raw", action="store_true", help="打印全部原始事件，供调试使用")
    parser.add_argument("--tool-output", action="store_true", help="显示已完成工具的输出摘要")
    parser.add_argument("--no-color", action="store_true", help="禁用 ANSI 颜色和单行状态刷新")
    return parser.parse_args()


async def watch_events(args: argparse.Namespace) -> None:
    """连接 OpenCode SSE 并持续渲染事件。"""

    client = AsyncOpencode(base_url=args.base_url)
    renderer = OpenCodeEventRenderer(
        session_id=args.session_id,
        all_sessions=args.all_sessions,
        raw=args.raw,
        show_tool_output=args.tool_output,
        color=not args.no_color,
    )
    print(f"connecting to {args.base_url} ...")
    stream = await client.event.list()
    print("connected. waiting for OpenCode events (Ctrl-C to stop)")
    async for event in stream:
        renderer.handle(event)


def main() -> None:
    try:
        asyncio.run(watch_events(_parse_args()))
    except KeyboardInterrupt:
        print("\nstopped.")


def _part_event(part: dict[str, Any]) -> dict[str, Any]:
    return {"type": "message.part.updated", "properties": {"part": part}}


def test_renderer_prints_only_text_delta() -> None:
    output = io.StringIO()
    renderer = OpenCodeEventRenderer(color=False, stream=output)
    common = {"id": "part-1", "messageID": "message-1", "sessionID": "session-1", "type": "text"}

    renderer.handle(_part_event({**common, "text": "hello"}))
    renderer.handle(_part_event({**common, "text": "hello world", "time": {"start": 1, "end": 2}}))

    rendered = output.getvalue()
    assert rendered.count("hello") == 1
    assert "hello world" in rendered


def test_renderer_hides_duplicate_tool_state() -> None:
    output = io.StringIO()
    renderer = OpenCodeEventRenderer(color=False, stream=output)
    tool_part = {
        "id": "part-tool",
        "messageID": "message-1",
        "sessionID": "session-1",
        "type": "tool",
        "tool": "read",
        "state": {"status": "running", "title": "Read Makefile", "time": {"start": 1}},
    }

    renderer.handle(_part_event(tool_part))
    renderer.handle(_part_event(tool_part))

    assert output.getvalue().count("Read Makefile") == 1


def test_renderer_collapses_reasoning_updates() -> None:
    output = io.StringIO()
    renderer = OpenCodeEventRenderer(color=False, stream=output)
    common = {
        "id": "part-reasoning",
        "messageID": "message-1",
        "sessionID": "session-1",
        "type": "reasoning",
    }

    renderer.handle(_part_event({**common, "text": "first thought"}))
    renderer.handle(_part_event({**common, "text": "first thought and more"}))

    rendered = output.getvalue()
    assert rendered.count("thinking") == 1
    assert "first thought" not in rendered


if __name__ == "__main__":
    main()
