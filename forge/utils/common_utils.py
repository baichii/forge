from __future__ import annotations

from functools import wraps


def is_class_dict(class_dict: dict) -> bool:
    return "class" in class_dict and ("params" in class_dict or "config" in class_dict)


def construct(class_dict: dict, *, unpack_params: bool = True, params_key: str = "params", **kwargs):
    """
    根据 class_dict 实例化对象

    Args:
        class_dict: 对象参数
        unpack_params: 是否将class_dict中参数作为一个整体传入class_中
        params_key: 参数名称
        **kwargs: 额外参数

    Returns:
        实例化对象
    """
    if not is_class_dict(class_dict):
        raise ValueError(
            f"Expected a dict with keys `class` and `params` or `config`. but get {class_dict}"
    )
    class_ = class_dict["class"]
    if params_key not in class_dict and params_key == "params":
        params_key = "config"
    params_ = class_dict[params_key]
    if unpack_params:
        return class_(**params_, **kwargs)
    return class_(params=params_, **kwargs)


def id_generator() -> str:
    """生成8位唯一id"""
    return uuid4().hex[:8]


def safe_query(default_value):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RuntimeError:
                return default_value

        return wrapper

    return decorator


def safe_process(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RuntimeError:
            traceback.print_exc()
            return None

    return wrapper

