from __future__ import annotations

from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
import enum
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from forge.manager.hub import ManagerHub


@dataclass
class ActionParams:
    """行动参数, 阵营参数"""

    params: dict[str, Any]  # 行动参数
    persistent: bool  # 是否是持续性命令
    camp_id: str | int  # 行动主语阵营
    side_id: str | int  # 行动主语side
    agent_name: str  # 下发这个指令的智能体
    action_id: str | int | None = None  # 行动id，全局唯一，在action_manager中生成, 由action_manager维护


class ActionStatus(enum.StrEnum):
    """标记action的运行状态表示, 逻辑状态，非业务层面状态(描述状态)"""

    Invalid = enum.auto()
    Created = enum.auto()
    Waiting = enum.auto()
    Ready = enum.auto()
    Running = enum.auto()
    Paused = enum.auto()
    Exited = enum.auto()
    Error = enum.auto()


class Action(metaclass=ABCMeta):
    """Action definition with a manager-backed lifecycle."""

    def __init__(self, action_params: ActionParams, manager_hub: "ManagerHub"):
        self.action_params = action_params
        self.params = action_params.params
        self.manager_hub = manager_hub
        self.action_status = ActionStatus.Created

    @abstractmethod
    def build(self) -> ActionStatus:
        """Initialize or transition action state."""

    def step(self) -> tuple:
        """step入口方法, 仅用于hook/callback挂载, 不要直接修改这个方法"""
        return self._step_implement()

    @abstractmethod
    def _step_implement(self) -> tuple:
        """step具体实现方法"""

    @property
    def camp_id(self):
        return self.action_params.camp_id

    @property
    def side_id(self):
        return self.action_params.side_id

    @property
    def agent_name(self):
        return self.action_params.agent_name

    @property
    def action_id(self):
        return self.action_params.action_id
