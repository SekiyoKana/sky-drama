import request from '@/utils/request'

export interface LogResponse {
  logs: string[]
}

export function getLatestLogs(limit: number = 100) {
  return request.get<any, LogResponse>('/logs/latest', {
    params: { limit }
  })
}