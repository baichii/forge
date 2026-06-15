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
import type {
  RunOutput,
  TaskContext,
  TaskContextCreateRequest,
  TaskContextListItemView,
  TaskPlan,
  TaskRunCreateRequest,
  TaskRunListItemView,
} from './types'

export type BattlePlannerClient = {
  listPlans: () => Promise<TaskPlan[]>
  getPlan: (planId: string) => Promise<TaskPlan>
  createContext: (request: TaskContextCreateRequest) => Promise<TaskContext>
  listContexts: () => Promise<TaskContextListItemView[]>
  getContext: (contextId: string) => Promise<TaskContext>
  createRun: (request: TaskRunCreateRequest) => Promise<RunOutput>
  listRuns: () => Promise<TaskRunListItemView[]>
  getRun: (runId: string) => Promise<RunOutput>
}

export const battlePlannerClient: BattlePlannerClient = {
  listPlans: listMockPlans,
  getPlan: getMockPlan,
  createContext: createMockContext,
  listContexts: listMockContexts,
  getContext: getMockContext,
  createRun: createMockRun,
  listRuns: listMockRuns,
  getRun: getMockRun,
}
