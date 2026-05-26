from __future__ import annotations

from pathlib import Path

from battle_planner.data.models import SchemeSpec

BATTLE_PLANNER_ROOT = Path(__file__).resolve().parents[1]
PARAMS_DIR = BATTLE_PLANNER_ROOT / "params"
SCHEME_CONFIG_DIR = PARAMS_DIR / "schemes"


def resolve_scheme_config_path(name: str | Path) -> Path:
    path = Path(name)
    if path.is_absolute():
        return path
    if path.suffix != ".json":
        path = path.with_suffix(".json")
    return SCHEME_CONFIG_DIR / path


def load_scheme_config(name: str | Path) -> SchemeSpec:
    path = resolve_scheme_config_path(name)
    return SchemeSpec.model_validate_json(path.read_text(encoding="utf-8"))
