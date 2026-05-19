import time
import datetime
from typing import Any

from forge.utils.specs import EnvSpec, EnvMode, EnvLink, TickAgentSpec, CallbackSpec
from forge.env import Runner as BaseRuner
from forge.lib.callback import CallBackList



class Runner(BaseRuner):
    """测试runner， hard code

    Notes:
        1. 必要条件，runner必须具备基于config启动的能力，env和agent都要在内部构造而不能作为实例输入
        2. 对于需要在不同callback中频繁统计的信息，应该在env外封装一个wrapper，在wrapper层实现中间指标计算

    """

    def __init__(self, env_spec, tick_agents: list[TickAgentSpec], callbacks: list[CallbackSpec]):

        # env/agent/callback init
        self._init_env(env_spec)
        self._init_tick_agents(tick_agents)
        self._init_callbacks(callbacks)

        #
        self._on_begin()

        # others
        self._last_actions = []
        self._start_time = time.time()
        self._end_time = self._start_time

    def reset(self):
        self.env.reset()

    def run(self, max_step: int | None=None) -> Any:
        step = 0
        while True:
            observation, terminated, truncated, info =  self.run_step()
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
        self._callbacks.on_begin()

    def run_step(self):
        self._on_step_begin()
        observation, _, terminated, truncated, info = self.env.step(self._last_actions)
        actions = []
        for _, tick_agent in self._tick_agents.items():
            action, status, done, info = tick_agent.step(observation)
            actions.extend(action)
        self._last_actions = actions
        self._on_step_end()
        return observation, terminated, truncated, info

    def _init_env(self, env_spec) -> None:
        # todo: 优化为参数解析
        from pysim import Sim
        from scenario.scenario_zc_lite import scenario_conf
        self._env = Sim(scenario_conf, subscribe_cont=True)

    def _init_tick_agents(self, tick_agents: list[TickAgentSpec]) -> None:
        self._tick_agents = {}
        for tick_agent in tick_agents:
            # todo: 初始化agent
            pass

    def _init_callbacks(self, callbacks: list[CallbackSpec]) -> None:
        callbacks_ = []
        for callback in callbacks:
            pass
        self._callbacks: CallBackList = CallBackList(callbacks_)





def test_runner():
    test_env_spec = EnvSpec(
        name="test env spec",
        mode=EnvMode.CREATE,
        link=EnvLink.GYM,
        params={
            "scenario": "zc3_lite",
            "seed": 42,
        }
    )

    test_agents = []
    test_callbacks = []
    runner = Runner(test_env_spec, test_agents, test_callbacks)
    runner.reset()
    runner.run()


if __name__ == '__main__':
    test_runner()