from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from forge.manager.hub import ManagerHub


class Manager(metaclass=ABCMeta):
    """Base class for a single state or judgement manager."""

    def __init__(self, agent: object, config: dict, manager_hub: "ManagerHub"):
        super().__init__()
        self.agent = agent
        self.config = config
        self.manager_hub = manager_hub

    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError

    def initialise(self) -> None:
        """Initialize manager state before receiving observations."""
        pass

    @abstractmethod
    def update(self, **kwargs) -> None:
        """Update manager state from environment data.

        Note:
            1. 并非所有manager都需要维护update方法

        """
        raise NotImplementedError
