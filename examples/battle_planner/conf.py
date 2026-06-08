from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BATTLE_PLANNER_ROOT = Path(__file__).resolve().parent


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


class Settings(BaseSettings):
    """battle_planner 全局配置。

    这里只放应用级运行配置，不放单次 workflow 运行参数。
    """

    model_config = SettingsConfigDict(
        env_file=BATTLE_PLANNER_ROOT / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        cache_strings=True,
    )

    # runtime mode
    HOST: HostMode = HostMode.LOCAL
    SOURCE: SourceMode = SourceMode.LOCAL
    LLM_MODE: LLMMode = LLMMode.OFFLINE

    # datetime
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # workflow use
    WORKFLOW_NAME: str = "zc_lite_baseline"

    # model use
    MODEL: str = "by_qwen36"

    # model profiles
    MODEL_PROFILES: str = "by_qwen36,openai_gpt54_mini,deepseek_v4_pro"

    MODEL_BY_QWEN36_PROVIDER: str = "by"
    MODEL_BY_QWEN36_API_URL: str = "http://10.1.1.3:31143/v1"
    MODEL_BY_QWEN36_API_KEY: str = "dummy"
    MODEL_BY_QWEN36_MODEL_NAME: str = "qwen36-35b"

    MODEL_OPENAI_GPT54_MINI_PROVIDER: str = "openai"
    MODEL_OPENAI_GPT54_MINI_API_URL: str = "your api url"
    MODEL_OPENAI_GPT54_MINI_API_KEY: str = "your api key"
    MODEL_OPENAI_GPT54_MINI_MODEL_NAME: str = "gpt-5.4-mini"

    MODEL_DEEPSEEK_V4_PRO_PROVIDER: str = "deepseek"
    MODEL_DEEPSEEK_V4_PRO_API_URL: str = "https://api.deepseek.com"
    MODEL_DEEPSEEK_V4_PRO_API_KEY: str = "your api key"
    MODEL_DEEPSEEK_V4_PRO_MODEL_NAME: str = "deepseek-v4-pro"
    MODEL_DEEPSEEK_V4_PRO_REASONING_EFFORT: str = "high"
    MODEL_DEEPSEEK_V4_PRO_THINKING_TYPE: str = "enabled"

    # llm runtime
    BATTLE_PLANNER_LLM_MAX_TOKENS: int = 2048
    BATTLE_PLANNER_LLM_TIMEOUT_SECONDS: float = 30.0
    BATTLE_PLANNER_LLM_MAX_RETRY: int = 2

    # simulation
    BATTLE_PLANNER_SIM_RUNS_PER_PLAN: int = 3
    BATTLE_PLANNER_SIM_MAX_PARALLEL: int = 1
    BATTLE_PLANNER_SIM_MAX_DECISION_STEPS: int | None = None
    BATTLE_PLANNER_SIM_MAX_FAILURES: int = 1
    BATTLE_PLANNER_SIM_RANDOM_SEED: int | None = None

    # report
    BATTLE_PLANNER_REPORT_LEVEL: str = "full"
    BATTLE_PLANNER_REPORT_INCLUDE_LLM_TRACE: bool = True
    BATTLE_PLANNER_REPORT_INCLUDE_SIM_LOGS: bool = True
    BATTLE_PLANNER_REPORT_INCLUDE_FAILED_RUNS: bool = True
    BATTLE_PLANNER_REPORT_FORMAT: str = "md"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
