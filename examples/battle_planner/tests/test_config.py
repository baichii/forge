from __future__ import annotations

from battle_planner.conf import LLMMode, RuntimeMode, Settings, SourceMode


def test_settings_env_file_does_not_override_existing_env(monkeypatch, tmp_path) -> None:
    """验证运行时环境变量优先于 .env 文件。"""

    env_path = tmp_path / ".env"
    env_path.write_text("RUNTIME_MODE=server\nMODEL=from_file\n", encoding="utf-8")

    monkeypatch.setenv("RUNTIME_MODE", "local_dev")
    monkeypatch.setenv("MODEL", "from_runtime")
    settings = Settings(_env_file=env_path)

    assert settings.RUNTIME_MODE == RuntimeMode.LOCAL_DEV
    assert settings.MODEL == "from_runtime"


def test_settings_parse_key_runtime_and_model_env(monkeypatch) -> None:
    """验证关键运行配置能从环境变量解析。"""

    monkeypatch.setenv("RUNTIME_MODE", "server")
    monkeypatch.setenv("SOURCE", "service")
    monkeypatch.setenv("LLM_MODE", "offline")
    monkeypatch.setenv("WORKFLOW_NAME", "zc_lite_baseline")
    monkeypatch.setenv("VERBOSE", "2")
    monkeypatch.setenv("MODEL", "by_qwen36")
    monkeypatch.setenv("MODEL_PROFILES", "by_qwen36")

    settings = Settings(_env_file=None)

    assert settings.RUNTIME_MODE == RuntimeMode.SERVER
    assert settings.SOURCE == SourceMode.SERVICE
    assert settings.LLM_MODE == LLMMode.OFFLINE
    assert settings.WORKFLOW_NAME == "zc_lite_baseline"
    assert settings.VERBOSE == 2
    assert settings.MODEL == "by_qwen36"
    assert settings.model_profile_names == ["by_qwen36"]


def test_settings_defaults(monkeypatch) -> None:
    """验证未设置环境变量时使用默认配置。"""

    for name in ["RUNTIME_MODE", "SOURCE", "LLM_MODE", "VERBOSE", "MODEL", "MODEL_PROFILES"]:
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.RUNTIME_MODE == RuntimeMode.LOCAL_DEV
    assert settings.WORKFLOW_NAME == "zc_lite_baseline"
    assert settings.VERBOSE == 1


def test_runtime_mode_derives_artifact_behavior() -> None:
    """验证运行形态能派生产物行为。"""

    modes = {
        RuntimeMode.LOCAL_DEV: (True, False, False),
        RuntimeMode.LOCAL_FULL: (True, True, False),
        RuntimeMode.SERVER: (False, True, True),
    }

    for runtime_mode, expected in modes.items():
        settings = Settings(_env_file=None, RUNTIME_MODE=runtime_mode)
        assert (
            settings.should_print_artifacts,
            settings.should_store_artifacts,
            settings.should_serve_artifacts,
        ) == expected
