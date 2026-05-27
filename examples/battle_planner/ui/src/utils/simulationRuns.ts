import type { SimulationRunDraft } from '../types/session'

const SIMULATION_RUN_DRAFTS_STORAGE_KEY = 'battle-planner:simulation-run-drafts'

export function readSimulationRunDrafts(): SimulationRunDraft[] {
  const raw = window.localStorage.getItem(SIMULATION_RUN_DRAFTS_STORAGE_KEY)
  if (!raw) {
    return []
  }

  try {
    const parsed = JSON.parse(raw) as SimulationRunDraft[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function saveSimulationRunDraft(payload: SimulationRunDraft) {
  const existing = readSimulationRunDrafts()
  window.localStorage.setItem(
    SIMULATION_RUN_DRAFTS_STORAGE_KEY,
    JSON.stringify([payload, ...existing], null, 2),
  )
}
