export type StrategyBranchView = {
  strategyId: string
  name: string
  branchLabel: string
  description: string
  platformSummary: string
  platformItems: string[]
  humanSummary: string
  humanItems: string[]
  tags: string[]
  agentDescriptionIds: string[]
}

export type SchemeView = {
  schemeId: string
  name: string
  scenarioName: string
  side: string
  opponentSide: string
  objective: string
  constraints: string[]
  humanSummary: string
  humanItems: string[]
  branches: StrategyBranchView[]
}

export type BusinessPreference = {
  configuredName: string
  optimizationTarget: string
  riskFocus: string
  constraintNotes: string
  timeWindowPreference: string
  branchPreference: string
  notes: string
}

export type ConfiguredStrategy = {
  id: string
  scope: 'scheme' | 'strategy'
  schemeId: string
  schemeName: string
  scenarioName: string
  strategyId?: string
  strategyName?: string
  configuredName: string
  preferences: BusinessPreference
  savedAt: string
}
