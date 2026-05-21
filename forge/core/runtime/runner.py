from __future__ import annotations

from typing import Any, Protocol

from forge.core.lib.agent import TickAgent
from forge.core.lib.callback import CallBackList
from forge.core.specs import CallbackParams, EnvParams, TickAgentParams


class Runner(Protocol):
    """test runner protocol

    Notes:
        1. 开发过程中发现通过配置参数，定义环境创建/连接的形式其实是很痛duiqi苦的，即使是最小测试场景下
            需要兼容的创建模式有gym/docker
            需要兼容的连接模式有gym/infoman/custom


    """

    def __init__(
        self,
        env_params: EnvParams,
        tick_agents: list[TickAgent | TickAgentParams],
        callbacks: CallBackList | list[CallbackParams],
    ) -> None:
        """Initialize the runner with runtime parameters."""

    def run(self, max_step) -> Any:
        """Run an agent against an environment or environment connection."""
        ...
