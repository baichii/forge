"""Local workflow output seeds for offline tests."""

from __future__ import annotations

from typing import Any

from battle_planner.conf import settings
from battle_planner.model import RunIterationTagSpec, SchemeBranchExecutionSpec
from battle_planner.workspace.local.presets import select_agent_param_preset
from pydantic import BaseModel, Field

from forge.core.specs import TickAgentParams


class ScenarioUnderstandingOutputSeed(BaseModel):
    """Offline output for the scenario understanding node."""

    scenario_understanding_md: str = Field(description="预置的想定理解 Markdown。")
    trace_summary: dict[str, Any] = Field(default_factory=dict, description="可选 trace 摘要。")


class BattlePlanGenerationOutputSeed(BaseModel):
    """Offline output for the battle plan generation node."""

    battle_plan_md: str = Field(description="预置的作战方案 Markdown。")
    trace_summary: dict[str, Any] = Field(default_factory=dict, description="可选 trace 摘要。")


class AgentParameterPlanningOutputSeed(BaseModel):
    """Offline output for the agent parameter planning node."""

    branch_executions: list[SchemeBranchExecutionSpec] = Field(
        default_factory=list, description="分支绑定的 agent runtime 参数。"
    )
    planned_agent_params: list[TickAgentParams] = Field(description="预置的 agent runtime 参数。")
    trace_summary: dict[str, Any] = Field(default_factory=dict, description="可选 trace 摘要。")


class SummaryGenerationOutputSeed(BaseModel):
    """Offline output for the summary generation node."""

    summary_md: str = Field(description="预置的总结 Markdown。")
    trace_summary: dict[str, Any] = Field(default_factory=dict, description="可选 trace 摘要。")


class IterationOutputSeed(BaseModel):
    """Offline outputs for one workflow iteration."""

    iteration_index: int = Field(description="seed 内部迭代序号。")
    stage_label: str = Field(description="本轮样例阶段标签。")
    iteration_tags: list[RunIterationTagSpec] = Field(default_factory=list, description="本轮展示标签。")
    scenario_understanding: ScenarioUnderstandingOutputSeed | None = Field(
        default=None, description="想定理解节点输出。"
    )
    battle_plan_generation: BattlePlanGenerationOutputSeed | None = Field(
        default=None, description="作战方案生成节点输出。"
    )
    agent_parameter_planning: AgentParameterPlanningOutputSeed | None = Field(
        default=None, description="agent 参数规划节点输出。"
    )
    summary_generation: SummaryGenerationOutputSeed | None = Field(
        default=None, description="总结生成节点输出。"
    )


class LocalRunOutputSeed(BaseModel):
    """Offline outputs for non-deterministic workflow nodes."""

    seed_id: str = Field(description="输出 seed 标识。")
    iterations: list[IterationOutputSeed] = Field(default_factory=list, description="按迭代组织的输出。")


DEBUG_SCENARIO_UNDERSTANDING_MD = "\n".join(
    [
        "# 想定理解（offline seed）",
        "",
        "## 任务目标",
        "- 围绕 zc3_lite 想定验证蓝方对红方航母目标的规划链路。",
        "- 本段来自 run_output_seed.py，用于隔离离线测试中的 LLM 输出不确定性。",
        "",
        "## 初步判断",
        "- 红方航母是首要目标。",
        "- 蓝方可使用空对海和舰对海打击能力形成逐轮火力方案。",
        "- 后续节点应基于该固定文本继续生成方案或日志事件。",
    ]
)


def _battle_plan_md(*, stage_label: str, title: str, body: list[str]) -> str:
    return "\n".join(
        ["# 作战方案（offline seed）", "", f"## {title}", *body, "", f"- stage_label: {stage_label}"]
    )


def _summary_md(*, stage_label: str, title: str, body: list[str]) -> str:
    return "\n".join(
        ["# 策略迭代总结（offline seed）", "", f"## {title}", *body, "", f"- stage_label: {stage_label}"]
    )


def _agent_parameter_output(
    iteration_index: int,
    stage_label: str,
    iteration_tags: list[RunIterationTagSpec],
) -> AgentParameterPlanningOutputSeed:
    preset = select_agent_param_preset(iteration_index=iteration_index)
    return AgentParameterPlanningOutputSeed(
        branch_executions=[item.model_copy(deep=True) for item in preset["branch_executions"]],
        planned_agent_params=[item.model_copy(deep=True) for item in preset["agents"]],
        trace_summary={
            "source": "run_output_seed",
            "node": "agent_parameter_planning",
            "stage_label": stage_label,
            "seed_iteration_index": iteration_index,
            "iteration_tags": [tag.model_dump(mode="json") for tag in iteration_tags],
        },
    )


