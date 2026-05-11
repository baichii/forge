""" Tool for caching attribute value

"""


def property_cache_interval(f, interval: int = 60):
    """Cache the property value for a specified interval (in seconds)"""

    cache_attr = f"_cache_{f.__name__}"
    cache_time_attr = f"_cache_time_{f.__name__}"

    def wrapper(self):

        cache_time = getattr(self, cache_time_attr, 0)

        value = f(self)
        setattr(self, cache_attr, value)
        setattr(self, cache_time_attr, current_time)
        return value

    return property(wrapper)