import request from '@/utils/request'

interface GenerateParams {
  projectId: number;
  episodeId: number;
  prompt: string;
  type?: string;
  skill?: string;
  data?: any;
}

interface StreamCallbacks {
  onMessage: (data: any) => void;
  onError?: (error: any) => void;
  onFinish?: () => void;
}

// --- Auth ---
export const authApi = {
  login: (data: any) => request.post('/login/access-token', data, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  }),
  register: (data: any) => request.post('/login/register', data),
  logout: () => {
    localStorage.removeItem('token')
    window.location.reload()
  }
}

export const aiApi = {
    testConnection: (apiKeyId: number) => request.post('/ai/test-connection', { api_key_id: apiKeyId }),
    updateScriptItem: (data: { episode_id: number, item_id: string, updates: any }) => request.post('/ai/script/update_item', data),
    deleteScriptItem: (data: { episode_id: number, item_id: string }) => request.post('/ai/script/delete_item', data),
    skillsStream: async (data: GenerateParams, callbacks: StreamCallbacks, signal?: AbortSignal) => {
      const { onMessage, onError, onFinish } = callbacks;
  
      try {
        const response = await fetch(`${request.getUri()}/ai/generate`, { 
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            project_id: data.projectId,
            episode_id: data.episodeId,
            prompt: data.prompt,
            type: data.type || 'text',
            skill: data.skill || 'short-video-screenwriter',
            data: data.data || {}
          }),
          signal
        });
  
        if (!response.ok) {
          const errText = await response.text();
          throw new Error(`HTTP Error ${response.status}: ${errText}`);
        }
        
        if (!response.body) {
          throw new Error('Response body is empty');
        }
  
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
  
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) break;
  
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || ''; 
  
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const jsonStr = line.slice(6).trim();
              if (!jsonStr || jsonStr === '[DONE]') continue;
              
              try {
                const parsedData = JSON.parse(jsonStr);
                onMessage(parsedData); 
              } catch (e) {
                console.error('SSE JSON Parse Error:', e);
              }
            }
          }
        }
        if (onFinish) onFinish();
  
      } catch (error: any) {
        if (error.name === 'AbortError') {
           console.log('Fetch aborted');
           // Propagate abort as a specific error or handle silently?
           // The caller might want to know.
           if (onError) onError(new Error('User Terminated'));
           return;
        }
        console.error('Stream Fetch Error:', error);
        if (onError) onError(error);
      }
    }
}

// --- Tags ---
export const tagApi = {
  // 获取标签库
  list: (params: { projectId?: number; episodeId?: number }) => {
    return request.get('/tags/', { params })
  },
  // 创建标签
  create: (data: { category: string; content: string; type: number; ref_id: number, data: any }) => {
    return request.post('/tags/', data)
  }
}

// --- Projects ---
export const projectApi = {
  list: (params?: any) => request.get('/projects/', { params }),
  create: (data: { name: string; description?: string }) => request.post('/projects/', data),
  get: (id: number) => request.get(`/projects/${id}`),
  update: (id: number, data: any) => request.put(`/projects/${id}`, data),
  delete: (id: number) => request.delete(`/projects/${id}`),
  getAssets: (id: number) => request.get(`/projects/${id}/assets`)
}

// --- Episodes ---
// 假设后端已有对应路由，若无请按 Project 逻辑补充
export const episodeApi = {
  list: (projectId: number) => request.get(`/projects/${projectId}/episodes`),
  create: (projectId: number, data: { title: string }) => request.post(`/projects/${projectId}/episodes`, data),
  update: (projectId: number, episodeId: number, data: { title: string }) => 
    request.put(`/projects/${projectId}/episodes/${episodeId}`, data),
  delete: (projectId: number, episodeId: number) => request.delete(`/projects/${projectId}/episodes/${episodeId}`),
  exportAssets: (projectId: number, episodeId: number, onProgress?: (progress: number) => void) => 
    request.get(`/projects/${projectId}/episodes/${episodeId}/export/assets`, { 
        responseType: 'blob',
        onDownloadProgress: (progressEvent) => {
            if (onProgress && progressEvent.total) {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                onProgress(percentCompleted);
            }
        }
    }),
  exportVideo: (projectId: number, episodeId: number, onProgress?: (progress: number) => void) => 
    request.get(`/projects/${projectId}/episodes/${episodeId}/export/video`, { 
        responseType: 'blob',
        onDownloadProgress: (progressEvent) => {
             if (onProgress && progressEvent.total) {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                onProgress(percentCompleted);
            }
        }
    }),
  exportStoryboardData: (projectId: number, episodeId: number) => 
    request.get(`/projects/${projectId}/episodes/${episodeId}/export/storyboard_data`, { 
        responseType: 'blob'
    })
}


// --- API Keys (对应后端的 ApiKey 模型) ---
export const apiKeyApi = {
  list: () => request.get('/apikeys/'), 
  create: (data: any) => request.post('/apikeys/', data),
  update: (id: number, data: any) => request.put(`/apikeys/${id}`, data),
  delete: (id: number) => request.delete(`/apikeys/${id}`)
}

// --- User ---
export const userApi = {
  getMe: () => request.get('/users/me'),
  completeOnboarding: () => request.post('/users/me/onboarding'),
  changePassword: (data: any) => request.post('/users/change-password', data)
}

// --- Prompt ---
export const promptApi = {
    list: (params?: any) => request.get('/prompts/', { params }),
    create: (data: any) => request.post('/prompts/', data),
    delete: (id: number) => request.delete(`/prompts/${id}`)
  }

// --- Style Templates ---
export const styleApi = {
  list: (params?: any) => request.get('/styles/', { params }),
  create: (data: FormData) => request.post('/styles/', data, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  update: (id: number, data: FormData) => request.put(`/styles/${id}`, data, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  delete: (id: number) => request.delete(`/styles/${id}`)
}
