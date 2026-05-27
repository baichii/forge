export type ReplayStrategySummary = {
  id: string
  name: string
  schemeName: string
  branchName: string
  description: string
  savedAt: string
}

export type ReplaySessionSummary = {
  sessionId: string
  displayName: string
  status: string
  totalRounds: number
  seedCount: number
  startedAt: string
  updatedAt: string
  stopReason: string
}

export type ReplaySessionImplementation = {
  title: string
  description: string
  items: Array<{
    label: string
    value: string
  }>
}

export type ReplayMetricSet = {
  score: number
  targetDamageRatio: number
  weaponCostRatio: number
  platformRiskRatio: number
  successRate: number
  inactiveAgentCount: number
  constraintViolationCount: number
}

export type ReplayExecutionPlan = {
  planName: string
  timeWindowSummary: string
  agents: string[]
  targets: string[]
  weaponSummary: string
  plannedActionCount: number
  dispatchedActionCount: number
  inactiveAgents: string[]
  maxSimulationSteps: number
}

export type ReplayParameterDiff = {
  name: string
  previousValue: string
  currentValue: string
  direction: string
  reason: string
  impact: string
}

export type ReplayFailureReason = {
  reason: string
  count: number
  summary: string
}

export type ReplaySeedRun = {
  seed: number
  status: string
  score: number
  targetDamageRatio: number
  weaponCostRatio: number
  platformRiskRatio: number
  success: boolean
  failureReason?: string
}

export type ReplaySeedStats = {
  seedCount: number
  meanScore: number
  bestScore: number
  worstScore: number
  stdScore: number
  successRate: number
  volatilityLevel: string
  failureReasons: ReplayFailureReason[]
}

export type ReplayDataSupportKind = 'direct' | 'derived' | 'unsupported'

export type ReplayDataSupportItem = {
  label: string
  support: ReplayDataSupportKind
  source: string
  note: string
}

export type ReplayDecision = {
  status: string
  recommendation: string
  rationale: string
}

export type ReplayRound = {
  roundId: string
  roundNumber: number
  label: string
  title: string
  summary: string
  metrics: ReplayMetricSet
  reportSummary: string
  llmDiagnosis: string
  decision: ReplayDecision
  executionPlan: ReplayExecutionPlan
  parameterDiff: ReplayParameterDiff[]
  seedStats: ReplaySeedStats
  seedRuns: ReplaySeedRun[]
}

export type StrategyIterationReplay = {
  configuredStrategy: ReplayStrategySummary
  selectedSession: ReplaySessionSummary
  implementation: ReplaySessionImplementation
  recommendedRoundId: string
  rounds: ReplayRound[]
  dataSupport: ReplayDataSupportItem[]
}
