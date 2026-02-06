import { debugLogger } from './debugLogger'
import { getLatestLogs } from '@/api/logs'

class LogStreamClient {
    private ws: WebSocket | null = null
    private reconnectInterval = 3000
    private maxRetries = 100
    private retries = 0
    private url: string
    private fallbackUrl: string

    constructor() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        // Default to current host
        this.url = `${protocol}//${window.location.host}/ws/logs`
        this.fallbackUrl = ''

        // Special handling for Vite dev server (usually on 5173) connecting to backend on 11451
        if (window.location.host.includes('localhost') || window.location.host.includes('127.0.0.1')) {
             this.url = 'ws://127.0.0.1:11451/ws/logs'
             this.fallbackUrl = 'ws://localhost:11451/ws/logs'
        }
    }

    connect(useFallback = false) {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            return
        }

        const targetUrl = useFallback && this.fallbackUrl ? this.fallbackUrl : this.url
        console.log(`[LogStream] Connecting to ${targetUrl}...`)
        
        try {
            this.ws = new WebSocket(targetUrl)
        } catch (e) {
            console.error('[LogStream] Connection creation failed', e)
            this.scheduleReconnect()
            return
        }

        this.ws.onopen = async () => {
            console.log(`[LogStream] Connected to ${targetUrl}`)
            debugLogger.addLog('frontend', `[LogStream] Connected to backend logs at ${targetUrl}`, 'info')
            this.retries = 0
            
            // Fetch initial logs upon connection to show history
            try {
                const res = await getLatestLogs(50)
                if (res.logs && Array.isArray(res.logs)) {
                        res.logs.forEach(line => {
                            let level: any = 'info'
                            if (line.includes('ERROR') || line.includes('CRITICAL')) level = 'error'
                            else if (line.includes('WARN')) level = 'warn'
                            
                            debugLogger.addLog('backend', line.trim(), level)
                        })
                }
            } catch (e) {
                console.error('[LogStream] Failed to fetch initial logs', e)
            }
        }

        this.ws.onmessage = async (event) => {
            if (event.data === "LOG_UPDATE" || (typeof event.data === 'string' && event.data.includes("LOG_UPDATE"))) {
                try {
                    const res = await getLatestLogs(50)
                    if (res.logs && Array.isArray(res.logs)) {
                         res.logs.forEach(line => {
                             // Try to detect level from log line
                             let level: any = 'info'
                             if (line.includes('ERROR') || line.includes('CRITICAL')) level = 'error'
                             else if (line.includes('WARN')) level = 'warn'
                             
                             debugLogger.addLog('backend', line.trim(), level)
                         })
                    }
                } catch (e) {
                    console.error('[LogStream] Failed to fetch logs', e)
                }
            } else {
                debugLogger.addLog('backend', event.data, 'info')
            }
        }

        this.ws.onclose = () => {
            console.log('[LogStream] Disconnected')
            this.scheduleReconnect()
        }

        this.ws.onerror = (error) => {
            console.error('[LogStream] Error', error)
            // If first attempt failed and we have a fallback, try that immediately
            if (!useFallback && this.fallbackUrl && this.retries === 0) {
                console.log('[LogStream] Retrying with fallback URL...')
                this.ws?.close()
                this.ws = null
                this.connect(true)
            }
        }
    }

    private scheduleReconnect() {
        if (this.retries < this.maxRetries) {
            setTimeout(() => {
                this.retries++
                this.connect()
            }, this.reconnectInterval)
        }
    }
}

export const logStream = new LogStreamClient()
