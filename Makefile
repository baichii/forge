.PHONY: setup lint format format-check test check

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

check: lint format-check test
