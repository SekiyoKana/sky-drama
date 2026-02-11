import axios from 'axios'
import router from '@/router' // 👈 引入路由
import { useAuthStore } from '@/stores/auth' // 👈 引入 Auth Store

import { debugLogger } from '@/utils/debugLogger'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/v1',
  timeout: 5000000
})

// Check for Tauri environment and adjust base URL if necessary
// @ts-ignore
if (typeof window !== 'undefined' && window.__TAURI_INTERNALS__ !== undefined) {
    service.defaults.baseURL = 'http://127.0.0.1:11451/v1';
}

service.interceptors.request.use(
  (config) => {
    const store = useAuthStore()
    if (store.token) {
      config.headers['Authorization'] = `Bearer ${store.token}`
    }
    
    if (!store.token && config.url && !config.url.includes('/login') && !config.url.includes('/register') && !config.url.includes('/access-token')) {
        store.logout()
        
        if (router.currentRoute.value.path !== '/login') {
            const controller = new AbortController()
            config.signal = controller.signal
            controller.abort()
            
            router.push(`/login?redirect=${router.currentRoute.value.fullPath}`)
            return Promise.reject(new Error('No token found, redirecting to login'))
        }
    }

    if (config.url && !config.url.includes('/logs/latest')) {
        const fullUrl = config.baseURL ? `${config.baseURL}${config.url}` : config.url
        debugLogger.addLog('frontend', `➡️ [Request] ${config.method?.toUpperCase()} ${config.url}`, 'info', undefined, {
            fullUrl,
            params: config.params,
            data: config.data,
            headers: config.headers
        })
    }
    
    return config
  },
  (error) => {
    debugLogger.addLog('frontend', `❌ [Request Error] ${error.message}`, 'error')
    return Promise.reject(error)
  }
)

import { resolveImageUrl } from '@/utils/assets'

// 递归遍历对象，处理图片和视频 URL
const transformUrls = (data: any): any => {
  if (!data) return data
  
  if (Array.isArray(data)) {
    return data.map(item => transformUrls(item))
  }
  
  if (typeof data === 'object') {
    const newData: any = { ...data }
    for (const key in newData) {
      // 兼容 image/video/src/previewUrl/reference_image 字段的资源地址
      if (['image_url', 'video_url', 'src', 'previewUrl', 'reference_image'].includes(key)) {
        if (typeof newData[key] === 'string') {
          newData[key] = resolveImageUrl(newData[key])
        }
      } else {
        newData[key] = transformUrls(newData[key])
      }
    }
    return newData
  }
  
  return data
}

service.interceptors.response.use(
  (response) => {
    if (response.config.responseType === 'blob' || response.data instanceof Blob) {
      return response.data
    }

    // 自动处理返回数据中的 URL
    if (response.data) {
      response.data = transformUrls(response.data)
    }

    if (response.config && response.config.url && !response.config.url.includes('/logs/latest')) {
       debugLogger.addLog('frontend', `⬅️ [Response] ${response.status} ${response.config.url}`, 'info', undefined, {
           data: response.data,
           headers: response.headers
       })
    }

    return response.data
  },
  (error) => {
    debugLogger.addLog('backend', error.message, 'error', error.stack, {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      data: error.response?.data
    })

    // 1. 检测 401 状态码
    if (error.response && error.response.status === 401) {
      const store = useAuthStore()
      
      // 2. 执行登出清理 (清空 token, user 等状态)
      store.logout()
      
      // 3. 强制跳转登录页 (带上 redirect 参数，方便登录后跳回原页面)
      // 避免在登录页重复跳转
      if (router.currentRoute.value.path !== '/login') {
        router.push(`/login?redirect=${router.currentRoute.value.fullPath}`)
      }
    }
    
    return Promise.reject(error)
  }
)

export default service
