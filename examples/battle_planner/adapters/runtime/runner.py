import enum
import time
from typing import Any

from battle_planner.adapters.runtime.specs import (
    BattlefieldReport,
    EnvRunReport,
    RunnerReport,
    TickAgentReport,
)
from battle_planner.registry import register_battle_planner_modules

from forge.core.lib.callback import CallBackList
from forge.core.runtime import Runner as BaseRuner
from forge.core.specs import CallbackParams, EnvLink, EnvMode, EnvParams, TickAgentParams
from forge.registration import make_callback, make_env, make_tick_agent
from forge.utils.common_utils import make_id_generator


class RunnerStatus(enum.StrEnum):
    """runner 逻辑"""

    INIT = enum.auto()
    RUNNING = enum.auto()
    MAX_STEP = enum.auto()
    ENV_TRUNCATED = enum.auto()
    ENV_TERMINAL = enum.auto()


class Runner(BaseRuner):
    """测试runner， hard code

    Notes:
        1. 必要条件，runner必须具备基于config启动的能力，env和agent都要在内部构造而不能作为实例输入
        2. 对于需要在不同callback中频繁统计的信息，应该在env外封装一个wrapper，在wrapper层实现中间指标计算

    """

    def __init__(
        self,
        env: EnvParams,
        tick_agents: list[TickAgentParams],
        callbacks: list[CallbackParams],
    ):
        self._init_env(env)
        self._id_generator = make_id_generator()
        self._init_tick_agents(tick_agents)
        self._init_callbacks(callbacks)

        # global setting
        self._last_actions = []
        self._start_time = time.time()
        self._end_time = self._start_time
        self._status = RunnerStatus.INIT
        self._step = 0
        self._max_step: int | None = None
        self._last_observation: dict[str, Any] = {}
        self._init_report_state()

    def reset(self):
        self._env.reset()
        self._id_generator.reset()
        self.set_status(RunnerStatus.RUNNING)

    def run(self, max_step: int | None = None) -> Any:
        self._callbacks.on_begin()
        self._max_step = max_step
        while True:
            # step callbacks
            self._callbacks.on_step_begin()
            observation, terminated, truncated, info = self.run_step()
            self._callbacks.on_step_end()

            self._last_observation = observation if isinstance(observation, dict) else {}
            self._update_status(terminated=terminated, truncated=truncated)
            if self._is_terminal():
                break
        self._end_time = time.time()
        self._callbacks.on_end()
        return self.report()

    def run_step(self):
        self._step += 1
        observation, _, terminated, truncated, info = self._env.step(self._last_actions)
        sim_time = observation.get("sim_time") if isinstance(observation, dict) else None
        if isinstance(info, dict):
            self._battlefield_events.extend(info.get("battlefield_events", []))
        actions = []
        for agent_instance_id, tick_agent in self._tick_agents.items():
            action, status, done, agent_info = tick_agent.step(observation)
            for action_ in action:
                action_["side"] = tick_agent.side
            actions.extend(action)
            self._record_tick_agent_step(
                agent_instance_id=agent_instance_id,
                actions=action,
                status=status,
                done=done,
                info=agent_info,
                sim_time=sim_time,
            )
        self._last_actions = actions
        return observation, terminated, truncated, info

    def _init_env(self, env_params: EnvParams) -> None:
        self._env_params = env_params
        self._env = make_env(env_params.name, **env_params.params)

    def _init_tick_agents(self, tick_agents: list[TickAgentParams]) -> None:
        self._tick_agents = {}
        for tick_agent in tick_agents:
            agent_name = tick_agent.agent_name
            agent_instance_id = tick_agent.agent_instance_id or self._id_generator(agent_name)
            tick_agent_params = tick_agent.model_copy(update={"agent_instance_id": agent_instance_id})
            self._tick_agents[agent_instance_id] = make_tick_agent(agent_name, params=tick_agent_params)

    def _init_callbacks(self, callbacks: list[CallbackParams]) -> None:
        callbacks_ = []
        for callback in callbacks:
            callback_instance_id = callback.callback_instance_id or self._id_generator(callback.name)
            callback_params = callback.model_copy(update={"callback_instance_id": callback_instance_id})
            callbacks_.append(
                make_callback(
                    callback.name,
                    params=callback_params,
                )
            )
        self._callbacks: CallBackList = CallBackList(callbacks_)
        self._callbacks.set_runner(self)

    def _init_report_state(self) -> None:
        self._battlefield_events: list[BattlefieldReport] = []
        self._agent_reports: dict[str, TickAgentReport] = {
            agent_instance_id: TickAgentReport(
                agent_instance_id=agent_instance_id,
                agent_name=tick_agent.name,
                side=tick_agent.side,
            )
            for agent_instance_id, tick_agent in self._tick_agents.items()
        }

    def set_status(self, status: RunnerStatus):
        self._status = status

    def _update_status(self, *, terminated: bool, truncated: bool) -> None:
        if terminated:
            self.set_status(RunnerStatus.ENV_TERMINAL)
        elif truncated:
            self.set_status(RunnerStatus.ENV_TRUNCATED)
        elif self._max_step and self._step >= self._max_step:
            self.set_status(RunnerStatus.MAX_STEP)

    def _is_terminal(self) -> bool:
        return self._status in {
            RunnerStatus.ENV_TRUNCATED,
            RunnerStatus.ENV_TERMINAL,
            RunnerStatus.MAX_STEP,
        }

    def report(self) -> RunnerReport:
        end_time = self._end_time if self._end_time > self._start_time else time.time()
        return RunnerReport(
            env=EnvRunReport(
                env_name=self._env_params.name,
                seed=self._env_params.params.get("seed"),
                max_steps=self._max_step,
                step_count=self._step,
                elapsed_seconds=end_time - self._start_time,
                stop_reason=self._status.value,
                final_sim_time=self._last_observation.get("sim_time"),
            ),
            agents=list(self._agent_reports.values()),
            battlefield_events=self._battlefield_events,
            callbacks=self._callbacks.result(),
        )

    def _record_tick_agent_step(
        self,
        *,
        agent_instance_id: str,
        actions: list[Any],
        status: dict[str, bool],
        done: bool,
        info: dict[str, Any],
        sim_time: float | None,
    ) -> None:
        report = self._agent_reports[agent_instance_id]
        report.action_count += len(actions)
        last_status = report.status_history[-1]["status"] if report.status_history else None
        if status != last_status:
            report.status_history.append(
                {
                    "step": self._step,
                    "sim_time": sim_time,
                    "status": status,
                    "done": done,
                }
            )
        if status.get("running") and report.first_active_step is None:
            report.first_active_step = self._step
            report.first_active_sim_time = sim_time
        if done and report.finished_step is None:
            report.finished_step = self._step
            report.finished_sim_time = sim_time

        if not actions:
            return
        report.events.append(
            {
                "step": self._step,
                "sim_time": sim_time,
                "event_type": "dispatched",
                "info": info,
                "action_count": len(actions),
                "raw_actions": actions,
            }
        )


def test_runner():
    register_battle_planner_modules()
    test_env_params = EnvParams(
        name="pysim",
        mode=EnvMode.CREATE,
        link=EnvLink.GYM,
    )

    test_agents = []
    test_callbacks = []
    runner = Runner(env=test_env_params, tick_agents=test_agents, callbacks=test_callbacks)
    runner.reset()
    runner.run(max_step=None)


if __name__ == "__main__":
    test_runner()
