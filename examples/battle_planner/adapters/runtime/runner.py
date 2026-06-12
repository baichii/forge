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
    """runner状态"""

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
        3. 评估，拆成2个体系去做这个工作，
            - 业务评估，业务侧开发实现，继承callback进行开发，接收env的observation返回
            - 系统评估，系统侧开发实现，暂时固化在report中，接收，env info返回和tick-agent返回

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
            self._callbacks.on_step_begin()
            observation, terminated, truncated, _ = self.run_step()
            self._callbacks.observe(observation)
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
            system_evaluation=self._build_system_evaluation_report(),
        )

    def _build_system_evaluation_report(self) -> dict[str, Any]:
        return {
            "agent_execution": self._build_agent_execution_evaluation(),
            "weapon_usage": self._build_weapon_usage_evaluation(),
        }

    def _build_agent_execution_evaluation(self) -> dict[str, Any]:
        agent_records = []
        total_action_count = 0
        executed_agent_count = 0

        for report in self._agent_reports.values():
            executed = report.action_count > 0
            total_action_count += report.action_count
            if executed:
                executed_agent_count += 1
            agent_records.append(
                {
                    "agent_instance_id": report.agent_instance_id,
                    "agent_name": report.agent_name,
                    "side": report.side,
                    "action_count": report.action_count,
                    "executed": executed,
                    "first_active_step": report.first_active_step,
                    "finished_step": report.finished_step,
                    "event_count": len(report.events),
                    "status_history_count": len(report.status_history),
                }
            )

        agent_count = len(agent_records)
        inactive_agent_count = agent_count - executed_agent_count
        execution_rate = executed_agent_count / agent_count if agent_count else 0.0

        return {
            "metrics": {
                "agent_count": agent_count,
                "executed_agent_count": executed_agent_count,
                "inactive_agent_count": inactive_agent_count,
                "agent_execution_rate": round(execution_rate, 4),
                "agent_action_count": total_action_count,
            },
            "details": {"agents": agent_records},
        }

    def _build_weapon_usage_evaluation(self) -> dict[str, Any]:
        requested_weapon_count = 0
        weapon_action_count = 0
        action_records = []

        for report in self._agent_reports.values():
            for event in report.events:
                for action in _as_list(event.get("raw_actions")):
                    action_payload = action if isinstance(action, dict) else {}
                    weapon_count = _weapon_count_from_action(action_payload)
                    if weapon_count <= 0:
                        continue
                    requested_weapon_count += weapon_count
                    weapon_action_count += 1
                    action_records.append(
                        {
                            "agent_instance_id": report.agent_instance_id,
                            "agent_name": report.agent_name,
                            "step": event.get("step"),
                            "sim_time": event.get("sim_time"),
                            "requested_weapon_count": weapon_count,
                            "raw_action": action_payload,
                        }
                    )

        return {
            "metrics": {
                "requested_weapon_count": requested_weapon_count,
                "weapon_action_count": weapon_action_count,
            },
            "details": {"weapon_actions": action_records},
        }

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
        if _is_agent_running(status) and report.first_active_step is None:
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


def _is_agent_running(status: dict[str, bool]) -> bool:
    return bool(status.get("运行中") or status.get("running"))


def _weapon_count_from_action(action: dict[str, Any]) -> int:
    action_params = _as_dict(action.get("params"))
    mission_params = _as_dict(action_params.get("params"))
    unit_ids = _as_list(mission_params.get("unit_ids"))
    unit_count = max(1, len(unit_ids))

    for key in ("wp_num", "wp_nums", "weapon_nums"):
        value = mission_params.get(key)
        if isinstance(value, list):
            return _sum_ints(value)
        if isinstance(value, int | float) and not isinstance(value, bool):
            return max(0, int(value)) * unit_count
    return 0


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _sum_ints(values: list[Any]) -> int:
    total = 0
    for value in values:
        if isinstance(value, int | float) and not isinstance(value, bool):
            total += max(0, int(value))
    return total
