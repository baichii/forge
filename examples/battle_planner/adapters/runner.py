import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES_ROOT = Path(__file__).resolve().parents[2]
for path in (REPO_ROOT, EXAMPLES_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from battle_planner.registry import register_battle_planner_modules  # noqa: E402

from forge.env import Runner as BaseRuner  # noqa: E402
from forge.lib.callback import CallBackList  # noqa: E402
from forge.registration import make_callback, make_env, make_tick_agent  # noqa: E402
from forge.utils.specs import CallbackSpec, EnvLink, EnvMode, EnvSpec  # noqa: E402


class Runner(BaseRuner):
    """测试runner， hard code

    Notes:
        1. 必要条件，runner必须具备基于config启动的能力，env和agent都要在内部构造而不能作为实例输入
        2. 对于需要在不同callback中频繁统计的信息，应该在env外封装一个wrapper，在wrapper层实现中间指标计算

    """

    def __init__(self, env_spec, tick_agents: list[Any], callbacks: list[CallbackSpec]):

        self._init_env(env_spec)
        self._init_tick_agents(tick_agents)
        self._init_callbacks(callbacks)

        self._callbacks.on_begin()

        self._last_actions = []
        self._start_time = time.time()
        self._end_time = self._start_time

    def reset(self):
        self._env.reset()

    def run(self, max_step: int | None = None) -> Any:
        step = 0
        while True:
            observation, terminated, truncated, info = self.run_step()
            step += 1

            done = False

            if max_step and step >= max_step:
                print("达到最大step数量")
                done = True

            if truncated:
                print("环境达到最大步数")
                done = True

            if terminated:
                print("环境触发终止条件")
                done = True

            if done:
                break
        self._callbacks.on_end()

    def run_step(self):
        self._callbacks.on_step_begin()
        observation, _, terminated, truncated, info = self._env.step(self._last_actions)
        actions = []
        for _, tick_agent in self._tick_agents.items():
            action, status, done, info = tick_agent.step(observation)
            actions.extend(action)
        self._last_actions = actions
        self._callbacks.on_step_end()
        return observation, terminated, truncated, info

    def _init_env(self, env_spec) -> None:
        self._env = make_env(env_spec.name, **env_spec.params)

    def _init_tick_agents(self, tick_agents: list[Any]) -> None:
        self._tick_agents = {}
        for tick_agent in tick_agents:
            if hasattr(tick_agent, "name"):
                name = tick_agent.name
            else:
                name = tick_agent.agent_name
            self._tick_agents[name] = make_tick_agent(name, params=tick_agent.params)

    def _init_callbacks(self, callbacks: list[CallbackSpec]) -> None:
        callbacks_ = []
        for callback in callbacks:
            callbacks_.append(make_callback(callback.name, **callback.params))
        self._callbacks: CallBackList = CallBackList(callbacks_)
        self._callbacks.set_runner(self)


def test_runner():
    register_battle_planner_modules()
    test_env_spec = EnvSpec(
        name="pysim",
        mode=EnvMode.CREATE,
        link=EnvLink.GYM,
    )

    test_agents = []
    test_callbacks = []
    runner = Runner(test_env_spec, test_agents, test_callbacks)
    runner.reset()
    runner.run(max_step=None)


if __name__ == "__main__":
    test_runner()
