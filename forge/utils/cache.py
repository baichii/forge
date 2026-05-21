"""Tool for caching attribute value"""

import time
from functools import wraps


def property_cache_interval(f, interval: int = 60):
    """Cache the property value for a specified interval (in seconds)"""

    cache_attr = f"_cache_{f.__name__}"
    cache_time_attr = f"_cache_time_{f.__name__}"

    @wraps(f)
    def wrapper(self):
        current_time = time.time()
        cache_time = getattr(self, cache_time_attr, 0)
        if current_time - cache_time < interval and hasattr(self, cache_attr):
            return getattr(self, cache_attr)

        value = f(self)
        setattr(self, cache_attr, value)
        setattr(self, cache_time_attr, current_time)
        return value

    return property(wrapper)
