export type RiskStyle = 'aggressive' | 'balanced' | 'conservative'

export type TaskBranch = {
  branch_id: number
  name: string
  description: string
  platform: {
    summary?: string
    items?: string[]
  }
  meta?: Record<string, unknown>
}

export type TaskPlan = {
  plan_id: string
  name: string
  scenario_name: string
  side: string
  opponent_side: string
  objective: string
  constraints: string[]
  branches: TaskBranch[]
  meta?: Record<string, unknown>
}

export type PlanHumanInput = {
  goal: string
  risk_style: RiskStyle
  constraints: string[]
  risk_points: string[]
  notes: string
}

export type BranchHumanInput = {
  goal: string
  risk_style: RiskStyle
  constraints: string[]
  risk_points: string[]
  notes: string
}

export type TaskBranchHumanInputRequest = {
  branch_id: number
  human: BranchHumanInput
}

export type TaskContextCreateRequest = {
  plan_id: string
  name: string
  plan_human: PlanHumanInput
  branch_humans: TaskBranchHumanInputRequest[]
}

export type TaskBranchContext = {
  branch_id: number
  name: string
  description: string
  human: BranchHumanInput
  meta?: Record<string, unknown>
}

export type TaskContext = {
  context_id: string
  plan_id: string
  name: string
  plan_name: string
  scenario_name: string
  side: string
  opponent_side: string
  human: PlanHumanInput
  branches: TaskBranchContext[]
  meta: Record<string, unknown>
}

export type TaskContextListItemView = {
  context_id: string
  name: string
  plan_id: string
  plan_name: string
  scenario_name: string
  branch_count: number
  created_at: string
}

export type TaskRunOptions = {
  workflow_name: string
  max_iterations: number
  sim_runs_per_scheme: number
  max_retry: number
  timeout_seconds: number | null
  extra: Record<string, unknown>
}

export type TaskRunCreateRequest = {
  context_id: string
  run_name: string
  options: TaskRunOptions
}

export type RunOutputStatus = 'created' | 'running' | 'completed' | 'failed' | 'cancelled'

export type RunIterationStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped'

export type TaskRunListItemView = {
  run_id: string
  run_name: string
  context_id: string
  context_name: string
  plan_id: string
  plan_name: string
  status: RunOutputStatus
  iteration_count: number
  created_at: string
}

export type RunTextSummary = {
  label: string
  title: string
  summary: string
}

export type RunIterationTag = {
  key: string
  label: string
  reason: string
}

export type RunSimulationRecord = {
  simulation_index: number
  seed: number | null
  simulation_result?: {
    steps?: number
    done?: boolean
    logs?: string[]
    raw_summary?: Record<string, unknown>
    metrics?: Record<string, number | string | boolean | Record<string, unknown>>
  } | null
  callback_reports?: Record<string, unknown>
  summary?: RunTextSummary | null
  meta?: Record<string, unknown>
}

export type RunMetricAggregate = {
  key: string
  name: string
  description: string
  mean: number
  min: number
  max: number
  std: number
}

export type RunMetricTrendPoint = {
  iteration_index: number
  mean: number
  min: number
  max: number
  std: number
}

export type RunMetricTrend = {
  key: string
  name: string
  description: string
  chart_type: 'line'
  points: RunMetricTrendPoint[]
}

export type TickAgentRunParams = {
  agent_name: string
  side: string
  agent_instance_id?: string | null
  params: Record<string, unknown>
}

export type SchemeBranchExecution = {
  branch_id?: number
  planned_agent_params?: TickAgentRunParams[]
  meta?: Record<string, unknown>
}

export type RunIterationOutput = {
  iteration_index: number
  status: RunIterationStatus
  iteration_tags: RunIterationTag[]
  overall_summary?: RunTextSummary | null
  effect_summary?: RunTextSummary | null
  report_summary?: RunTextSummary | null
  decision_summary?: RunTextSummary | null
  scheme?: {
    scheme_id?: number | string
    run_id?: string
    branch_executions?: SchemeBranchExecution[]
    callback_params?: unknown[]
  } | null
  simulation_runs: RunSimulationRecord[]
  metric_aggregates: RunMetricAggregate[]
  meta?: Record<string, unknown>
}

export type RunOutput = {
  run_id: string
  run_name: string
  context_id: string
  context_name: string
  plan_id: string
  plan_name: string
  scenario_name: string
  objective: string
  max_iterations: number | null
  status: RunOutputStatus
  started_at: string
  ended_at: string | null
  iterations: RunIterationOutput[]
  metric_trends: RunMetricTrend[]
  meta: Record<string, unknown>
}
