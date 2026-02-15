<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { debugLogger } from '@/utils/debugLogger'
import { getLatestLogs } from '@/api/logs'
import { X, Trash2, Activity, Terminal, Monitor, Server, ArrowDown } from 'lucide-vue-next'

import { useMessage } from '@/utils/useMessage'

const activeTab = ref<'all' | 'frontend' | 'backend'>('frontend')
const logContainer = ref<HTMLElement | null>(null)
const message = useMessage()
// const expandedLogs = ref<Set<number>>(new Set())

const windowState = reactive({
  x: window.innerWidth / 2 - 400,
  y: window.innerHeight / 2 - 300,
  w: 800,
  h: 600
})

const filteredLogs = computed(() => {
  if (activeTab.value === 'all') return debugLogger.state.logs
  return debugLogger.state.logs.filter(log => log.type === activeTab.value)
})

const count = ref(0)
const lastKeyTime = ref(0)

// const checkTauri = () => {
//   return typeof window !== 'undefined' && (window as any).__TAURI_INTERNALS__ !== undefined
// }

const handleKeydown = (e: KeyboardEvent) => {
  if (e.repeat) return

  if (e.key === 'Control') {
    const now = Date.now()
    if (now - lastKeyTime.value > 1000) {
      count.value = 0
    }
    
    count.value++
    lastKeyTime.value = now
    
    if (count.value >= 5) {
      debugLogger.toggle(true)
      count.value = 0
    }
  }
}

// Drag logic
let isDragging = false
let dragOffset = { x: 0, y: 0 }

const startDrag = (e: MouseEvent) => {
  isDragging = true
  dragOffset.x = e.clientX - windowState.x
  dragOffset.y = e.clientY - windowState.y
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.body.style.userSelect = 'none'
}

const onDrag = (e: MouseEvent) => {
  if (!isDragging) return
  const maxX = window.innerWidth - windowState.w
  const maxY = window.innerHeight - windowState.h
  windowState.x = Math.max(0, Math.min(e.clientX - dragOffset.x, maxX))
  windowState.y = Math.max(0, Math.min(e.clientY - dragOffset.y, maxY))
}

const stopDrag = () => {
  isDragging = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.body.style.userSelect = ''
}

// Resize logic
let isResizing = false

const startResize = (e: MouseEvent) => {
  isResizing = true
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
  e.stopPropagation()
}

const onResize = (e: MouseEvent) => {
  if (!isResizing) return
  const newW = Math.max(400, e.clientX - windowState.x)
  const newH = Math.max(300, e.clientY - windowState.y)
  windowState.w = Math.min(newW, window.innerWidth - windowState.x)
  windowState.h = Math.min(newH, window.innerHeight - windowState.y)
}

const stopResize = () => {
  isResizing = false
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
}

// const formatTime = (ts: number) => {
//   const d = new Date(ts)
//   const pad = (n: number) => n.toString().padStart(2, '0')
//   return `【${d.getFullYear()}/${pad(d.getMonth() + 1)}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}.${d.getMilliseconds().toString().padStart(3, '0')}】`
// }

// Auto scroll
const userScrolled = ref(false)

const handleScroll = () => {
  if (!logContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = logContainer.value
  // If user is within 50px of bottom, they are "at bottom"
  const atBottom = scrollHeight - scrollTop - clientHeight < 50
  userScrolled.value = !atBottom
}

const scrollToBottom = () => {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
    userScrolled.value = false
  }
}

