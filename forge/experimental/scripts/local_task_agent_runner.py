"""测试调用本地的codex/claude code执行任务"""

import queue
import subprocess
import threading
import time
from dataclasses import dataclass, field


@dataclass
class Message:
    role: str
    content: str


@dataclass
class AgentSession:
    history: list[Message] = field(default_factory=list)

    def build_prompt(self, user_input: str) -> str:
        """
        构建上下文 prompt
        """

        self.history.append(Message("user", user_input))

        prompt = []

        for msg in self.history[-10:]:
            prompt.append(f"{msg.role.upper()}:\n{msg.content}")

        prompt.append("ASSISTANT:")

        return "\n\n".join(prompt)

    def append_assistant(self, content: str):
        self.history.append(Message("assistant", content))


class RuntimeAdapter:
    """
    Claude/Codex runtime adapter
    """

    def __init__(
        self,
        command: list[str],
        timeout: int = 300,
    ):
        self.command = command
        self.timeout = timeout

    def run(self, prompt: str) -> str:
        """
        执行一次 agent
        """

        full_cmd = self.command + [prompt]

        print("\n[spawn]", " ".join(full_cmd))

        process = subprocess.Popen(
            full_cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        stdout_queue = queue.Queue()
        stderr_queue = queue.Queue()

        def read_stdout():
            for line in process.stdout:
                stdout_queue.put(line)

        def read_stderr():
            for line in process.stderr:
                stderr_queue.put(line)

        threading.Thread(target=read_stdout, daemon=True).start()
        threading.Thread(target=read_stderr, daemon=True).start()

        start_time = time.time()

        assistant_output = []

        while True:
            if process.poll() is not None:
                break

            if time.time() - start_time > self.timeout:
                process.kill()
                raise TimeoutError("Agent timeout")

            try:
                line = stdout_queue.get(timeout=0.1)

                print(line, end="", flush=True)

                assistant_output.append(line)

            except queue.Empty:
                pass

            while not stderr_queue.empty():
                err = stderr_queue.get()

                print(f"\n[stderr] {err}", end="")

        process.wait()

        return "".join(assistant_output)


def main():
    """
    多轮会话 demo
    """

    # 改成 claude 也行
    runtime = RuntimeAdapter(
        command=["codex", "exec"],
        timeout=300,
    )

    session = AgentSession()

    print("=" * 60)
    print("Multi-turn Agent Demo")
    print("type 'exit' to quit")
    print("=" * 60)

    while True:
        user_input = input("\nUSER > ")

        if user_input.strip() == "exit":
            break

        prompt = session.build_prompt(user_input)

        try:
            result = runtime.run(prompt)

            session.append_assistant(result)

        except Exception as e:
            print("\n[ERROR]", e)


if __name__ == "__main__":
    main()
