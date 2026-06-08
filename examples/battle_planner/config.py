from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TypeVar

from dotenv import load_dotenv
from pydantic import BaseModel, Field

ENV_PATH = Path(__file__).with_name(".env")
DEFAULT_TARGET_CARRIER_ID = "red_CV16 “辽宁”号001型航空母舰_1"


def load_battle_planner_env(path: Path = ENV_PATH, *, override: bool = False) -> bool:
    """Load local env without overriding container/runtime env vars by default."""
    return load_dotenv(path, override=override)


load_battle_planner_env()


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _get_optional_int(name: str, default: int | None = None) -> int | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _profile_env_prefix(profile_name: str) -> str:
    return f"MODEL_{profile_name.upper().replace('-', '_')}"


EnumValue = TypeVar("EnumValue", bound=StrEnum)


def _get_enum(name: str, enum_type: type[EnumValue], default: EnumValue) -> EnumValue:
    return enum_type(_get_str(name, default.value).lower())


class HostMode(StrEnum):
    LOCAL = "local"
    SERVER = "server"


class SourceMode(StrEnum):
    LOCAL = "local"
    SERVICE = "service"
    REPLAY = "replay"


class LLMMode(StrEnum):
    LIVE = "live"
    OFFLINE = "offline"
    REPLAY = "replay"


class RuntimeConfig(BaseModel):
    """控制本次运行入口、输入来源、工作流选择和 LLM 调用方式的顶层配置。"""

    host: HostMode = Field(default=HostMode.LOCAL, description="运行宿主模式：本地运行或服务托管。")
    source: SourceMode = Field(
        default=SourceMode.LOCAL, description="输入来源模式：本地数据、服务数据或回放数据。"
    )
    workflow_name: str = Field(default="zc_lite_baseline", description="本次运行要构建的工作流名称。")
    llm_mode: LLMMode = Field(default=LLMMode.OFFLINE, description="LLM 调用模式：真实调用、离线或回放。")

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        return cls(
            host=_get_enum("HOST", HostMode, HostMode.LOCAL),
            source=_get_enum("SOURCE", SourceMode, SourceMode.LOCAL),
            workflow_name=_get_str("WORKFLOW_NAME", "zc_lite_baseline"),
            llm_mode=_get_enum("LLM_MODE", LLMMode, LLMMode.OFFLINE),
        )

    @property
    def use_local_host(self) -> bool:
        return self.host == HostMode.LOCAL

    @property
    def use_server_host(self) -> bool:
        return self.host == HostMode.SERVER

    @property
    def use_local_source(self) -> bool:
        return self.source == SourceMode.LOCAL

    @property
    def use_service_source(self) -> bool:
        return self.source == SourceMode.SERVICE

    @property
    def use_replay_source(self) -> bool:
        return self.source == SourceMode.REPLAY

    @property
    def use_live_llm(self) -> bool:
        return self.llm_mode == LLMMode.LIVE

    @property
    def use_offline_llm(self) -> bool:
        return self.llm_mode == LLMMode.OFFLINE

    @property
    def use_replay_llm(self) -> bool:
        return self.llm_mode == LLMMode.REPLAY


class ModelProfile(BaseModel):
    name: str = Field(description="模型配置名称，对应 MODEL 选择的 profile。")
    provider: str = Field(description="模型服务类型，例如 openai、by 或 deepseek。")
    api_url: str = Field(default="", description="兼容 OpenAI 接口的 API Base URL。")
    api_key: str = Field(default="", description="兼容 OpenAI 接口的 API Key。")
    model_name: str = Field(default="", description="实际请求模型服务时使用的模型名称。")
    reasoning_effort: str = Field(default="", description="可选的推理强度配置，供 reasoning 模型使用。")
    thinking_type: str = Field(default="", description="可选的 thinking.type 配置，会写入请求 extra_body。")

    @classmethod
    def from_env(cls, profile_name: str) -> "ModelProfile":
        prefix = _profile_env_prefix(profile_name)
        return cls(
            name=profile_name,
            provider=os.getenv(f"{prefix}_PROVIDER", ""),
            api_url=os.getenv(f"{prefix}_API_URL", ""),
            api_key=os.getenv(f"{prefix}_API_KEY", "dummy"),
            model_name=os.getenv(f"{prefix}_MODEL_NAME", ""),
            reasoning_effort=os.getenv(f"{prefix}_REASONING_EFFORT", ""),
            thinking_type=os.getenv(f"{prefix}_THINKING_TYPE", ""),
        )


class ModelConfig(BaseModel):
    selected: str = Field(default="by_qwen36", description="当前启用的模型 profile，由 MODEL 指定。")
    profiles: dict[str, ModelProfile] = Field(
        default_factory=dict, description="已加载的模型 profile 配置集合。"
    )
    max_tokens: int = Field(default=2048, description="LLM 单次调用的最大输出 token 数。")
    timeout_seconds: float = Field(default=30.0, description="LLM 单次请求超时时间，单位为秒。")
    max_retry: int = Field(default=2, description="LLM 调用失败后的最大重试次数。")

    @classmethod
    def from_env(cls) -> "ModelConfig":
        selected = os.getenv("MODEL", "by_qwen36").strip()
        profile_names = [
            item.strip()
            for item in os.getenv(
                "MODEL_PROFILES",
                "by_qwen36,openai_gpt54_mini,deepseek_v4_pro",
            ).split(",")
            if item.strip()
        ]
        profiles = {name: ModelProfile.from_env(name) for name in profile_names}
        if selected and selected not in profiles:
            profiles[selected] = ModelProfile.from_env(selected)
        return cls(
            selected=selected,
            profiles=profiles,
            max_tokens=_get_int("BATTLE_PLANNER_LLM_MAX_TOKENS", 2048),
            timeout_seconds=_get_float("BATTLE_PLANNER_LLM_TIMEOUT_SECONDS", 30.0),
            max_retry=_get_int("BATTLE_PLANNER_LLM_MAX_RETRY", 2),
        )

    @property
    def active_profile(self) -> ModelProfile:
        if self.selected not in self.profiles:
            raise ValueError(f"MODEL profile `{self.selected}` is not configured")
        return self.profiles[self.selected]


