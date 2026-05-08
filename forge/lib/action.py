from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from forge.lib.entity import EntityRef
    from forge.manager.hub import ManagerHub


@dataclass(frozen=True)
class ActionIntent:
    """Planner-facing action intent."""

    name: str
    actor: "EntityRef"
    target: "EntityRef | None" = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionCommand:
    """Environment-facing executable command."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    env_id: str | None = None


@dataclass(frozen=True)
class ActionResult:
    ok: bool
    message: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionParams:
    params: dict[str, Any]
    camp_id: str | int
    agent_name: str
    action_id: Union[int | str]


class ActionState(StrEnum):
    Ready = "ready"
    Pending = "pending"


class Action:
    """Action definition with a manager-backed lifecycle."""

    def __init__(self, action_params: ActionParams, manager_hub: "ManagerHub"):
        self.camp_id = action_params.camp_id
        self.agent_name = action_params.agent_name
        self.action_id = action_params.action_id
        self.manager_hub = manager_hub

    @abstractmethod
    def build(self) -> ActionState:
        """Initialize or transition action state."""

    def step(self) -> tuple:
        """"""
