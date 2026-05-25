from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

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


def _get_optional_int(name: str, default: int | None = None) -> int | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _profile_env_prefix(profile_name: str) -> str:
    return f"MODEL_{profile_name.upper().replace('-', '_')}"


class ModelProfile(BaseModel):
    name: str = Field(description="Model profile name selected by MODEL.")
    provider: str = Field(description="Provider type, for example openai, local, or offline.")
    api_url: str = Field(default="", description="OpenAI-compatible API base URL.")
    api_key: str = Field(default="", description="OpenAI-compatible API key.")
    model_name: str = Field(default="", description="Concrete model name used for API calls.")
    reasoning_effort: str = Field(default="", description="Optional reasoning effort for thinking models.")
    thinking_type: str = Field(default="", description="Optional extra_body thinking.type value.")

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
    selected: str = Field(default="deepseek_v4_pro", description="Active model profile selected by MODEL.")
    profiles: dict[str, ModelProfile] = Field(
        default_factory=dict, description="Configured model profiles."
    )
    max_tokens: int = Field(default=2048, description="LLM max output tokens.")
    timeout_seconds: float = Field(default=30.0, description="LLM request timeout seconds.")
    max_retry: int = Field(default=2, description="Maximum LLM call retries.")

    @classmethod
    def from_env(cls) -> "ModelConfig":
        selected = os.getenv("MODEL", "deepseek_v4_pro").strip()
        profile_names = [
            item.strip()
            for item in os.getenv(
                "MODEL_PROFILES",
                "local_qwen36,openai_gpt54_mini,deepseek_v4_pro,offline",
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
    max_stage_retry: int = Field(default=2, description="Maximum retries for each workflow stage.")
    max_iterations: int = Field(default=5, description="Maximum iterations for workflow loop tests.")
    fail_fast: bool = Field(default=False, description="Stop workflow immediately after stage failure.")
    save_artifacts: bool = Field(default=True, description="Save workflow artifacts.")
    artifact_dir: str = Field(
        default="examples/battle_planner/artifacts", description="Artifact output dir."
    )
    display_mode: bool = Field(
        default=False,
        description="Use display preset runtime params while keeping LLM text stages enabled.",
    )

    @classmethod
    def from_env(cls) -> "WorkflowConfig":
        return cls(
            max_stage_retry=_get_int("BATTLE_PLANNER_MAX_STAGE_RETRY", 2),
            max_iterations=_get_int("BATTLE_PLANNER_WORKFLOW_MAX_ITERATIONS", 5),
            fail_fast=_get_bool("BATTLE_PLANNER_FAIL_FAST", False),
            save_artifacts=_get_bool("BATTLE_PLANNER_SAVE_ARTIFACTS", True),
            artifact_dir=os.getenv("BATTLE_PLANNER_ARTIFACT_DIR", "examples/battle_planner/artifacts"),
            display_mode=_get_bool("BATTLE_PLANNER_DISPLAY_MODE", False),
        )


class TargetStatisticConfig(BaseModel):
    callback_instance_id: str = Field(
        default="target_statistic_carrier",
        description="Callback instance id for target statistic summary evaluation.",
    )
    side: str = Field(default="red", description="Side that owns target units.")
    target_ids: list[str] = Field(
        default_factory=lambda: [DEFAULT_TARGET_CARRIER_ID],
        description="Target unit ids observed by target_statistic callback.",
    )


class SimulationConfig(BaseModel):
    runs_per_plan: int = Field(default=3, description="Simulation runs for each generated plan.")
    max_parallel: int = Field(default=1, description="Maximum parallel simulation runs.")
    max_decision_steps: int | None = Field(
        default=None,
        description="Optional workflow-side max decision steps. None lets env decide termination.",
    )
    max_failures: int = Field(
        default=1, description="Maximum failed runs before a plan is considered failed."
    )
    random_seed: int | None = Field(default=None, description="Optional random seed for reproducible runs.")
    target_statistic: TargetStatisticConfig = Field(
        default_factory=TargetStatisticConfig,
        description="Default target_statistic callback config used by simulation node.",
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
    level: str = Field(default="full", description="Report level: brief, standard, or full.")
    include_llm_trace: bool = Field(default=True, description="Include LLM trace in report.")
    include_sim_logs: bool = Field(default=True, description="Include simulation logs in report.")
    include_failed_runs: bool = Field(default=True, description="Include failed simulation runs in report.")
    format: str = Field(default="md", description="Report format.")

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
    model: ModelConfig = field(default_factory=ModelConfig.from_env)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig.from_env)
    simulation: SimulationConfig = field(default_factory=SimulationConfig.from_env)
    report: ReportConfig = field(default_factory=ReportConfig.from_env)


config = BattlePlannerConfig()
