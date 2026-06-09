from __future__ import annotations

from pydantic import BaseModel, Field


class HumanInputSpec(BaseModel):
    """人工输入的约束、偏好或补充说明。"""

    summary: str = Field(default="", description="人工输入摘要。")
    items: list[str] = Field(default_factory=list, description="人工输入条目。")