def _iteration_seed(
    *,
    iteration_index: int,
    stage_label: str,
    iteration_tags: list[RunIterationTagSpec],
    battle_title: str,
    battle_body: list[str],
    summary_title: str,
    summary_body: list[str],
) -> IterationOutputSeed:
    return IterationOutputSeed(
        iteration_index=iteration_index,
        stage_label=stage_label,
        iteration_tags=iteration_tags,
        scenario_understanding=ScenarioUnderstandingOutputSeed(
            scenario_understanding_md=DEBUG_SCENARIO_UNDERSTANDING_MD,
            trace_summary=_trace_summary(
                node="scenario_understanding",
                stage_label=stage_label,
                iteration_index=iteration_index,
                iteration_tags=iteration_tags,
            ),
        ),
        battle_plan_generation=BattlePlanGenerationOutputSeed(
            battle_plan_md=_battle_plan_md(stage_label=stage_label, title=battle_title, body=battle_body),
            trace_summary=_trace_summary(
                node="battle_plan_generation",
                stage_label=stage_label,
                iteration_index=iteration_index,
                iteration_tags=iteration_tags,
            ),
        ),
        agent_parameter_planning=_agent_parameter_output(iteration_index, stage_label, iteration_tags),
        summary_generation=SummaryGenerationOutputSeed(
            summary_md=_summary_md(stage_label=stage_label, title=summary_title, body=summary_body),
            trace_summary=_trace_summary(
                node="summary_generation",
                stage_label=stage_label,
                iteration_index=iteration_index,
                iteration_tags=iteration_tags,
            ),
        ),
    )


def _trace_summary(
    *,
    node: str,
    stage_label: str,
    iteration_index: int,
    iteration_tags: list[RunIterationTagSpec],
) -> dict[str, Any]:
    return {
        "source": "run_output_seed",
        "node": node,
        "stage_label": stage_label,
        "seed_iteration_index": iteration_index,
        "iteration_tags": [tag.model_dump(mode="json") for tag in iteration_tags],
    }


LOCAL_RUN_OUTPUT_SEEDS: dict[str, LocalRunOutputSeed] = {
    "debug": LocalRunOutputSeed(
        seed_id="debug",
        iterations=[
            _iteration_seed(
                iteration_index=0,
                stage_label="insufficient_firepower",
                iteration_tags=[
                    RunIterationTagSpec(
                        key="exploration",
                        label="探索",
                        reason="最小火力探测，用于确认链路和火力下限。",
                    ),
                    RunIterationTagSpec(
                        key="insufficient_firepower",
                        label="火力不足",
                        reason="预期无法稳定摧毁目标，下一轮需要增加火力。",
                    ),
                ],
                battle_title="火力探测",
                battle_body=[
                    "- 先用单机空袭与单舰打击验证链路。",
                    "- 预期火力不足，重点观察任务下发、目标识别和毁伤反馈。",
                ],
                summary_title="火力不足",
                summary_body=[
                    "- 本轮用于验证最小火力链路。",
                    "- 若目标未摧毁，下一轮增加空中和舰艇火力。",
                ],
            ),
            _iteration_seed(
                iteration_index=1,
                stage_label="firepower_increase",
                iteration_tags=[
                    RunIterationTagSpec(
                        key="firepower_increase",
                        label="增加火力",
                        reason="在上一轮火力不足后增加空中和舰艇打击强度。",
                    )
                ],
                battle_title="增强火力",
                battle_body=[
                    "- 增加空中编组和舰艇打击弹量。",
                    "- 目标是提升毁伤，同时继续观察武器消耗。",
                ],
                summary_title="火力增加",
                summary_body=[
                    "- 本轮提高压制强度。",
                    "- 若毁伤改善但仍不足，下一轮继续拉高火力边界。",
                ],
            ),
            _iteration_seed(
                iteration_index=2,
                stage_label="overkill_waste",
                iteration_tags=[
                    RunIterationTagSpec(
                        key="overkill",
                        label="火力浪费",
                        reason="强火力边界样例，用于确认目标可摧毁但存在冗余消耗。",
                    )
                ],
                battle_title="强火力边界",
                battle_body=[
                    "- 使用多批空中打击和舰艇补充打击形成强压制。",
                    "- 目标是确认可摧毁航母的火力上限。",
                ],
                summary_title="火力浪费",
                summary_body=[
                    "- 本轮偏向确保目标达成。",
                    "- 若武器消耗明显偏高，下一轮回收部分冗余火力。",
                ],
            ),
            _iteration_seed(
                iteration_index=3,
                stage_label="timing_balance",
                iteration_tags=[
                    RunIterationTagSpec(
                        key="balance_adjustment",
                        label="调整平衡",
                        reason="在达成目标基础上回收冗余火力并调整打击时序。",
                    )
                ],
                battle_title="时序平衡",
                battle_body=[
                    "- 保留强火力框架，调整批次和弹量。",
                    "- 目标是在达成毁伤的同时降低浪费。",
                ],
                summary_title="调整平衡",
                summary_body=[
                    "- 本轮开始压缩冗余火力。",
                    "- 下一轮寻找更接近阈值的推荐方案。",
                ],
            ),
            _iteration_seed(
                iteration_index=4,
                stage_label="balanced_recommendation",
                iteration_tags=[
                    RunIterationTagSpec(
                        key="recommended",
                        label="推荐",
                        reason="当前离线样例中的平衡推荐方案。",
                    ),
                    RunIterationTagSpec(
                        key="stable",
                        label="稳定",
                        reason="目标达成和武器消耗之间更接近可接受平衡。",
                    ),
                ],
                battle_title="平衡推荐",
                battle_body=[
                    "- 保留关键批次，减少过量弹药。",
                    "- 目标是稳定达成并控制武器消耗。",
                ],
                summary_title="推荐平衡方案",
                summary_body=[
                    "- 本轮作为平衡推荐样例。",
                    "- 后续若继续迭代，将按 5 轮 seed 循环复用。",
                ],
            ),
        ],
    )
}


