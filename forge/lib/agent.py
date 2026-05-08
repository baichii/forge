from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TickAgent(ABC):
    """Realtime agent contract driven by repeated step calls."""

    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def step(self, observation: Any | None = None) -> Any:
        raise NotImplementedError


class TaskAgent(ABC):
    """Async task-oriented agent contract, suitable for LLM workflows."""

    @abstractmethod
    async def run(self, task: Any, context: Any | None = None) -> Any:
        raise NotImplementedError
