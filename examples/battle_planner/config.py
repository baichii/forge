from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

ENV_PATH = Path(__file__).with_name(".env")


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


class ApiConfig(BaseModel):
    openai_api_url: str
    openai_api_key: str
    openai_model: str
    local_openai_api_url: str
    local_openai_api_key: str
    local_openai_model: str

    @classmethod
    def from_env(cls) -> "ApiConfig":
        return cls(
            openai_api_url=os.getenv("OPENAI_API_URL") or os.getenv("OPENAI_BASE_URL", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL") or os.getenv("OPENAI_DEFAULT_MODEL", "gpt-5.4-mini"),
            local_openai_api_url=os.getenv("LOCAL_OPENAI_API_URL", ""),
            local_openai_api_key=os.getenv("LOCAL_OPENAI_API_KEY", "dummy"),
            local_openai_model=os.getenv("LOCAL_OPENAI_MODEL", ""),
        )


class ModelConfig(BaseModel):
    provider: str = Field(default="auto", description="Model provider: auto, local, openai, or offline.")
    max_tokens: int = Field(default=2048, description="LLM max output tokens.")
    timeout_seconds: float = Field(default=30.0, description="LLM request timeout seconds.")
    max_retry: int = Field(default=2, description="Maximum LLM call retries.")

    @classmethod
    def from_env(cls) -> "ModelConfig":
        return cls(
            provider=os.getenv("BATTLE_PLANNER_MODEL_PROVIDER", "auto"),
            max_tokens=_get_int("BATTLE_PLANNER_LLM_MAX_TOKENS", 2048),
            timeout_seconds=_get_float("BATTLE_PLANNER_LLM_TIMEOUT_SECONDS", 30.0),
            max_retry=_get_int("BATTLE_PLANNER_LLM_MAX_RETRY", 2),
        )


class WorkflowConfig(BaseModel):
    max_stage_retry: int = Field(default=2, description="Maximum retries for each workflow stage.")
    fail_fast: bool = Field(default=False, description="Stop workflow immediately after stage failure.")
    save_artifacts: bool = Field(default=True, description="Save workflow artifacts.")
    artifact_dir: str = Field(
        default="examples/battle_planner/artifacts", description="Artifact output dir."
    )

    @classmethod
    def from_env(cls) -> "WorkflowConfig":
        return cls(
            max_stage_retry=_get_int("BATTLE_PLANNER_MAX_STAGE_RETRY", 2),
            fail_fast=_get_bool("BATTLE_PLANNER_FAIL_FAST", False),
            save_artifacts=_get_bool("BATTLE_PLANNER_SAVE_ARTIFACTS", True),
            artifact_dir=os.getenv("BATTLE_PLANNER_ARTIFACT_DIR", "examples/battle_planner/artifacts"),
        )


class SimulationConfig(BaseModel):
    runs_per_plan: int = Field(default=3, description="Simulation runs for each generated plan.")
    max_parallel: int = Field(default=1, description="Maximum parallel simulation runs.")
    max_decision_steps: int = Field(
        default=3, description="Maximum decision steps for each simulation run."
    )
    max_failures: int = Field(
        default=1, description="Maximum failed runs before a plan is considered failed."
    )
    random_seed: int | None = Field(default=None, description="Optional random seed for reproducible runs.")

    @classmethod
    def from_env(cls) -> "SimulationConfig":
        return cls(
            runs_per_plan=_get_int("BATTLE_PLANNER_SIM_RUNS_PER_PLAN", 3),
            max_parallel=_get_int("BATTLE_PLANNER_SIM_MAX_PARALLEL", 1),
            max_decision_steps=_get_int("BATTLE_PLANNER_SIM_MAX_DECISION_STEPS", 3),
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
    api: ApiConfig = field(default_factory=ApiConfig.from_env)
    model: ModelConfig = field(default_factory=ModelConfig.from_env)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig.from_env)
    simulation: SimulationConfig = field(default_factory=SimulationConfig.from_env)
    report: ReportConfig = field(default_factory=ReportConfig.from_env)


config = BattlePlannerConfig()