def load_local_run_output_seed(seed_id: str | None = None) -> LocalRunOutputSeed:
    """读取本地 offline 输出 seed。

    Args:
        seed_id: 输出 seed 标识；不传时使用全局配置。

    Returns:
        本地输出 seed。
    """

    selected_seed_id = seed_id if seed_id is not None else settings.OUTPUT_SEED
    try:
        return LOCAL_RUN_OUTPUT_SEEDS[selected_seed_id]
    except KeyError as exc:
        available = ", ".join(sorted(LOCAL_RUN_OUTPUT_SEEDS))
        raise ValueError(
            f"Unknown local run output seed: {selected_seed_id}. Available: {available}"
        ) from exc


def load_iteration_output_seed(
    seed_id: str | None = None,
    *,
    iteration_index: int = 0,
) -> IterationOutputSeed:
    """读取某次 workflow 迭代的 offline 输出 seed。"""

    seed = load_local_run_output_seed(seed_id)
    if not seed.iterations:
        raise ValueError(f"Output seed `{seed.seed_id}` has no iterations")
    selected_index = iteration_index % len(seed.iterations)
    return seed.iterations[selected_index].model_copy(deep=True)


def load_scenario_understanding_output_seed(
    seed_id: str | None = None,
    *,
    iteration_index: int = 0,
) -> ScenarioUnderstandingOutputSeed:
    """读取想定理解节点 offline 输出。

    Args:
        seed_id: 输出 seed 标识；不传时使用全局配置。

    Returns:
        想定理解节点输出 seed。
    """

    iteration_seed = load_iteration_output_seed(seed_id, iteration_index=iteration_index)
    if iteration_seed.scenario_understanding is None:
        raise ValueError(
            f"Output seed iteration `{iteration_seed.iteration_index}` has no scenario_understanding output"
        )
    return iteration_seed.scenario_understanding


def load_battle_plan_generation_output_seed(
    seed_id: str | None = None,
    *,
    iteration_index: int = 0,
) -> BattlePlanGenerationOutputSeed:
    """读取作战方案生成节点 offline 输出。"""

    iteration_seed = load_iteration_output_seed(seed_id, iteration_index=iteration_index)
    if iteration_seed.battle_plan_generation is None:
        raise ValueError(
            f"Output seed iteration `{iteration_seed.iteration_index}` has no battle_plan_generation output"
        )
    return iteration_seed.battle_plan_generation


def load_agent_parameter_planning_output_seed(
    seed_id: str | None = None,
    *,
    iteration_index: int = 0,
) -> AgentParameterPlanningOutputSeed:
    """读取 agent 参数规划节点 offline 输出。"""

    iteration_seed = load_iteration_output_seed(seed_id, iteration_index=iteration_index)
    if iteration_seed.agent_parameter_planning is None:
        raise ValueError(
            f"Output seed iteration `{iteration_seed.iteration_index}` has no agent_parameter_planning output"
        )
    return iteration_seed.agent_parameter_planning


def load_summary_generation_output_seed(
    seed_id: str | None = None,
    *,
    iteration_index: int = 0,
) -> SummaryGenerationOutputSeed:
    """读取总结生成节点 offline 输出。"""

    iteration_seed = load_iteration_output_seed(seed_id, iteration_index=iteration_index)
    if iteration_seed.summary_generation is None:
        raise ValueError(
            f"Output seed iteration `{iteration_seed.iteration_index}` has no summary_generation output"
        )
    return iteration_seed.summary_generation
