"""Battle planner backend 服务配置。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


class BackendSettings(BaseSettings):
    """backend 独立配置。"""

    model_config = SettingsConfigDict(
        env_file=PACKAGE_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="BATTLE_PLANNER_BACKEND_",
        env_ignore_empty=True,
        extra="ignore",
        cache_strings=True,
    )

    # run 缓存目录；backend 只通过该目录读取和写入服务数据。
    RUNS_DIR: Path = PACKAGE_ROOT / "runs"
    # 后台 workflow 线程数；第一版用于小场景工程验证。
    EXECUTION_MAX_WORKERS: int = 2
    # 同时运行中的任务数量上限；超过后 POST /runs 直接返回 429。
    EXECUTION_MAX_ACTIVE_RUNS: int = 2
    # SSE 轮询本地 run 缓存的间隔。
    EVENT_POLL_INTERVAL_SECONDS: float = 0.5


@lru_cache
def get_backend_settings() -> BackendSettings:
    """获取 backend 配置。"""

    return BackendSettings()


backend_settings = get_backend_settings()
