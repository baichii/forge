export type BattlePlannerApiMode = 'offline' | 'online'

const rawMode = import.meta.env.VITE_BATTLE_PLANNER_API_MODE ?? 'offline'
const rawBaseUrl = import.meta.env.VITE_BATTLE_PLANNER_API_BASE_URL ?? ''

function normalizeMode(value: string): BattlePlannerApiMode {
  return value === 'online' ? 'online' : 'offline'
}

function normalizeBaseUrl(value: string) {
  return value.trim().replace(/\/+$/, '')
}

export const battlePlannerApiConfig = {
  mode: normalizeMode(rawMode),
  baseUrl: normalizeBaseUrl(rawBaseUrl),
  pollIntervalMs: 2000,
} as const

export function requireBattlePlannerBaseUrl() {
  if (!battlePlannerApiConfig.baseUrl) {
    throw new Error('online 模式需要配置 VITE_BATTLE_PLANNER_API_BASE_URL')
  }
  return battlePlannerApiConfig.baseUrl
}
