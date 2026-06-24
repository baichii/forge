import {
  createMockContext,
  createMockRun,
  getMockContext,
  getMockPlan,
  getMockRun,
  listMockContexts,
  listMockPlans,
  listMockRuns,
} from './mockBackendData'
import { battlePlannerApiConfig, requireBattlePlannerBaseUrl } from './config'
import type {
  RunOutput,
  RunOutputStatus,
  TaskContext,
  TaskContextCreateRequest,
  TaskContextListItemView,
  TaskPlan,
  TaskRunCreateRequest,
  TaskRunListItemView,
} from './types'

export type RunWatchEvent = {
  type: string
  run_id: string
  iteration_index?: number
  status?: RunOutputStatus
  reason?: string
  message?: string
}

export type RunWatchHandlers = {
  onUpdate: (run: RunOutput, event?: RunWatchEvent) => void
  onError?: (error: Error) => void
}

export type RunWatchUnsubscribe = () => void

export type BattlePlannerClient = {
  listPlans: () => Promise<TaskPlan[]>
  getPlan: (planId: string) => Promise<TaskPlan>
  createContext: (request: TaskContextCreateRequest) => Promise<TaskContext>
  listContexts: () => Promise<TaskContextListItemView[]>
  getContext: (contextId: string) => Promise<TaskContext>
  createRun: (request: TaskRunCreateRequest) => Promise<RunOutput>
  listRuns: () => Promise<TaskRunListItemView[]>
  getRun: (runId: string) => Promise<RunOutput>
  watchRun: (runId: string, handlers: RunWatchHandlers) => RunWatchUnsubscribe
}

const mockClient: BattlePlannerClient = {
  listPlans: listMockPlans,
  getPlan: getMockPlan,
  createContext: createMockContext,
  listContexts: listMockContexts,
  getContext: getMockContext,
  createRun: createMockRun,
  listRuns: listMockRuns,
  getRun: getMockRun,
  watchRun: () => () => undefined,
}

function buildApiUrl(path: string) {
  return `${requireBattlePlannerBaseUrl()}${path}`
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  })
  if (!response.ok) {
    throw new Error(await responseErrorMessage(response))
  }
  return response.json() as Promise<T>
}

async function responseErrorMessage(response: Response) {
  const fallback = `backend 请求失败：${response.status} ${response.statusText}`
  try {
    const payload = (await response.json()) as { detail?: unknown }
    if (typeof payload.detail === 'string') {
      return payload.detail
    }
    if (payload.detail) {
      return JSON.stringify(payload.detail)
    }
  } catch {
    return fallback
  }
  return fallback
}

const terminalStatuses = new Set<RunOutputStatus>(['completed', 'failed', 'cancelled'])

const httpClient: BattlePlannerClient = {
  listPlans: () => requestJson<TaskPlan[]>('/battle-planner/plans'),
  getPlan: (planId) => requestJson<TaskPlan>(`/battle-planner/plans/${encodeURIComponent(planId)}`),
  createContext: (request) =>
    requestJson<TaskContext>('/battle-planner/contexts', {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  listContexts: () => requestJson<TaskContextListItemView[]>('/battle-planner/contexts'),
  getContext: (contextId) =>
    requestJson<TaskContext>(`/battle-planner/contexts/${encodeURIComponent(contextId)}`),
  createRun: (request) =>
    requestJson<RunOutput>('/battle-planner/runs', {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  listRuns: () => requestJson<TaskRunListItemView[]>('/battle-planner/runs'),
  getRun: (runId) => requestJson<RunOutput>(`/battle-planner/runs/${encodeURIComponent(runId)}`),
  watchRun: (runId, handlers) => watchHttpRun(runId, handlers),
}

function watchHttpRun(runId: string, handlers: RunWatchHandlers): RunWatchUnsubscribe {
  let stopped = false
  let eventSource: EventSource | null = null
  let pollTimer: number | undefined

  async function fetchRun(event?: RunWatchEvent) {
    if (stopped) {
      return
    }
    try {
      const run = await httpClient.getRun(runId)
      if (stopped) {
        return
      }
      handlers.onUpdate(run, event)
      if (terminalStatuses.has(run.status)) {
        stop()
      }
    } catch (error) {
      if (!stopped) {
        handlers.onError?.(error instanceof Error ? error : new Error('run 刷新失败'))
      }
    }
  }

  function stopPolling() {
    if (pollTimer !== undefined) {
      window.clearInterval(pollTimer)
      pollTimer = undefined
    }
  }

  function startPolling() {
    if (pollTimer !== undefined || stopped) {
      return
    }
    pollTimer = window.setInterval(() => {
      void fetchRun({ type: 'poll', run_id: runId })
    }, battlePlannerApiConfig.pollIntervalMs)
  }

  function closeEventSource() {
    eventSource?.close()
    eventSource = null
  }

  function stop() {
    stopped = true
    closeEventSource()
    stopPolling()
  }

  try {
    eventSource = new EventSource(
      buildApiUrl(`/battle-planner/runs/${encodeURIComponent(runId)}/events`),
    )
    const handleEvent = (event: MessageEvent<string>) => {
      void fetchRun(parseRunWatchEvent(event, runId))
    }
    eventSource.addEventListener('iteration_ready', handleEvent)
    eventSource.addEventListener('run_completed', handleEvent)
    eventSource.addEventListener('run_failed', handleEvent)
    eventSource.addEventListener('run_cancelled', handleEvent)
    eventSource.onerror = () => {
      closeEventSource()
      startPolling()
    }
  } catch (error) {
    handlers.onError?.(error instanceof Error ? error : new Error('run 监听失败'))
    startPolling()
  }

  return stop
}

function parseRunWatchEvent(event: MessageEvent<string>, runId: string): RunWatchEvent {
  try {
    return JSON.parse(event.data) as RunWatchEvent
  } catch {
    return { type: event.type, run_id: runId }
  }
}

export const battlePlannerClient: BattlePlannerClient =
  battlePlannerApiConfig.mode === 'online' ? httpClient : mockClient
