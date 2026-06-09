## Operation Guide

### Response Language

- Use Chinese when answering users unless they explicitly ask for another language.

### Prerequisites

- Python 3.13.
- `uv` installed for dependency management (`uv sync`) and `uv run` for Python commands.
- `make` available to run repository tasks.

### Common Commands

- `make setup`: install dependencies.
- `make format`: format code.
- `make format-check`: verify formatting without modifying files.
- `make test`: run core tests.
- `make check`: run local validation.

### Python Import Paths

- Do not modify `sys.path` inside scripts to make repository imports work.
- Run repository Python scripts with an explicit `PYTHONPATH` instead, usually:
  `PYTHONPATH=.:examples:pythonlib uv run python <script>`.
- For battle planner scripts, prefer:
  `PYTHONPATH=.:examples:pythonlib uv run python examples/battle_planner/scripts/<script>.py`.

### Engineering Boundaries

- Keep `forge.core.lib` generic and small.
- Keep `forge.core.manager` focused on lifecycle, state, and query orchestration.
- Do not put scenario-specific battle planner logic into `forge.core.lib` or `forge.core.manager`.
- Keep environment truth inside adapters and runtimes.
- Capability logic should provide planner-facing summaries, matching, and explanations, not a second simulator legality engine.

### Code Style

- When adding Python comments or docstrings, use Google-style conventions for parameter and return-value sections.
- Keep comments short and purposeful; do not add comments that merely repeat obvious code.

### Change Policy

- Prefer small, reviewable changes.
- Modify only the content explicitly requested by the user; do not change unrelated files or behavior.
- Do not rewrite unrelated files.
- Add or update tests for behavior changes.
- For `examples/battle_planner`, keep pytest tests offline and maintainable: do not add live model probes, manual payload-print tests, or `__main__` debug entrypoints under `tests/`.
- For automation or configuration changes, verify with the matching `make` command.
