from __future__ import annotations

from battle_planner.conf import HostMode, LLMMode, Settings, SourceMode


def test_settings_env_file_does_not_override_existing_env(monkeypatch, tmp_path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("HOST=server\nMODEL=from_file\n", encoding="utf-8")

    monkeypatch.setenv("HOST", "local")
    monkeypatch.setenv("MODEL", "from_runtime")
    settings = Settings(_env_file=env_path)

    assert settings.HOST == HostMode.LOCAL
    assert settings.MODEL == "from_runtime"


def test_settings_parse_key_runtime_and_model_env(monkeypatch) -> None:
    monkeypatch.setenv("HOST", "server")
    monkeypatch.setenv("SOURCE", "service")
    monkeypatch.setenv("LLM_MODE", "offline")
    monkeypatch.setenv("WORKFLOW_NAME", "zc_lite_baseline")
    monkeypatch.setenv("MODEL", "by_qwen36")
    monkeypatch.setenv("MODEL_PROFILES", "by_qwen36")

    settings = Settings(_env_file=None)

    assert settings.HOST == HostMode.SERVER
    assert settings.SOURCE == SourceMode.SERVICE
    assert settings.LLM_MODE == LLMMode.OFFLINE
    assert settings.WORKFLOW_NAME == "zc_lite_baseline"
    assert settings.MODEL == "by_qwen36"
    assert settings.model_profile_names == ["by_qwen36"]


def test_settings_defaults(monkeypatch) -> None:
    for name in ["HOST", "SOURCE", "LLM_MODE", "MODEL", "MODEL_PROFILES"]:
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.HOST == HostMode.LOCAL
    assert settings.WORKFLOW_NAME == "zc_lite_baseline"
