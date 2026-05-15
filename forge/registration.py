"""注册模块"""

import copy
import difflib
import importlib
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from forge import error
from forge.logger import logger

MODULE_ID_RE = re.compile(r"^(?:(?P<namespace>[\w:-]+)\/)?(?:(?P<name>.+))$")


class ModuleCreator(Protocol):
    """function type expected for callable module."""

    def __call__(self, **kwargs) -> Callable: ...


@dataclass
class ModuleSpec:
    """module specification

    attributes:
        id: 唯一标识
        entry_point: 模块入口路径
        kwargs: 模块在创建时候默认传入的参数
        data: 模块携带的数据, 用于数据查询

    """

    id: str
    entry_point: ModuleCreator | str | None = field(default=None)

    kwargs: dict = field(default_factory=dict)
    data: dict = field(default=dict)

    # post-init attributes
    namespace: str | None = field(init=False)
    name: str = field(init=False)

    def __post_init__(self):
        self.namespace, self.name = parse_module_id(self.id)

    def make(self, **kwargs):
        return make(self, **kwargs)

    def pprint(self, disable_print: bool = False) -> str:
        output = f"id={self.id}\n"

        if not disable_print:
            print(output)
        return output


# 全局module注册
registry: dict[str, ModuleSpec] = {}
# 支持的namespace
# action 自定义行动
# manager 自定义信息管理模块, 建议使用版本号命名空间, 例如 unit_manager/v1
namespaces: set[str] = {"action", "entity", "agent", "node", "manager"}


def parse_module_id(module_id: str) -> tuple[str | None, str]:
    """解析 module ID"""
    match = MODULE_ID_RE.fullmatch(module_id)
    if not match:
        raise error.RegistrationError(
            f"Malformed module ID: {module_id}. Currently all IDs must be of the form [namespace/](module-name)). (namespace is optional))"
        )
    ns, name = match.group("namespace", "name")
    return ns, name


def get_module_id(ns: str | None, name: str) -> str:
    """获取module id"""
    full_name = name
    if ns is not None:
        full_name = f"{ns}/{name}"
    return full_name


def _check_namespace_exists(ns: str | None):
    """检查命名空间是否存在"""
    if ns is None:
        return

    namespace: set[str] = {
        module_spec.namespace for module_spec in registry.values() if module_spec.namespace is not None
    }
    if ns in namespace:
        return

    # 生成帮助信息
    suggestion = difflib.get_close_matches(ns, namespace, n=1) if len(namespace) > 1 else None
    if suggestion:
        suggestion_msg = f"Did you mean {suggestion[0]}?"
    else:
        suggestion_msg = f"Namespace {ns} not found."
    raise error.NamespaceNotFound(f"Namespace {ns} not found. {suggestion_msg}")


def _check_name_exists(ns: str | None, name: str):
    """检查模块名称是否在namespace中存在"""
    _check_namespace_exists(ns)

    names: set[str] = {module_spec.name for module_spec in registry.values() if module_spec.namespace == ns}
    if name in names:
        return

    # 生成帮助信息
    suggestion = difflib.get_close_matches(name, names, n=1)
    namespace_msg = f" in namespace {ns}" if ns else ""
    suggestion_msg = f"Did you mean {suggestion[0]}?" if suggestion else ""
    raise error.NameNotFound(f"Module {name} doesn't exist{namespace_msg}. {suggestion_msg}")


def _check_exists(ns: str | None, name: str):
    """检查版本是否在namespace中存在"""
    if get_module_id(ns, name) in registry:
        return

    _check_name_exists(ns, name)


def _check_spec_register(testing_spec: ModuleSpec):
    """检查module是否已经注册"""
    if testing_spec.id in registry:
        raise error.Error(f"Module {testing_spec.id} already registered.")


def _find_spec(module_id: str) -> ModuleSpec:
    assert isinstance(module_id, str)

    module, module_name = (None, module_id) if ":" not in module_id else module_id.split(":")
    if module is not None:
        try:
            importlib.import_module(module)
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(f"{e}. Module registration via importing a module failed.")
    module_spec = registry.get(module_name)
    if module_spec is None:
        raise error.Error(
            f"No registered module with id: {module_name}. Did you register it, or import the package that registers it?"
        )
    return module_spec


def load_module_creator(name: str) -> ModuleCreator:
    """通过(import_path):(module name)加载模块"""
    mod_name, attr_name = name.rsplit(":")
    mod = importlib.import_module(mod_name)
    fn = getattr(mod, attr_name)
    return fn


def register(
    module_id: str, entry_point: ModuleCreator | str, kwargs: dict | None = None, data: dict | None = None
) -> ModuleCreator:
    ns, name = parse_module_id(module_id)
    if kwargs is None:
        kwargs = dict()

    full_module_id = get_module_id(ns, name)
    new_spec = ModuleSpec(
        id=full_module_id,
        entry_point=entry_point,
        kwargs=kwargs,
        data=data,
    )
    _check_spec_register(new_spec)

    if new_spec.id in registry:
        logger.warn(f"Overriding module {new_spec.id} already registered.")
    registry[new_spec.id] = new_spec


def make(module_id: str | ModuleSpec, **kwargs):
    """创建module"""
    if isinstance(module_id, ModuleSpec):
        module_spec = module_id
    else:
        assert isinstance(module_id, str)
        module_spec = _find_spec(module_id)

    assert isinstance(module_spec, ModuleSpec)

    module_spec_kwargs = copy.deepcopy(module_spec.kwargs)
    module_spec_kwargs.update(kwargs)

    if module_spec.entry_point is None:
        raise error.Error(f"{module_spec.id} registered but entry_point is not specified")
    elif callable(module_spec.entry_point):
        module_creator = module_spec.entry_point
    else:
        module_creator = load_module_creator(module_spec.entry_point)

    try:
        module = module_creator(**module_spec_kwargs)
    except TypeError as e:
        raise type(e)(
            f"{e} was raised from the module creator for {module_spec.id} with kwargs ({module_spec_kwargs})"
        )
    return module


def query(module_id: str | ModuleSpec) -> Any:
    """查询module

    用于查询entity原型属性

    """
    if isinstance(module_id, ModuleSpec):
        module_spec = module_id
    else:
        assert isinstance(module_id, str)
        module_spec = _find_spec(module_id)
    return module_spec.data


def spec(module_id: str) -> ModuleSpec:
    """通过module id 检索module spec"""
    module_spec = registry.get(module_id)
    if module_spec is None:
        ns, name = parse_module_id(module_id)
        _check_exists(ns, name)
        raise error.Error(f"No registered module with id: {module_id}.")
    else:
        assert isinstance(module_spec, ModuleSpec), (
            f"Expected the registry for {module_id} to be an `ModuleSpec`, actual type is {type(module_spec)}"
        )
        return module_spec


def register_action(
    name: str, entry_point: ModuleCreator | str
) -> ModuleCreator:
    """注册action module"""
    module_id = f"action/{name}"
    return register(module_id, entry_point)

def make_action(name: str, **kwargs):
    """创建action module"""
    module_id = f"action/{name}"
    return make(module_id, **kwargs)
