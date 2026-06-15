"""
命名规则
    spec: 提供给业务/llm查看的信息
    params: 模块运行参数
"""

from typing import Any

from pydantic import BaseModel, Field


class ParamType:
    """参数输入类型"""

    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"
    LIST = "list"
    DICT = "dict"
    DATATIME = "datetime"
    TABLE = "table"  # 表格数据，格式为 list[dict]，每个 dict 代表一行数据，key 是列名
    ENUM_S = "enum_s"  # 单选
    ENUM_M = "enum_m"  # 多选
    AREA = "area"  # 区域数据，格式为 list
    NAMED_AREA = "named_area"  # 带名称的区域数据，格式为 dict[name, area]，其中 area 格式同 AREA
    ROUTE = "route"  # 路径数据，格式为 list[dict]，每个 dict 代表路径上的一个点，包含坐标和时间等信息


class ParamSpecTemplate(BaseModel):
    """参数声明规范, 用于描述参数展示名、类型、是否必需、默认值等信息"""

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
        name="开始时间",
        type=ParamType.DATATIME,
        required=True,
        description="智能体开始运行时间。",
    )
    end_time = ParamSpecTemplate(
        name="结束时间",
        type=ParamType.DATATIME,
        required=True,
        description="智能体停止运行时间。",
    )
    unit_id = ParamSpecTemplate(
        name="执行单位 ID",
        type=ParamType.STRING,
        required=True,
        description="执行任务的单位 id。",
    )
    unit_ids = ParamSpecTemplate(
        name="执行单位 ID 列表",
        type=ParamType.LIST,
        required=True,
        description="执行任务的单位 id 列表。",
    )
    target_id = ParamSpecTemplate(
        name="目标单位 ID",
        type=ParamType.STRING,
        required=True,
        description="目标单位 id。",
    )
    target_ids = ParamSpecTemplate(
        name="目标单位 ID 列表",
        type=ParamType.LIST,
        required=True,
        description="目标单位 id 列表。",
    )
    side = ParamSpecTemplate(
        name="参演方",
        type=ParamType.STRING,
        required=False,
        description="执行方名称。",
    )


class TickAgentSpec(BaseModel):
    name: str = Field(description="智能体类型名称")
    description: str = Field(description="智能体描述")
    params: dict[str, ParamSpecTemplate] = Field(default_factory=dict, description="智能体参数规范")
    entrypoint: str = Field(description="智能体执行入口，path:Module格式")
    status: list[str] = Field(default_factory=list, description="描述智能体在执行过程中可以返回的状态列表")
    version: str = "0.1"  # 0.1为初始版本，仅用于默认值填充


class CallbackSpec(BaseModel):
    name: str = Field(description="callback 类型名称")
    description: str = Field(description="callback 描述")
    params: dict[str, ParamSpecTemplate] = Field(default_factory=dict, description="callback 参数规范")
    entrypoint: str = Field(description="callback 执行入口，path:Module格式")
    metrics: dict[str, ParamSpecTemplate] = Field(default_factory=dict, description="callback 输出指标声明")
    version: str = "0.1"  # 0.1为初始版本，仅用于默认值填充


class TickAgentParams(BaseModel):
    agent_name: str = Field(description="智能体类型名称")
    side: str = Field(description="智能体实例所属阵营")
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


class CallbackParams(BaseModel):
    """callback 运行参数."""

    name: str = Field(description="回调名称")
    callback_instance_id: str | None = Field(default=None, description="本次运行中的 callback 实例 id")
    params: dict[str, Any] = Field(default_factory=dict, description="回调函数自定义参数")
