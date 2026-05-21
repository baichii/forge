from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from forge.core.specs import TickAgentParams, TickAgentSpec


class TickAgent(ABC):
    """Realtime agent contract driven by repeated step calls."""

    declaration: TickAgentSpec | None = None

    def __init__(self, params: TickAgentParams):
        self._params = params
        self.params = params.params

    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def step(self, *args, **kwargs) -> tuple[list, dict[str, bool], bool, dict[str, Any]]:
        """执行step

        Returns:
            action: list 动作列表, 每个元素是一个dict
            status: dict[str, bool] 状态描述, 智能体中定义的每个状态都需要返回一个bool值 {status: bool}
            done: bool 智能体是否运行结束
            info: dict | None 额外信息
        """

    @property
    def name(self):
        """智能体类型名称"""
        return self._params.agent_name

    @property
    def id(self):
        """智能体实例化执行唯一id"""
        return self._params.agent_instance_id

    @property
    def side(self):
        return self._params.side


class TaskAgent(ABC):
    """Async task-oriented agent contract, suitable for LLM workflows."""

    @abstractmethod
    async def run(self, task: Any, context: Any | None = None) -> Any:
        raise NotImplementedError
