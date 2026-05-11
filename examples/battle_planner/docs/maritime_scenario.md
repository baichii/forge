# Maritime Battle Planner Scenario

This document owns the business scenario that should not leak into `forge.lib`
or `forge.manager`.

## Scenario

- Small maritime environment.
- Around 5v5 units.
- Three initial command types.
- Opponent agent uses longer cooldowns to leave optimization space.
- The target behavior is to discover short-window breakthrough tactics.
- A baseline should be used to confirm whether planner-discovered tactics create
  measurable improvement.

## Planner-Owned Logic

- prompts
- workflow design
- baseline metrics
- experiment records
- version comparisons
- explanation of improvement sources

## Adapter Dependency

`battle_planner` should depend on a battle environment adapter that implements
forge contracts for:

- entity normalization
- relation and capability judgement
- action intent translation
- manager updates

## Open Design Tension

If the LLM participates in realtime decision-making, the simulation may need a
controlled decision window. Otherwise, task-level planning is based mostly on
the initial global situation and lower-level agents must absorb realtime changes
such as target selection or subject selection.
