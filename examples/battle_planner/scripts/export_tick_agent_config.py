from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES_ROOT = REPO_ROOT / "examples"
PYTHONLIB_ROOT = REPO_ROOT / "pythonlib"
for path in (REPO_ROOT, EXAMPLES_ROOT, PYTHONLIB_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

DEFAULT_DECLARATION = "battle_planner.tick_agents.air_to_sea_strike_tick_agent:declaration"
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "examples"
    / "battle_planner"
    / "tick_agents"
    / "air_to_sea_strike_tick_agent"
    / "config.yaml"
)


def _str_representer(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


yaml.SafeDumper.add_representer(str, _str_representer)


def main() -> None:
    args = _parse_args()
    declaration = _load_declaration(args.declaration)
    payload = declaration.model_dump(mode="json")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"exported {payload['name']} config to {output}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a tick-agent declaration to config.yaml.")
    parser.add_argument(
        "--declaration",
        default=DEFAULT_DECLARATION,
        help="Declaration import path in module:attribute form.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output config.yaml path.",
    )
    return parser.parse_args()


def _load_declaration(import_path: str) -> Any:
    module_name, _, attribute_name = import_path.partition(":")
    if not module_name or not attribute_name:
        raise ValueError(f"Invalid declaration import path: {import_path}")
    module = importlib.import_module(module_name)
    return getattr(module, attribute_name)


if __name__ == "__main__":
    main()
