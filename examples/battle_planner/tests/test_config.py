from __future__ import annotations

import os


def test_dotenv_does_not_override_existing_env(monkeypatch, tmp_path) -> None:
    from battle_planner.config import load_battle_planner_env

    env_path = tmp_path / ".env"
    env_path.write_text("BATTLE_PLANNER_TEST_PRIORITY=from_dotenv\n", encoding="utf-8")

    monkeypatch.setenv("BATTLE_PLANNER_TEST_PRIORITY", "from_runtime")
    load_battle_planner_env(env_path, override=False)

    assert os.environ["BATTLE_PLANNER_TEST_PRIORITY"] == "from_runtime"


def test_config_groups_parse_env_values(monkeypatch) -> None:
    from battle_planner.config import ModelConfig, ReportConfig, SimulationConfig, WorkflowConfig

    monkeypatch.setenv("MODEL", "local_test")
    monkeypatch.setenv("MODEL_PROFILES", "local_test,offline")
    monkeypatch.setenv("MODEL_LOCAL_TEST_PROVIDER", "local")
    monkeypatch.setenv("MODEL_LOCAL_TEST_API_URL", "http://localhost:8000/v1")
    monkeypatch.setenv("MODEL_LOCAL_TEST_API_KEY", "dummy")
    monkeypatch.setenv("MODEL_LOCAL_TEST_MODEL_NAME", "test-model")
    monkeypatch.setenv("MODEL_LOCAL_TEST_REASONING_EFFORT", "high")
    monkeypatch.setenv("MODEL_LOCAL_TEST_THINKING_TYPE", "enabled")
    monkeypatch.setenv("MODEL_OFFLINE_PROVIDER", "offline")
    monkeypatch.setenv("MODEL_OFFLINE_MODEL_NAME", "offline")
    monkeypatch.setenv("BATTLE_PLANNER_LLM_MAX_TOKENS", "4096")
    monkeypatch.setenv("BATTLE_PLANNER_LLM_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("BATTLE_PLANNER_LLM_MAX_RETRY", "3")
    monkeypatch.setenv("BATTLE_PLANNER_MAX_STAGE_RETRY", "4")
    monkeypatch.setenv("BATTLE_PLANNER_WORKFLOW_MAX_ITERATIONS", "2")
    monkeypatch.setenv("BATTLE_PLANNER_FAIL_FAST", "true")
    monkeypatch.setenv("BATTLE_PLANNER_SAVE_ARTIFACTS", "false")
    monkeypatch.setenv("BATTLE_PLANNER_DISPLAY_MODE", "true")
    monkeypatch.setenv("BATTLE_PLANNER_SIM_RUNS_PER_PLAN", "5")
    monkeypatch.setenv("BATTLE_PLANNER_SIM_MAX_PARALLEL", "2")
    monkeypatch.setenv("BATTLE_PLANNER_SIM_MAX_DECISION_STEPS", "7")
    monkeypatch.setenv("BATTLE_PLANNER_SIM_MAX_FAILURES", "2")
    monkeypatch.setenv("BATTLE_PLANNER_SIM_RANDOM_SEED", "42")
    monkeypatch.setenv("BATTLE_PLANNER_REPORT_LEVEL", "standard")
    monkeypatch.setenv("BATTLE_PLANNER_REPORT_INCLUDE_LLM_TRACE", "false")

    model = ModelConfig.from_env()
    workflow = WorkflowConfig.from_env()
    simulation = SimulationConfig.from_env()
    report = ReportConfig.from_env()

    assert model.selected == "local_test"
    assert workflow.max_iterations == 2
    assert workflow.display_mode is True
    assert simulation.max_decision_steps == 7
    assert report.level == "standard"


def test_model_config_defaults_to_deepseek_profile(monkeypatch) -> None:
    from battle_planner.config import ModelConfig

    monkeypatch.delenv("MODEL", raising=False)
    monkeypatch.delenv("MODEL_PROFILES", raising=False)

    model = ModelConfig.from_env()

    assert model.selected == "deepseek_v4_pro"
    assert "deepseek_v4_pro" in model.profiles


def test_model_provider_rejects_requested_model_mismatch() -> None:
    from battle_planner.llm_runtime.model_provider import ModelRequest, OpenAICompatibleModelProvider

    provider = OpenAICompatibleModelProvider(
        name="local_test",
        base_url="http://localhost:8000/v1",
        api_key="dummy",
        model="configured-model",
    )

    response = provider.complete(ModelRequest(messages=[], model="other-model"))

    assert "does not match configured model" in response.error


def test_model_provider_passes_reasoning_and_thinking_options(monkeypatch) -> None:
    from battle_planner.llm_runtime import model_provider
    from battle_planner.llm_runtime.model_provider import ModelRequest, OpenAICompatibleModelProvider

    captured: dict = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            message = type(
                "Message",
                (),
                {
                    "content": '{"agents":[]}',
                    "reasoning_content": "hidden reasoning",
                },
            )()
            choice = type("Choice", (), {"message": message})()
            return type("Response", (), {"choices": [choice]})()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setattr(model_provider, "OpenAI", FakeOpenAI)
    provider = OpenAICompatibleModelProvider(
        name="deepseek_v4_pro",
        base_url="https://api.deepseek.com",
        api_key="dummy",
        model="deepseek-v4-pro",
        reasoning_effort="high",
        thinking_type="enabled",
    )

    provider.complete(ModelRequest(messages=[{"role": "user", "content": "hello"}]))

    assert captured["reasoning_effort"] == "high"
    assert captured["extra_body"] == {"thinking": {"type": "enabled"}}


def test_simulation_config_defaults_to_env_terminal_control(monkeypatch) -> None:
    from battle_planner.config import SimulationConfig

    monkeypatch.delenv("BATTLE_PLANNER_SIM_MAX_DECISION_STEPS", raising=False)

    simulation = SimulationConfig.from_env()

    assert simulation.max_decision_steps is None


def test_workflow_config_defaults(monkeypatch) -> None:
    from battle_planner.config import WorkflowConfig

    monkeypatch.delenv("BATTLE_PLANNER_DISPLAY_MODE", raising=False)
    monkeypatch.delenv("BATTLE_PLANNER_WORKFLOW_MAX_ITERATIONS", raising=False)

    workflow = WorkflowConfig.from_env()

    assert workflow.max_iterations == 5
    assert workflow.display_mode is False
