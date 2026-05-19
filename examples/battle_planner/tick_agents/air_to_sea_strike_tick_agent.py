from __future__ import annotations

from typing import Any

from battle_planner.adapters.scenario_loader import ensure_pythonlib_path
from battle_planner.tick_agents.base import TickAgent, TickAgentRuntimeContext
from pydantic import BaseModel

from forge.utils.specs import ParamSpec, ParamSpecTemplate, ParamType, TickAgentSpec

ensure_pythonlib_path()
from pysim.schema.action import MissionFormatter  # noqa: E402

TASK_TYPE = "NavalAsuWStrike_Air"


class AirToSeaStrikeParams(BaseModel):
    start_time: float
    end_time: float
    unit_ids: list[str]
    target_ids: list[str]
    wp_num: int = 2
    clear_targets: bool = True


declaration = TickAgentSpec(
    name="air_to_sea_strike_agent",
    version="0.1.0",
    entrypoint="battle_planner.tick_agents.air_to_sea_strike_tick_agent:Agent",
    description=f"""# 空对海打击智能体

在指定时间窗口内组织空中单位对海上目标执行打击任务。

## 适用场景
- 固定海上目标打击。
- 红方不主动防御或防御影响暂不建模。
- 以摧毁关键海上目标为主要目标，并关注武器消耗。

## 行为逻辑
智能体在 `start_time <= sim_time <= end_time` 且尚未下发过任务时，输出一次 `{TASK_TYPE}` 类型任务。

## 输出说明
输出由 `pysim.schema.action.MissionFormatter.air_attack` 构建的标准 mission action。
""",
    status=["running", "finished"],
    params={
        "start_time": ParamSpec.start_time.redeclaration(type=ParamType.FLOAT, description="智能体开始运行时间，单位秒。"),
        "end_time": ParamSpec.end_time.redeclaration(type=ParamType.FLOAT, description="智能体停止运行时间，单位秒。"),
        "unit_ids": ParamSpec.unit_ids.redeclaration(description="执行任务的飞机单位 id 列表。"),
        "target_ids": ParamSpec.target_ids.redeclaration(description="海上目标单位 id 列表。"),
        "wp_num": ParamSpecTemplate(
            name="wp_num",
            description="每个目标分配的武器数量。",
            type=ParamType.INT,
            required=False,
            default_value=2,
            examples=[1, 2, 4],
            other={"min_value": 1},
        ),
        "clear_targets": ParamSpecTemplate(
            name="clear_targets",
            description="是否清理旧目标。",
            type=ParamType.BOOL,
            required=False,
            default_value=True,
        ),
    },
)


class Agent(TickAgent):
    declaration = declaration

    def __init__(self, params: AirToSeaStrikeParams):
        super().__init__(params=params)
        self._dispatched = False

    def reset(self) -> None:
        self._dispatched = False

    def step(self, observation: dict[str, Any]) -> tuple[list, dict[str, bool], bool, dict[str, Any]]:
        sim_time = float(observation.get("sim_time", observation.get("time", 0.0)))
        status = {
            "running": self.params.start_time <= sim_time <= self.params.end_time and not self._dispatched,
            "finished": self._dispatched or sim_time > self.params.end_time,
        }
        if self._dispatched:
            return [], status, True, {"reason": "mission_already_dispatched", "sim_time": sim_time}
        if sim_time < self.params.start_time or sim_time > self.params.end_time:
            done = sim_time > self.params.end_time
            reason = "before_start_time" if sim_time < self.params.start_time else "after_end_time"
            return [], status, done, {"reason": reason, "sim_time": sim_time}

        self._dispatched = True
        actions = [
            MissionFormatter.air_attack(
                unit_ids=self.params.unit_ids,
                target_id=target_id,
                wp_num=self.params.wp_num,
                clear_targets=self.params.clear_targets if index == 0 else False,
            )
            for index, target_id in enumerate(self.params.target_ids)
        ]
        status = {
            "running": False,
            "finished": True,
        }
        return actions, status, True, {
            "reason": "mission_dispatched",
            "sim_time": sim_time,
            "task_type": TASK_TYPE,
            "source": self.runtime_context.agent_name,
        }
