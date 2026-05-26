import type { ConfiguredStrategy } from '../types/strategy'

export const CONFIGURED_STRATEGIES_STORAGE_KEY =
  'battle-planner:configured-strategies'

export function readConfiguredStrategies(): ConfiguredStrategy[] {
  const raw = window.localStorage.getItem(CONFIGURED_STRATEGIES_STORAGE_KEY)
  if (!raw) {
    return []
  }

  try {
    const parsed = JSON.parse(raw) as ConfiguredStrategy[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function saveConfiguredStrategy(payload: ConfiguredStrategy) {
  const existing = readConfiguredStrategies()
  window.localStorage.setItem(
    CONFIGURED_STRATEGIES_STORAGE_KEY,
    JSON.stringify([payload, ...existing], null, 2),
  )
}
