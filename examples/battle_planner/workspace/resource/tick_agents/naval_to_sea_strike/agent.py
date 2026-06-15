from __future__ import annotations

from typing import Any

from pysim.schema.action import MissionFormatter

from forge.core.lib.agent import TickAgent
from forge.core.specs import ParamSpec, ParamSpecTemplate, ParamType, TickAgentParams, TickAgentSpec

declaration = TickAgentSpec(
    name="舰对海打击智能体",
    version="0.1.0",
    entrypoint="agent:Agent",
    description="""# 舰对海打击智能体

在指定时间窗口内组织水面舰艇使用舰载导弹打击海上目标。

## 适用场景
- 固定海上目标打击。
- 红方不主动防御或防御影响暂不建模。
- 可作为空对海打击后的补充打击手段。

## 行为逻辑
智能体在 `start_time <= sim_time <= end_time` 且尚未下发过任务时，输出一次 `舰对海打击智能体` 类型任务。

## 输出说明
输出由 `pysim.schema.action.MissionFormatter.attack` 构建的标准 mission action。
""",
    status=["运行中", "已结束"],
    params={
        "start_time": ParamSpec.start_time.redeclaration(
            type=ParamType.FLOAT, description="智能体开始运行时间，单位秒。"
        ),
        "end_time": ParamSpec.end_time.redeclaration(
            type=ParamType.FLOAT, description="智能体停止运行时间，单位秒。"
        ),
        "unit_ids": ParamSpec.unit_ids.redeclaration(description="执行任务的舰艇单位 id 列表。"),
        "target_ids": ParamSpec.target_ids.redeclaration(description="海上目标单位 id 列表。"),
        "wp_num": ParamSpecTemplate(
            name="舰载导弹数量",
            description="每个目标分配的舰载导弹数量。",
            type=ParamType.INT,
            required=False,
            default_value=2,
            examples=[1, 2, 4],
            other={"min_value": 1},
        ),
        "clear_targets": ParamSpecTemplate(
            name="清理旧目标",
            description="是否清理旧目标。",
            type=ParamType.BOOL,
            required=False,
            default_value=True,
        ),
    },
)


class Agent(TickAgent):
    declaration = declaration

    def __init__(self, params: TickAgentParams):
        super().__init__(params=params)
        self._dispatched = False

    def reset(self) -> None:
        self._dispatched = False

    def step(self, observation: dict[str, Any]) -> tuple[list, dict[str, bool], bool, dict[str, Any]]:
        sim_time = float(observation.get("sim_time", observation.get("time", 0.0)))
        start_time = float(self.params["start_time"])
        end_time = float(self.params["end_time"])
        status = {
            "运行中": start_time <= sim_time <= end_time and not self._dispatched,
            "已结束": self._dispatched or sim_time > end_time,
        }
        if self._dispatched:
            return [], status, True, {"reason": "mission_already_dispatched", "sim_time": sim_time}
        if sim_time < start_time or sim_time > end_time:
            done = sim_time > end_time
            reason = "before_start_time" if sim_time < start_time else "after_end_time"
            return [], status, done, {"reason": reason, "sim_time": sim_time}

        self._dispatched = True
        actions = [
            MissionFormatter.attack(
                unit_ids=self.params["unit_ids"],
                target_id=target_id,
                wp_num=self.params.get("wp_num", 2),
                clear_targets=self.params.get("clear_targets", True) if index == 0 else False,
            )
            for index, target_id in enumerate(self.params["target_ids"])
        ]
        for action in actions:
            action["side"] = self.side
        status = {
            "运行中": False,
            "已结束": True,
        }
        return (
            actions,
            status,
            True,
            {
                "reason": "mission_dispatched",
                "sim_time": sim_time,
                "source": self.declaration.name,
            },
        )
