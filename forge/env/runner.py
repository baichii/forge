from __future__ import annotations

from typing import Any, Protocol

from forge.lib.agent import TickAgent
from forge.lib.callback import CallBackList
from forge.utils.specs import CallbackSpec, EnvSpec, TickAgentSpec


class Runner(Protocol):
    """test runner protocol

    Notes:
        1. 开发过程中发现通过配置参数，定义环境创建/连接的形式其实是很痛duiqi苦的，即使是最小测试场景下
            需要兼容的创建模式有gym/docker
            需要兼容的连接模式有gym/infoman/custom


    """

    def __init__(
        self,
        env_spec: EnvSpec,
        tick_agents: list[TickAgent | TickAgentSpec],
        callbacks: CallBackList | list[CallbackSpec],
    ) -> None:
        """Initialize the runner with a specification."""

    def run(self, max_step) -> Any:
        """Run an agent against an environment or environment connection."""
        ...
