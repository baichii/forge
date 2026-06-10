from __future__ import annotations

from pydantic import BaseModel, Field

from forge.core.specs import CallbackParams

ZC3_LITE_PLAN_ID = "2175600675558391808"
ZC3_LITE_SCENARIO_NAME = "zc3_lite"
ZC3_LITE_TARGET_CARRIER_ID = "red_CV16 “辽宁”号001型航空母舰_1"
ZC3_LITE_TARGET_STATISTIC_CALLBACK_ID = "target_statistic_carrier"


class PlanPreset(BaseModel):
    """和业务方案绑定的本地预定义运行数据。"""

    plan_id: str = Field(description="任务方案唯一标识。")
    plan_name: str = Field(description="任务方案名称。")
    scenario_name: str = Field(description="想定名称或场景标识。")
    callback_params: list[CallbackParams] = Field(
        default_factory=list, description="运行时 callback 参数。"
    )
    objective_callback_instance_id: str = Field(description="用于判断业务目标的 callback 实例 ID。")
    target_ids: list[str] = Field(default_factory=list, description="业务目标关联的运行时目标 ID。")


PLAN_PRESETS: dict[str, PlanPreset] = {
    ZC3_LITE_PLAN_ID: PlanPreset(
        plan_id=ZC3_LITE_PLAN_ID,
        plan_name="海上航母对抗验证任务方案",
        scenario_name=ZC3_LITE_SCENARIO_NAME,
        callback_params=[
            CallbackParams(
                name="target_statistic",
                callback_instance_id=ZC3_LITE_TARGET_STATISTIC_CALLBACK_ID,
                params={
                    "side": "red",
                    "target_ids": [ZC3_LITE_TARGET_CARRIER_ID],
                },
            )
        ],
        objective_callback_instance_id=ZC3_LITE_TARGET_STATISTIC_CALLBACK_ID,
        target_ids=[ZC3_LITE_TARGET_CARRIER_ID],
    )
}


def load_plan_preset(plan_id: str | None, scenario_name: str | None = None) -> PlanPreset:
    """读取任务方案绑定的本地预定义运行数据。"""

    if plan_id:
        preset = PLAN_PRESETS.get(plan_id)
        if preset is not None:
            return preset.model_copy(deep=True)
        raise ValueError(f"unsupported battle planner plan_id: {plan_id}")

    if scenario_name == ZC3_LITE_SCENARIO_NAME:
        return PLAN_PRESETS[ZC3_LITE_PLAN_ID].model_copy(deep=True)

    raise ValueError(
        f"unsupported battle planner plan preset: plan_id={plan_id!r}, scenario_name={scenario_name!r}"
    )
