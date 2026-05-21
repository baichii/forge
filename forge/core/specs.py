from typing import Any

from pydantic import BaseModel, Field


class ParamType:
    """参数输入类型"""

    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"
    LIST = "list"
    DATATIME = "datetime"
    TABLE = "table"  # 表格数据，格式为 list[dict]，每个 dict 代表一行数据，key 是列名
    ENUM_S = "enum_s"  # 单选
    ENUM_M = "enum_m"  # 多选
    AREA = "area"  # 区域数据，格式为 list
    NAMED_AREA = "named_area"  # 带名称的区域数据，格式为 dict[name, area]，其中 area 格式同 AREA
    ROUTE = "route"  # 路径数据，格式为 list[dict]，每个 dict 代表路径上的一个点，包含坐标和时间等信息


class ParamSpecTemplate(BaseModel):
    """参数声明规范, 用于描述参数的类型、是否必需、默认值等信息"""

    name: str
    type: str
    required: bool = True
    description: str = ""
    default_value: Any = None
    examples: list[Any] = Field(default_factory=list)
    other: dict = Field(default_factory=dict)

    def redeclaration(self, **kwargs) -> "ParamSpecTemplate":
        """基于当前参数规范创建一个新的参数规范, 可以通过 kwargs 覆盖原有属性"""
        return self.model_copy(deep=True, update=kwargs)


class ParamSpec:
    """智能体参数规范"""

    start_time = ParamSpecTemplate(
        name="start_time",
        type=ParamType.DATATIME,
        required=True,
        description="智能体开始运行时间。",
    )
    end_time = ParamSpecTemplate(
        name="end_time",
        type=ParamType.DATATIME,
        required=True,
        description="智能体停止运行时间。",
    )
    unit_id = ParamSpecTemplate(
        name="unit_id",
        type=ParamType.STRING,
        required=True,
        description="执行任务的单位 id。",
    )
    unit_ids = ParamSpecTemplate(
        name="unit_ids",
        type=ParamType.LIST,
        required=True,
        description="执行任务的单位 id 列表。",
    )
    target_id = ParamSpecTemplate(
        name="target_id",
        type=ParamType.STRING,
        required=True,
        description="目标单位 id。",
    )
    target_ids = ParamSpecTemplate(
        name="target_ids",
        type=ParamType.LIST,
        required=True,
        description="目标单位 id 列表。",
    )


class TickAgentSpec(BaseModel):
    name: str = Field(description="智能体类型名称")
    description: str = Field(description="智能体描述")
    params: dict[str, ParamSpecTemplate] = Field(default_factory=dict, description="智能体参数规范")
    entrypoint: str = Field(description="智能体执行入口，path:Module格式")
    status: list[str] = Field(default_factory=list, description="描述智能体在执行过程中可以返回的状态列表")
    version: str = "0.1"  # 0.1为初始版本，仅用于默认值填充


class TickAgentParams(BaseModel):
    agent_name: str = Field(description="智能体类型名称")
    agent_instance_id: str | None = Field(default=None, description="本次运行中的智能体实例 id")
    params: dict[str, Any] = Field(default_factory=dict, description="智能体运行参数")


class EnvMode:
    """环境获取方式."""

    CREATE = "create"
    CONNECT = "connect"


class EnvLink:
    """环境连接风格."""

    GYM = "gym"
    INFOMAN = "infoman"
    CUSTOM = "custom"


class EnvParams(BaseModel):
    """环境运行参数.

    mode 表示环境怎么来，create 由 runner 创建或启动，connect 连接已有环境。
    link 表示 runner 用什么风格和环境交互。
    """

    name: str = Field(description="环境名称")
    mode: str = Field(default=EnvMode.CREATE, description="环境获取方式")
    link: str = Field(default=EnvLink.GYM, description="环境连接风格")
    params: dict[str, Any] = Field(default_factory=dict, description="环境连接配置")


clas


class CallbackParams(BaseModel):
    """callback 运行参数."""

    name: str = Field(description="回调名称")
    entrypoint: str = Field(description="callback执行入口，path:Module格式")
    params: dict[str, Any] = Field(default_factory=dict, description="回调函数自定义参数")
