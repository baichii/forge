from __future__ import annotations


class WorkflowStages:
    """workflow 对外可见阶段名。"""

    START = "start"
    ERROR = "error"
    COMPLETE = "complete"
    SCENARIO_PREPARATION = "scenario_preparation"
    SCENARIO_UNDERSTANDING = "scenario_understanding"
    BATTLE_PLAN_GENERATION = "battle_plan_generation"
    AGENT_SCHEMA_LOADING = "agent_schema_loading"
    AGENT_PARAMETER_PLANNING = "agent_parameter_planning"
    SIMULATION_EXECUTION = "simulation_execution"
    RESULT_EVALUATION = "result_evaluation"
    SUMMARY_GENERATION = "summary_generation"
