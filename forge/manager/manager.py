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
    async def update(self, **kwargs) -> None:
        """Update manager state from environment data."""
        raise NotImplementedError
