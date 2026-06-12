from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_ROOT = Path(__file__).resolve().parent


class RuntimeMode(StrEnum):
    """运行形态。

    LOCAL_DEV 表示本地开发，仅打印产物；
    LOCAL_FULL 表示本地完整运行，打印并存储产物；
    SERVER 表示后端服务运行，存储产物并通过服务对外提供。
    """

    LOCAL_DEV = "local_dev"
    LOCAL_FULL = "local_full"
    SERVER = "server"


class SourceMode(StrEnum):
    """任务输入来源。

    LOCAL 表示从本地 plan_id、seed 和 workspace 资源构造输入；
    SERVICE 表示从服务接口请求构造输入。
    """

    LOCAL = "local"
    SERVICE = "service"


class LLMMode(StrEnum):
    """LLM 产物来源。

    LIVE 表示调用真实模型；OFFLINE 表示按本地输出 seed 读取模拟 LLM 产物。
    """

    LIVE = "live"
    OFFLINE = "offline"


class Settings(BaseSettings):
    """battle_planner 全局配置。

    这里只放应用级运行配置，不放单次 workflow 运行参数。
    """

    model_config = SettingsConfigDict(
        env_file=PACKAGE_ROOT / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        cache_strings=True,
    )

    # 运行形态：控制本地开发、本地完整运行和服务运行的产物行为。
    RUNTIME_MODE: RuntimeMode = RuntimeMode.LOCAL_DEV
    # 任务输入来源：local 从本地 plan_id/seed 构造，service 从接口请求构造。
    SOURCE: SourceMode = SourceMode.LOCAL
    # LLM 产物来源：offline 读取 run_output_seed，live 调用真实模型。
    LLM_MODE: LLMMode = LLMMode.OFFLINE

    # datetime
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # workflow use
    WORKFLOW_NAME: str = "zc_lite_baseline"
    VERBOSE: int = 1

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
    LLM_MAX_TOKENS: int = 2048
    LLM_TIMEOUT_SECONDS: float = 30.0
    LLM_MAX_RETRY: int = 2

    # simulation
    SIM_RUNS_PER_PLAN: int = 3
    SIM_MAX_PARALLEL: int = 1
    SIM_MAX_DECISION_STEPS: int | None = None
    SIM_MAX_FAILURES: int = 1
    SIM_RANDOM_SEED: int | None = None

    # report
    REPORT_LEVEL: str = "full"
    REPORT_INCLUDE_LLM_TRACE: bool = True
    REPORT_INCLUDE_SIM_LOGS: bool = True
    REPORT_INCLUDE_FAILED_RUNS: bool = True
    REPORT_FORMAT: str = "md"

    # 本地 LLM 输出 seed，仅在 LLM_MODE=offline 时生效。
    OUTPUT_SEED: str = "debug"
    # 运行记录目录，用于 local_full 和 server 模式下保存 run 数据。
    RUNS_DIR: Path = PACKAGE_ROOT / "runs"

    @property
    def should_print_artifacts(self) -> bool:
        return self.RUNTIME_MODE in {RuntimeMode.LOCAL_DEV, RuntimeMode.LOCAL_FULL}

    @property
    def should_store_artifacts(self) -> bool:
        return self.RUNTIME_MODE in {RuntimeMode.LOCAL_FULL, RuntimeMode.SERVER}

    @property
    def should_serve_artifacts(self) -> bool:
        return self.RUNTIME_MODE == RuntimeMode.SERVER

    @property
    def model_profile_names(self) -> list[str]:
        return [item.strip() for item in self.MODEL_PROFILES.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
