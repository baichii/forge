# battle_planner Params

This directory stores curated demo and test configuration for `battle_planner`.

It is intentionally separate from `runtime/presets/` and `artifacts/`:

- `schemes/` contains business-facing scheme and strategy fixtures that can be
  loaded by tests, mocks, or a future backend API.
- `agent_descriptions/` contains exported tick-agent declaration snapshots for
  demo fixtures. Keep fields aligned with `TickAgentSpec` declarations, such as
  `name`, `version`, `entrypoint`, `description`, and `status`. Do not add
  display-only fields that are not present in the declaration.
- `runtime/presets/` remains the place for executable display-mode agent
  parameter presets.
- `artifacts/` remains runtime output and should not be read directly by the
  browser UI.

The Vite UI should copy or transform the curated business data into local mocks
for the first static version. When a backend is introduced, replace those mocks
with an API/provider layer rather than coupling browser code to this directory.
