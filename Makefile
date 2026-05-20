BATTLE_PLANNER_PYTHONPATH := .:examples:pythonlib

.PHONY: setup lint format format-check test check run-battle-planner

setup:
	uv sync --all-groups

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix --select I .

format-check:
	uv run ruff format --check .
	uv run ruff check --select I .

test:
	uv run pytest forge/tests -v

run-battle-planner:
	PYTHONPATH=$(BATTLE_PLANNER_PYTHONPATH) uv run python examples/battle_planner/tests/run_zc_lite_demo.py

check: lint format-check test
