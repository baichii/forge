from __future__ import annotations

from pathlib import Path

from battle_planner.model.models import SchemeSpec

BATTLE_PLANNER_ROOT = Path(__file__).resolve().parents[2]
LOCAL_WORKSPACE_DIR = BATTLE_PLANNER_ROOT / "workspace" / "local"
SCHEME_CONFIG_DIR = LOCAL_WORKSPACE_DIR / "schemes"
LEGACY_SCHEME_CONFIG_DIR = BATTLE_PLANNER_ROOT / "params" / "schemes"


def resolve_scheme_config_path(name: str | Path) -> Path:
    path = Path(name)
    if path.is_absolute():
        return path
    if path.suffix != ".json":
        path = path.with_suffix(".json")
    source_path = SCHEME_CONFIG_DIR / path
    legacy_path = LEGACY_SCHEME_CONFIG_DIR / path
    if source_path.exists() or not legacy_path.exists():
        return source_path
    return legacy_path


def load_scheme_config(name: str | Path) -> SchemeSpec:
    path = resolve_scheme_config_path(name)
    return SchemeSpec.model_validate_json(path.read_text(encoding="utf-8"))
