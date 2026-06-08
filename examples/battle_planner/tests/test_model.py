import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return default


RUN_MODEL_TESTS = os.getenv("BATTLE_PLANNER_RUN_MODEL_TESTS", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

pytestmark = pytest.mark.skipif(
    not RUN_MODEL_TESTS,
    reason="set BATTLE_PLANNER_RUN_MODEL_TESTS=true to run live model probes",
)


def test_connection() -> None:
    client = OpenAI(
        api_key=_env("MODEL_OPENAI_GPT54_MINI_API_KEY"),
        base_url=_env("MODEL_OPENAI_GPT54_MINI_API_URL"),
    )

    response = client.chat.completions.create(
        model=_env("MODEL_OPENAI_GPT54_MINI_MODEL_NAME"),
        messages=[{"role": "user", "content": "hello"}],
    )

    assert len(response.choices[0].message.content) > 0, "Model response should not be empty"


def test_by_connection() -> None:
    client = OpenAI(
        api_key=_env("MODEL_BY_QWEN36_API_KEY"),
        base_url=_env("MODEL_BY_QWEN36_API_URL"),
    )

    response = client.chat.completions.create(
        model=_env("MODEL_BY_QWEN36_MODEL_NAME"),
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=1024,
    )

    message = response.choices[0].message
    content = message.content or getattr(message, "reasoning", None)
    print("content: ", content)
    assert content and len(content) > 0, "Model response should not be empty"


def test_by_stream_connection() -> None:
    client = OpenAI(
        api_key=_env("MODEL_BY_QWEN36_API_KEY"),
        base_url=_env("MODEL_BY_QWEN36_API_URL"),
    )

    stream = client.chat.completions.create(
        model=_env("MODEL_BY_QWEN36_MODEL_NAME"),
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=1024,
        stream=True,
    )

    chunks: list[str] = []
    for chunk in stream:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta
        text = delta.content or getattr(delta, "reasoning", None)
        if not text:
            continue

        chunks.append(text)

    content = "".join(chunks)
    assert content and len(content) > 0, "Stream response should not be empty"


def test_by_tool_call_connection() -> None:
    client = OpenAI(
        api_key=_env("MODEL_BY_QWEN36_API_KEY"),
        base_url=_env("MODEL_BY_QWEN36_API_URL"),
    )

    response = client.chat.completions.create(
        model=_env("MODEL_BY_QWEN36_MODEL_NAME"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a battle planner assistant. When the user asks "
                    "to query a task, call the provided tool instead of "
                    "answering in plain text."
                ),
            },
            {
                "role": "user",
                "content": "帮我查询 task_id 为 bp-20260514-0007 的方案优化任务当前状态。",
            },
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "scheme_query_tasks",
                    "description": "Query battle-planner optimization task status by task id.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The optimization task id to query.",
                            },
                            "include_logs": {
                                "type": "boolean",
                                "description": "Whether to include recent execution logs.",
                            },
                        },
                        "required": ["task_id"],
                        "additionalProperties": False,
                    },
                },
            }
        ],
        tool_choice="auto",
        max_tokens=1024,
    )

    choice = response.choices[0]
    message = choice.message
    print("finish_reason:", choice.finish_reason)
    print("content:", message.content)
    print("reasoning:", getattr(message, "reasoning", None))
    print("tool_calls:", message.tool_calls)

    assert choice.finish_reason == "tool_calls"
    assert message.tool_calls and len(message.tool_calls) > 0


if __name__ == "__main__":
    # test_connection()
    # test_by_connection()
    # test_by_stream_connection()
    test_by_tool_call_connection()
