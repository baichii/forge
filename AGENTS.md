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

### Engineering Boundaries

- Keep `forge.lib` generic and small.
- Keep `forge.manager` focused on lifecycle, state, and query orchestration.
- Do not put scenario-specific battle planner logic into `forge.lib` or `forge.manager`.
- Keep environment truth inside adapters and runtimes.
- Capability logic should provide planner-facing summaries, matching, and explanations, not a second simulator legality engine.

### Change Policy

- Prefer small, reviewable changes.
- Modify only the content explicitly requested by the user; do not change unrelated files or behavior.
- Do not rewrite unrelated files.
- Add or update tests for behavior changes.
- For automation or configuration changes, verify with the matching `make` command.
