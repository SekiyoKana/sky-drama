import request from '@/utils/request'

export interface LogResponse {
  logs: string[]
}

export interface DirectorRunSummary {
  run_id: string
  status: string
  started_at: string
  updated_at: string
  ended_at?: string
  duration_ms?: number
  context: {
    project_id?: number
    episode_id?: number
    user_id?: number
    type?: string
    skill?: string
    prompt_preview?: string
  }
  metrics: Record<string, number>
}

export interface DirectorRunsResponse {
  runs: DirectorRunSummary[]
}

export interface DirectorRunDetail {
  run_id: string
  status: string
  started_at: string
  updated_at: string
  ended_at?: string
  duration_ms?: number
  context: Record<string, any>
  metrics: Record<string, number>
  result?: Record<string, any>
  events: Array<{ ts: string; type: string; payload: any }>
}

export function getLatestLogs(limit: number = 100) {
  return request.get<any, LogResponse>('/logs/latest', {
    params: { limit }
  })
}

export function getDirectorRuns(params?: {
  limit?: number
  project_id?: number
  episode_id?: number
}) {
  return request.get<any, DirectorRunsResponse>('/logs/director-runs', {
    params
  })
}

export function getDirectorRunDetail(runId: string) {
  return request.get<any, DirectorRunDetail>(`/logs/director-runs/${runId}`)
}
