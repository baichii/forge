import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field


ENV_PATH = Path(__file__).with_name(".env")
load_dotenv(ENV_PATH)


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

class SystemConfig(BaseModel):
    max_retry: int = Field(default=10, description="最大重试次数")



@dataclass
class BattlePlannerConfig:
    api: ApiConfig = field(default_factory=ApiConfig.from_env)
    system: SystemConfig = field(default_factory=SystemConfig)


config = BattlePlannerConfig()