watch(() => filteredLogs.value.length, () => {
  nextTick(() => {
    if (logContainer.value && !userScrolled.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
})

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

let pollInterval: any = null

const isConnected = ref(true)

const fetchLogs = async () => {
  try {
    const res = await getLatestLogs(50)
    
    if (!isConnected.value) {
        isConnected.value = true
        message.success('重新连接')
    }

    if (res.logs && Array.isArray(res.logs)) {
      res.logs.forEach(line => {
        // Try to detect level from log line
        let level: any = 'info'
        if (line.includes('ERROR') || line.includes('CRITICAL')) level = 'error'
        else if (line.includes('WARN')) level = 'warn'
        
        // Avoid adding duplicate logs if possible, but for now simple append is okay 
        // as debugLogger handles circular buffer. 
        // Ideally we'd have a mechanism to only add NEW lines (e.g. by tracking last seen timestamp/id)
        // But since this is a simple debug tool, simple polling is acceptable.
        // Actually, polling will fetch overlapping logs. 
        // To fix this simply, we could clear backend logs before adding new ones? 
        // Or better: Let's just trust the user to clear if it gets too noisy, or add a simple de-dupe.
        
        // Simple de-dupe check against last few logs
        const lastLog = debugLogger.state.logs[debugLogger.state.logs.length - 1]
        if (lastLog && lastLog.type === 'backend' && lastLog.message === line.trim()) return

        // Filter out /v1/logs/latest polling logs to avoid recursion noise
        if (line.includes('/v1/logs/latest')) return

        debugLogger.addLog('backend', line.trim(), level)
      })
    }
  } catch (e) {
    if (isConnected.value) {
        isConnected.value = false
        message.error('与本地服务器连接断开')
    }
    // console.error('[GlobalDebug] Failed to fetch logs', e)
  }
}

watch(() => debugLogger.state.isVisible, (visible) => {
  if (visible) {
    fetchLogs() // Fetch immediately
    if (!pollInterval) {
      pollInterval = setInterval(fetchLogs, 5000)
    }
  } else {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
  }
}, { immediate: true })

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
  window.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
})

// Helper to determine text color class based on log level or content
const getLogClass = (log: any) => {
  if (log.type === 'backend') {
    // Attempt to parse python log levels
    if (log.message.includes('ERROR') || log.message.includes('CRITICAL')) return 'text-red-600 font-medium'
    if (log.message.includes('WARNING') || log.message.includes('WARN')) return 'text-yellow-600 font-medium'
    if (log.message.includes('DEBUG')) return 'text-gray-500'
    return 'text-green-700' // Default Info
  }
  
  // Frontend
  switch (log.level) {
    case 'error': return 'text-red-600 bg-red-100/50'
    case 'warn': return 'text-yellow-600 bg-yellow-100/50'
    case 'debug': return 'text-gray-500'
    default: return 'text-gray-700'
  }
}

// Highlight HTTP methods in backend logs
const formatLogMessage = (log: any) => {
  if (log.type !== 'backend' || typeof log.message !== 'string') return log.message
  
  // Basic HTML escaping
  let safeMsg = log.message
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")

  // Highlight HTTP methods
  safeMsg = safeMsg.replace(/(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)(?=\s)/g, (match: string) => {
    let colorClass = 'text-gray-500'
    switch (match) {
      case 'GET': colorClass = 'text-green-600 font-bold'; break;
      case 'POST': colorClass = 'text-blue-600 font-bold'; break;
      case 'PUT': colorClass = 'text-orange-600 font-bold'; break;
      case 'DELETE': colorClass = 'text-red-600 font-bold'; break;
      case 'PATCH': colorClass = 'text-purple-600 font-bold'; break;
    }
    return `<span class="${colorClass}">${match}</span>`
  })

  return safeMsg
}
</script>

<template>
  <div 
    v-if="debugLogger.state.isVisible" 
    class="fixed z-[9999] bg-[#E0E5EC] rounded-2xl flex flex-col overflow-hidden font-mono text-xs text-gray-700 shadow-2xl border border-white/40"
    :style="{ 
      left: windowState.x + 'px', 
      top: windowState.y + 'px', 
      width: windowState.w + 'px', 
      height: windowState.h + 'px' 
    }"
  >
    <!-- Header -->
    <div 
      class="flex items-center justify-between px-4 py-3 bg-[#E0E5EC] border-b border-gray-300/50 cursor-move select-none shrink-0 z-10"
      @mousedown="startDrag"
    >
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2 text-gray-500">
          <Terminal class="w-4 h-4 text-gray-600" />
          <span class="font-bold tracking-wide text-xs text-gray-600">调试控制台</span>
        </div>
        
        <!-- Tabs -->
        <div class="flex gap-3">
          <button 
            @click="activeTab = 'frontend'"
            class="px-3 py-1.5 rounded-xl text-[10px] font-bold transition-all flex items-center gap-1.5"
            :class="activeTab === 'frontend' ? 'bg-purple-100 text-purple-600 shadow-sm' : 'bg-transparent text-gray-500 hover:bg-gray-100'"
          >
            <Monitor class="w-3 h-3" /> 前端
          </button>
          <button 
            @click="activeTab = 'backend'"
            class="px-3 py-1.5 rounded-xl text-[10px] font-bold transition-all flex items-center gap-1.5"
            :class="activeTab === 'backend' ? 'bg-green-100 text-green-600 shadow-sm' : 'bg-transparent text-gray-500 hover:bg-gray-100'"
          >
            <Server class="w-3 h-3" /> 后端
          </button>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button 
          @click="debugLogger.clear()" 
          class="p-2 rounded-full text-gray-500 hover:bg-white hover:text-blue-500 transition-colors"
          title="清空控制台"
          @mousedown.stop
        >
          <Trash2 class="w-3.5 h-3.5" />
        </button>
        <button 
          @click="debugLogger.toggle(false)" 
          class="p-2 rounded-full text-gray-500 hover:bg-white hover:text-red-500 transition-colors"
          @mousedown.stop
        >
          <X class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <!-- Log Area -->
    <div 
      class="flex-1 relative overflow-hidden bg-[#E0E5EC]"
    >
      <div 
        ref="logContainer"
        class="absolute inset-4 overflow-y-auto p-4 custom-scroll space-y-4 rounded-xl shadow-[inset_3px_3px_6px_#b8b9be,inset_-3px_-3px_6px_#ffffff] bg-[#E0E5EC]"
        @scroll="handleScroll"
      >
        <div v-if="filteredLogs.length === 0" class="h-full flex flex-col items-center justify-center text-gray-400 gap-3 opacity-60">
          <Activity class="w-8 h-8" />
          <span class="italic text-xs font-bold tracking-wider">暂无日志</span>
        </div>

        <div 
          v-for="log in filteredLogs" 
          :key="log.id" 
          class="group flex items-start gap-3 hover:bg-white/40 px-2 py-1.5 rounded-lg leading-relaxed break-all transition-colors border border-transparent hover:border-white/50"
        >
          <!-- Timestamp & Type -->
          <!-- <div class="flex shrink-0 items-center gap-2 select-none opacity-60 group-hover:opacity-100 transition-opacity">
            <span class="text-[9px] text-blue-600 font-mono font-bold tracking-tight bg-blue-100/80 px-1.5 py-0.5 rounded shadow-sm">{{ formatTime(log.timestamp) }}</span>
            <span 
              class="text-[9px] w-6 text-center font-bold uppercase rounded-xs"
              :class="log.type === 'frontend' ? 'text-purple-600' : 'text-green-600'"
            >
              {{ log.type === 'frontend' ? 'FE' : 'BE' }}
            </span>
          </div> -->

          <!-- Log Content -->
          <div class="flex-1 min-w-0 font-mono text-[13px]" :class="getLogClass(log)">
            
            <!-- Backend: Raw Text -->
            <template v-if="log.type === 'backend'">
              <span class="whitespace-pre-wrap" v-html="formatLogMessage(log)"></span>
            </template>

            <!-- Frontend: Console Mimic -->
            <template v-else>
               <div class="flex flex-col gap-1 items-start w-full">
                 <div class="font-medium">{{ log.message }}</div>
                 
                 <!-- Meta Data (Request Details) -->
                 <div v-if="log.meta" class="w-full">
                    <details class="group/meta">
                      <summary class="cursor-pointer hover:bg-black/5 rounded px-1.5 text-blue-600 list-none flex items-center gap-1 font-bold transition-colors text-[10px] w-fit">
                        <span class="group-open/meta:rotate-90 transition-transform text-[8px]">▶</span> 
                        <span>Details</span>
                      </summary>
                      <pre class="mt-1 ml-2 text-[10px] text-gray-600 border-l-2 border-blue-200 pl-3 select-text overflow-x-auto bg-blue-50/30 p-2 rounded">{{ JSON.stringify(log.meta, null, 2) }}</pre>
                    </details>
                 </div>

                 <!-- Console Args -->
                 <div v-if="log.args && log.args.length" class="flex flex-wrap gap-1.5">
                    <div v-for="(arg, idx) in log.args" :key="idx">
                        <!-- String/Number -->
                        <span v-if="typeof arg !== 'object' || arg === null">{{ String(arg) }}</span>
                        
                        <!-- Object/Array: Use Details/Summary for native expansion -->
                        <details v-else class="inline-block align-top">
                          <summary class="cursor-pointer hover:bg-black/5 rounded px-1.5 text-blue-600 list-none flex items-center gap-1 font-bold transition-colors">
                            <span>▶</span> 
                            <span>{{ Array.isArray(arg) ? `Array(${arg.length})` : 'Object' }}</span>
                          </summary>
                          <pre class="mt-1.5 ml-2 text-[10px] text-gray-600 border-l-2 border-gray-300 pl-3 select-text overflow-x-auto bg-gray-50/50 p-2 rounded">{{ JSON.stringify(arg, null, 2) }}</pre>
                        </details>
                    </div>
                 </div>
                 
                 <!-- Fallback to message if no args and no meta (already shown above, but just in case) -->
                 <!-- <span v-else>{{ log.message }}</span> -->

                 <!-- Stack Trace (only if error/warn) -->
                 <details v-if="log.stack" class="w-full mt-1.5">
                    <summary class="text-gray-400 cursor-pointer text-[10px] hover:text-gray-600 list-none font-medium">
                       at (Stack Trace)
                    </summary>
                    <pre class="text-[9px] text-red-500 ml-4 mt-1 overflow-x-auto bg-red-50 p-2 rounded border border-red-100">{{ log.stack }}</pre>
                 </details>
               </div>
            </template>

          </div>
        </div>
      </div>
    </div>

    <!-- Resize Handle -->
    <div 
      class="absolute bottom-0 right-0 w-6 h-6 cursor-nwse-resize flex items-end justify-end p-1 text-gray-400 hover:text-gray-600 z-20"
      @mousedown="startResize"
    >
      <svg viewBox="0 0 24 24" class="w-full h-full fill-current opacity-50"><path d="M22 22H20V20H22V22ZM22 18H20V16H22V18ZM18 22H16V20H18V22ZM18 18H16V16H18V18Z" /></svg>
    </div>

    <!-- Scroll to Bottom Button -->
    <button 
      v-if="userScrolled"
      @click="scrollToBottom"
      class="absolute bottom-6 right-6 p-2.5 bg-white text-blue-500 rounded-full shadow-lg hover:text-blue-600 hover:-translate-y-0.5 transition-all z-30 border border-gray-100"
      title="滚动到底部"
    >
      <ArrowDown class="w-4 h-4" />
    </button>
  </div>
</template>

<style scoped>
.custom-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
.custom-scroll::-webkit-scrollbar-track { background: transparent; }
.custom-scroll::-webkit-scrollbar-thumb { background-color: #cbd5e0; border-radius: 10px; border: 2px solid #E0E5EC; }
.custom-scroll::-webkit-scrollbar-thumb:hover { background-color: #a0aec0; }

/* Hide default detail marker and use custom */
details > summary { list-style: none; }
details > summary::-webkit-details-marker { display: none; }
details[open] > summary > span:first-child { transform: rotate(90deg); display: inline-block; }
</style>
