# battle_planner UI Operation Guide

## Scope

This guide applies to the front-end application under `examples/battle_planner/ui`.

The UI is a static strategy-iteration workbench for `battle_planner`. Treat it as a
business-facing application that may later be embedded into a larger platform. Do not
turn it into a generic Vite demo, a marketing page, or an agent-flow editor.

## Technology Stack

- Use React + TypeScript + Vite for all application code.
- Use Ant Design as the production component system for pages, forms, navigation,
  tables, cards, descriptions, timelines, and feedback states.
- When adding front-end dependencies, update both `package.json` and
  `package-lock.json`.
- Keep the UI project independent from the Python runtime. Do not import Python
  artifacts or runtime code directly into the Vite app.

## Directory Conventions

- `src/types/`: domain types and UI view models, such as `Scheme`, `StrategyBranch`,
  `ConfiguredStrategy`, `SessionView`, and `IterationView`.
- `src/mocks/`: static schemes, configured strategy examples, and session replay
  fixtures. Do not inline large mock payloads in React components.
- `src/pages/`: page-level components. The first version includes the workspace home
  page, scheme configuration page, strategy iteration page, and simulation showcase
  page.
- `src/components/`: reusable UI components, such as metric cards, strategy cards,
  session summaries, iteration timelines, and detail panels.
- `src/layouts/`: workbench shell, navigation, page frames, and shared layout
  structure.
- `src/styles/`: global reset, shared design tokens, Ant Design token overrides, and
  other cross-page styles.

## Styling Rules

- Keep styles independent from component logic. Put business component styles in
  dedicated CSS or CSS Module files instead of large inline style objects in TSX.
- Put shared variables and global visual rules in `src/styles/`.
- Keep page-specific styles near the owning page or component.
- Prefer Ant Design primitives before writing custom controls.
- Use a professional, restrained, data-dense visual style. The default visual direction
  is a warm editorial workbench: parchment background, ivory cards, warm near-black
  text, terracotta primary actions, light ring-like borders, and very soft elevation.
- Ant Design is the component skeleton, not the visual identity. Do not fall back to
  the default AntD blue-and-white admin look unless a feature explicitly needs a
  semantic blue state.
- Keep blue, green, red, and yellow mostly for semantic data signals such as own side,
  success, danger, warning, and metric status. Primary navigation and CTAs should use
  the warm terracotta accent from `src/styles/`.
- Avoid marketing-style heroes, decorative dashboards, oversized visual effects, and
  complex admin-system chrome.
- The home page should keep only one short explanation and three entries:
  scheme configuration, strategy iteration, and simulation showcase. The Chinese
  labels should be `方案配置`, `策略迭代`, and `推演展示`.
- Do not use literal count headings such as `三个入口` for navigation areas. Prefer
  workflow-oriented copy, for example `从方案到推演`, when introducing the module
  cards.
- The home page should fit comfortably in one desktop viewport when possible. Compress
  vertical whitespace before shrinking the typography or cards; the page should feel
  substantial, not tiny.
- Do not duplicate module navigation with hero CTA buttons. Keep module entry actions
  on the three business cards.

## Data Boundary

- The first version uses local mock data and curated session fixtures only.
- Do not read directly from `examples/battle_planner/artifacts/` in browser code.
  That directory is runtime output and may be ignored by git.
- If a future backend is introduced, replace the mock provider/API layer rather than
  coupling page components to transport details.
- UI data should be shaped around business-facing concepts: schemes, strategy
  branches, configured strategies, sessions, iterations, metrics, summaries, and
  artifacts.

## Business Boundary

- Build for business users reviewing scheme intent, strategy preferences, iteration
  metrics, summaries, and replay evidence.
- Do not expose technical runtime parameters in the business UI, including `unit_ids`,
  runner details, callbacks, agent runtime config, or raw execution plumbing.
- Keep agent/runtime implementation details behind mock providers or future API
  adapters.

## Prototype Reference

- `dev/index.html` is a visual and information-architecture reference for the first
  home-page prototype.
- Do not copy its sandbox bridge scripts, snapshot scripts, injected attributes, or
  full inline style block into production React code.
- Rebuild the useful parts with React, TypeScript, Ant Design, and local styles.
- Simulation showcase is part of the workbench entry structure after the initial home
  prototype. Keep it business-facing: select a configured strategy, connect to
  simulation, and display live effects such as session status, current iteration,
  event stream, tactical view, and key metrics rather than raw runner internals.

## Verification

- After UI code changes, run these commands from `examples/battle_planner/ui`:

  ```bash
  npm run lint
  npm run build
  ```

- Documentation-only changes to this `AGENTS.md` file do not require a UI build.
- For page work, also verify the three pages in a browser at desktop and mobile
  widths. Text should not overflow, overlap, or leave the main content blank.