class WorkflowConfig(BaseModel):
    max_stage_retry: int = Field(default=2, description="单个工作流阶段失败后的最大重试次数。")
    max_iterations: int = Field(default=5, description="工作流循环运行的最大迭代次数。")
    fail_fast: bool = Field(default=False, description="阶段失败后是否立即终止整个工作流。")
    save_artifacts: bool = Field(default=True, description="是否保存工作流运行产物。")
    artifact_dir: str = Field(
        default="examples/battle_planner/workspace/artifacts", description="工作流运行产物输出目录。"
    )

    @classmethod
    def from_env(cls) -> "WorkflowConfig":
        return cls(
            max_stage_retry=_get_int("BATTLE_PLANNER_MAX_STAGE_RETRY", 2),
            max_iterations=_get_int("BATTLE_PLANNER_WORKFLOW_MAX_ITERATIONS", 5),
            fail_fast=_get_bool("BATTLE_PLANNER_FAIL_FAST", False),
            save_artifacts=_get_bool("BATTLE_PLANNER_SAVE_ARTIFACTS", True),
            artifact_dir=os.getenv(
                "BATTLE_PLANNER_ARTIFACT_DIR", "examples/battle_planner/workspace/artifacts"
            ),
        )


class TargetStatisticConfig(BaseModel):
    callback_instance_id: str = Field(
        default="target_statistic_carrier",
        description="用于目标统计评估的 callback 实例 ID。",
    )
    side: str = Field(default="red", description="被观测目标所属阵营。")
    target_ids: list[str] = Field(
        default_factory=lambda: [DEFAULT_TARGET_CARRIER_ID],
        description="target_statistic callback 需要观测的目标单位 ID 列表。",
    )


class SimulationConfig(BaseModel):
    runs_per_plan: int = Field(default=3, description="每个生成方案对应的仿真运行次数。")
    max_parallel: int = Field(default=1, description="最大并行仿真运行数。")
    max_decision_steps: int | None = Field(
        default=None,
        description="工作流侧可选的最大决策步数；为空时由环境自行决定终止条件。",
    )
    max_failures: int = Field(default=1, description="判定方案失败前允许的最大失败仿真次数。")
    random_seed: int | None = Field(default=None, description="可选随机种子，用于可复现的仿真运行。")
    target_statistic: TargetStatisticConfig = Field(
        default_factory=TargetStatisticConfig,
        description="仿真节点默认使用的 target_statistic callback 配置。",
    )

    @classmethod
    def from_env(cls) -> "SimulationConfig":
        return cls(
            runs_per_plan=_get_int("BATTLE_PLANNER_SIM_RUNS_PER_PLAN", 3),
            max_parallel=_get_int("BATTLE_PLANNER_SIM_MAX_PARALLEL", 1),
            max_decision_steps=_get_optional_int("BATTLE_PLANNER_SIM_MAX_DECISION_STEPS"),
            max_failures=_get_int("BATTLE_PLANNER_SIM_MAX_FAILURES", 1),
            random_seed=_get_optional_int("BATTLE_PLANNER_SIM_RANDOM_SEED"),
        )


class ReportConfig(BaseModel):
    level: str = Field(default="full", description="报告详细程度：brief、standard 或 full。")
    include_llm_trace: bool = Field(default=True, description="报告中是否包含 LLM 调用轨迹。")
    include_sim_logs: bool = Field(default=True, description="报告中是否包含仿真日志。")
    include_failed_runs: bool = Field(default=True, description="报告中是否包含失败的仿真运行记录。")
    format: str = Field(default="md", description="报告输出格式。")

    @classmethod
    def from_env(cls) -> "ReportConfig":
        return cls(
            level=os.getenv("BATTLE_PLANNER_REPORT_LEVEL", "full"),
            include_llm_trace=_get_bool("BATTLE_PLANNER_REPORT_INCLUDE_LLM_TRACE", True),
            include_sim_logs=_get_bool("BATTLE_PLANNER_REPORT_INCLUDE_SIM_LOGS", True),
            include_failed_runs=_get_bool("BATTLE_PLANNER_REPORT_INCLUDE_FAILED_RUNS", True),
            format=os.getenv("BATTLE_PLANNER_REPORT_FORMAT", "md"),
        )


@dataclass
class BattlePlannerConfig:
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig.from_env)
    model: ModelConfig = field(default_factory=ModelConfig.from_env)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig.from_env)
    simulation: SimulationConfig = field(default_factory=SimulationConfig.from_env)
    report: ReportConfig = field(default_factory=ReportConfig.from_env)


config = BattlePlannerConfig()
