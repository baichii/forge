export type KeyEventView = {
  event: string
  label: string
  summary: string
}

export type SimulationReportView = {
  decisionSteps?: number | null
  envDone?: boolean | null
  stopReason?: string
  finalSimTime?: number | null
  elapsedSeconds?: number | null
  agentActionCount?: number | null
}

export type IterationReplayView = {
  iterationIndex: number
  status: string
  agentParamPresetId?: string | null
  score?: number | null
  objectiveAchieved?: boolean | null
  targetInitialHealth?: number | null
  targetCurrentHealth?: number | null
  targetHealthDelta?: number | null
  targetDamageRatio?: number | null
  targetDestroyedCount?: number | null
  requestedWeaponCount?: number | null
  inactiveAgentCount?: number | null
  advice: string
  summaryExcerpt: string
  keyEvents: KeyEventView[]
  simulationReport: SimulationReportView
  error?: string | null
}

export type SessionReplayView = {
  sessionId: string
  status: string
  currentIteration: number
  maxIterations: number
  stopReason: string
  startedAt: string
  updatedAt: string
  iterations: IterationReplayView[]
}

export type SimulationRunDraft = {
  id: string
  configuredStrategyId?: string
  configuredStrategyName: string
  maxIterations: number
  simulationConnection: string
  evaluationFocus: string
  stopCondition: string
  notes: string
  createdAt: string
}
