import os
from dataclasses import dataclass, field

from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field


load_dotenv()


class ApiConfig(BaseModel):
    openai_api_url: str
    openai_api_key: str

    @classmethod
    def from_env(cls) -> "ApiConfig":
        return cls(
            openai_api_url=os.getenv("OPENAI_API_URL", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        )

class SystemConfig(BaseModel):
    max_retry: int = Field(default=10, description="最大重试次数")



@dataclass
class BattlePlannerConfig:
    api: ApiConfig = field(default_factory=ApiConfig.from_env)
    system: SystemConfig = field(default_factory=SystemConfig)


config = BattlePlannerConfig()
