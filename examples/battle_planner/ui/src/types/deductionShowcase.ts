export type DeductionStatusTone = 'success' | 'processing' | 'warning' | 'default'

export type DeductionStrategyBranchSummary = {
  id: string
  name: string
  summary: string
}

export type DeductionStrategySummary = {
  id: string
  name: string
  description: string
  objective: string
  branches: DeductionStrategyBranchSummary[]
}

export type DeductionEffectSummary = {
  title: string
  subtitle: string
  currentTime: string
  progress: string
  summary: string
}

export type DeductionStage = {
  id: string
  index: string
  title: string
  status: string
  statusTone: DeductionStatusTone
  time: string
  description: string
}

export type DeductionMetric = {
  label: string
  value: string
  trend: string
  tone: DeductionStatusTone
}

export type DeductionEvent = {
  time: string
  title: string
  detail: string
  tone: DeductionStatusTone
}

export type DeductionAgentStatus = {
  name: string
  role: string
  status: string
  summary: string
}

export type DeductionReplayRound = {
  id: string
  label: string
  version: string
  status: string
  statusTone: DeductionStatusTone
  effect: DeductionEffectSummary
  stages: DeductionStage[]
  metrics: DeductionMetric[]
  events: DeductionEvent[]
  agents: DeductionAgentStatus[]
}

export type DeductionReplaySession = {
  id: string
  displayName: string
  strategy: DeductionStrategySummary
  rounds: DeductionReplayRound[]
}

export type DeductionShowcaseView = {
  sessions: DeductionReplaySession[]
}
