import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import router from './router' // 引入配置好的路由

import { debugLogger } from '@/utils/debugLogger'

const app = createApp(App)

// Initialize Console Interceptor
debugLogger.interceptConsole()

app.config.errorHandler = (err: any, _instance, info) => {
  debugLogger.addLog('frontend', err?.message || 'Unknown Vue Error', 'error', err?.stack, { info })
  // console.error(err) // No need to double log, interceptor catches console.error if used, but this is Vue handler
}

window.onerror = (message, source, lineno, colno, error) => {
  debugLogger.addLog('frontend', String(message), 'error', error?.stack, { source, lineno, colno })
}

window.onunhandledrejection = (event) => {
  debugLogger.addLog('frontend', `Unhandled Promise Rejection: ${event.reason}`, 'error', undefined, { reason: event.reason })
}

app.use(createPinia())
app.use(router)

app.mount('#app')