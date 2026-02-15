import { reactive } from 'vue'

export type LogType = 'frontend' | 'backend'
export type LogLevel = 'info' | 'warn' | 'error' | 'debug'

export interface DebugLog {
  id: number
  type: LogType
  level: LogLevel
  message: string
  stack?: string
  timestamp: number
  meta?: any
  args?: any[]
}

class DebugLogger {
  state = reactive({
    logs: [] as DebugLog[],
    isVisible: false
  })

  private nextId = 1
  private maxLogs = 2000
  private originalConsole: any = {}

  constructor() {
    this.originalConsole = {
      log: console.log,
      info: console.info,
      warn: console.warn,
      error: console.error,
      debug: console.debug
    }
  }

  addLog(type: LogType, message: string, level: LogLevel = 'info', stack?: string, meta?: any, args?: any[]) {
    const log: DebugLog = {
      id: this.nextId++,
      type,
      level,
      message,
      stack,
      timestamp: Date.now(),
      meta,
      args
    }
    
    this.state.logs.push(log)
    
    if (this.state.logs.length > this.maxLogs) {
      this.state.logs.shift()
    }
  }

  clear() {
    this.state.logs = []
  }

  toggle(visible?: boolean) {
    this.state.isVisible = visible ?? !this.state.isVisible
  }

  interceptConsole() {
    const methods: LogLevel[] = ['log', 'info', 'warn', 'error', 'debug'] as any

    methods.forEach((method) => {
      // @ts-ignore
      console[method] = (...args: any[]) => {
        // @ts-ignore
        this.originalConsole[method].apply(console, args)

        // Map console method to LogLevel
        const level: LogLevel = (String(method) === 'log' ? 'info' : method) as any

        const message = args.map(arg => {
          if (typeof arg === 'object') {
             try {
               return JSON.stringify(arg)
             } catch (e) {
               return '[Circular/Object]'
             }
          }
          return String(arg)
        }).join(' ')

        this.addLog('frontend', message, level, undefined, undefined, args)
      }
    })
  }
}

export const debugLogger = new DebugLogger()
