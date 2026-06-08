from abc import ABC, abstractmethod
from typing import Any


class Pipeline(ABC):
    @abstractmethod
    def pre_process(self, *args: Any, **kwargs: Any) -> Any:
        """每个step的前处理"""
        raise NotImplementedError

    @abstractmethod
    def post_process(self, *args: Any, **kwargs: Any) -> Any:
        """每个step的后处理"""
        raise NotImplementedError

    @abstractmethod
    def reset(self):
        raise NotImplementedError
