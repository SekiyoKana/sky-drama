<script setup lang="ts">
import { ref, reactive, watch, nextTick, onUnmounted, computed } from 'vue'
import { X, Terminal, Clock, CheckCircle2, AlertCircle, ChevronRight, ChevronDown, Activity, ListTodo, FileJson, Layers, User, Image, Film, MapPin, Sparkles, Loader2 } from 'lucide-vue-next'

const props = defineProps<{
  visible: boolean
  logs: any[]
}>()

const emit = defineEmits(['close'])
const logContainer = ref<HTMLElement | null>(null)
const consoleRef = ref<HTMLElement | null>(null)

// --- Log Processing Logic ---
const processedLogs = computed(() => {
  return props.logs.flatMap(log => {
      // 1. Handle "thought" type (streaming text)
      if (log.type === 'thought') {
          // If the thought looks like a JSON array start, try to parse it
          // OR if it contains our block tags
          const parts: any[] = []
          
          // Check for JSON Array structure (simple heuristic for Storyboard Maker)
          if (log.content.trim().startsWith('[') && log.content.trim().endsWith(']')) {
              try {
                  const parsed = JSON.parse(log.content)
                  if (Array.isArray(parsed)) {
                      // It's our new Storyboard Array!
                      parts.push({ type: 'block', tag: 'STORYBOARD_ARRAY', content: parsed })
                      return parts
                  }
              } catch (e) {
                  // Not valid JSON yet, treat as text
              }
          }

          const tagRegex = /<\|([A-Z_]+)\|>(.*?)<\|\1_END\|>/gs
          
          let lastIndex = 0
          let match
          
          while ((match = tagRegex.exec(log.content)) !== null) {
              if (match.index > lastIndex) {
                  const text = log.content.substring(lastIndex, match.index).trim()
                  if (text) parts.push({ type: 'thought', content: text })
              }
              
              parts.push({ type: 'block', tag: match[1], content: match[2] })
              
              lastIndex = tagRegex.lastIndex
          }
          
          const remaining = log.content.substring(lastIndex)
          if (remaining) {
              const openMatch = remaining.match(/<\|([A-Z_]+)\|>/)
              if (openMatch) {
                  if (openMatch.index! > 0) {
                      const preText = remaining.substring(0, openMatch.index!).trim()
                      if (preText) parts.push({ type: 'thought', content: preText })
                  }
                  
                  // Extract partial content after the tag
                  const partialContent = remaining.substring(openMatch.index! + openMatch[0].length)
                  parts.push({ type: 'loading_block', tag: openMatch[1], content: partialContent })
              } else {
                  parts.push({ type: 'thought', content: remaining })
              }
          }
          
          return parts
      }
      // 2. Handle "finish" type with specific JSON payload
      else if (log.type === 'finish' && log.payload?.json) {
           // Check if it's the storyboard array format
           try {
               const parsed = typeof log.payload.json === 'string' ? JSON.parse(log.payload.json) : log.payload.json
               if (Array.isArray(parsed)) {
                   return [{ type: 'block', tag: 'STORYBOARD_ARRAY', content: parsed }]
               }
           } catch(e) {}
      }
      
      return [log]
  })
})

// --- HTML Rendering Helper ---
const renderHtml = (text: string) => {
  if (!text) return ''
  return text.replace(/\n/g, '<br>')
}

// --- Data Parsing Helper ---
const parseBlockData = (str: string) => {
    try {
        let clean = str.replace(/```json\s*/g, '').replace(/```/g, '').trim()
        const parsed = JSON.parse(clean)
        return parsed
    } catch (e) {
        return null
    }
}

// Icon mapping for blocks
const getBlockIcon = (tag: string) => {
    switch(tag) {
        case 'META': return FileJson
        case 'OUTLINE': return ListTodo
        case 'CHARACTERS': return User
        case 'SCENES': return Image
        case 'STORYBOARD': return Film
        case 'PROMPT_REFINEMENT': return Sparkles
        case 'STORYBOARD_ARRAY': return Film // New Icon
        default: return Layers
    }
}

const getBlockColor = (tag: string) => {
    switch(tag) {
        case 'META': return 'text-orange-600 bg-orange-50 border-orange-200'
        case 'OUTLINE': return 'text-blue-600 bg-blue-50 border-blue-200'
        case 'CHARACTERS': return 'text-purple-600 bg-purple-50 border-purple-200'
        case 'SCENES': return 'text-green-600 bg-green-50 border-green-200'
        case 'STORYBOARD': return 'text-pink-600 bg-pink-50 border-pink-200'
        case 'PROMPT_REFINEMENT': return 'text-indigo-600 bg-indigo-50 border-indigo-200'
        case 'STORYBOARD_ARRAY': return 'text-pink-600 bg-pink-50 border-pink-200' // Same as Storyboard
        default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
}

const getBlockTitle = (tag: string) => {
    switch(tag) {
        case 'META': return '项目元数据'
        case 'OUTLINE': return '剧本大纲'
        case 'CHARACTERS': return '角色列表'
        case 'SCENES': return '场景列表'
        case 'STORYBOARD': return '分镜脚本'
        case 'PROMPT_REFINEMENT': return '提示词优化'
        case 'STORYBOARD_ARRAY': return 'AI 分镜生成结果' // New Title
        default: return tag
    }
}

// Translation helpers
const getOutlineLabel = (key: string) => {
    const map: Record<string, string> = {
        'setup': '铺垫',
        'confrontation': '冲突',
        'resolution': '结局'
    }
    return map[key.toLowerCase()] || key
}

// --- Window State ---
const windowState = reactive({
  x: window.innerWidth - 550,
  y: window.innerHeight - 650,
  w: 500,
  h: 600
})

// --- Drag & Resize ---
let isDragging = false
let dragOffset = { x: 0, y: 0 }

const startDrag = (e: MouseEvent) => {
  if (!consoleRef.value) return
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

// --- Resize ---
let isResizing = false
const startResize = (e: MouseEvent) => {
  isResizing = true
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
  e.stopPropagation()
}

const onResize = (e: MouseEvent) => {
  if (!isResizing) return
  const newW = Math.max(300, e.clientX - windowState.x)
  const newH = Math.max(200, e.clientY - windowState.y)
  windowState.w = Math.min(newW, window.innerWidth - windowState.x)
  windowState.h = Math.min(newH, window.innerHeight - windowState.y)
}

const stopResize = () => {
  isResizing = false
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
}

// --- Auto Scroll ---
watch(() => props.logs.length, () => {
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
})

watch(() => props.logs, () => {
    nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
}, { deep: true })

const expandedItems = ref<Set<number>>(new Set())
const toggleExpand = (index: number) => {
  if (expandedItems.value.has(index)) expandedItems.value.delete(index)
  else expandedItems.value.add(index)
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
})
</script>

<template>
  <transition name="pop">
    <div 
      v-if="visible" 
      ref="consoleRef"
      class="fixed z-[100] bg-[#E0E5EC] rounded-2xl flex flex-col overflow-hidden font-sans text-xs text-gray-600 shadow-2xl border border-white/40"
      :style="{ 
        left: windowState.x + 'px', 
        top: windowState.y + 'px', 
        width: windowState.w + 'px', 
        height: windowState.h + 'px' 
      }"
    >
      <div 
        class="flex items-center justify-between px-4 py-3 bg-[#E0E5EC] border-b border-gray-300/50 cursor-move select-none shrink-0 z-10"
        @mousedown="startDrag"
      >
        <div class="flex items-center gap-2 pointer-events-none text-gray-500">
          <Activity class="w-4 h-4 text-blue-500" />
          <span class="font-bold tracking-wide">AI 导演控制台</span>
        </div>
        <button 
          @click="emit('close')" 
          class="p-1.5 rounded-full neu-flat hover:text-red-500 active:neu-pressed transition-all text-gray-400"
          @mousedown.stop
        >
          <X class="w-3.5 h-3.5" />
        </button>
      </div>

      <div class="flex-1 flex flex-col min-h-0 bg-[#E0E5EC] relative">
        <div class="flex-1 relative overflow-hidden p-4">
          <div 
            ref="logContainer"
            class="absolute inset-4 rounded-xl shadow-[inset_3px_3px_6px_#b8b9be,inset_-3px_-3px_6px_#ffffff] overflow-y-auto p-4 custom-scroll space-y-4 bg-[#E0E5EC]"
          >
            <div v-if="processedLogs.length === 0" class="h-full flex flex-col items-center justify-center text-gray-400 gap-2 opacity-60">
              <Terminal class="w-8 h-8" />
              <span class="italic">等待指令...</span>
            </div>

            <div v-for="(log, idx) in processedLogs" :key="idx" class="animate-in fade-in slide-in-from-bottom-2 duration-300">
              
              <!-- Standard Text Thought -->
              <div v-if="log.type === 'thought' && log.content.trim()" class="flex gap-3 group">
                <div class="w-1 bg-blue-400/30 group-hover:bg-blue-500 rounded-full shrink-0 my-1 transition-colors"></div>
                <div class="flex-1 min-w-0">
                  <div class="text-gray-600 leading-relaxed text-xs whitespace-pre-wrap" v-html="renderHtml(log.content)"></div>
                </div>
              </div>

              <!-- Loading Block (Partial) -->
              <div v-if="log.type === 'loading_block'" class="flex flex-col gap-2 p-3 rounded-lg border border-dashed border-gray-300 bg-gray-50/50">
                 <div class="flex items-center gap-3 animate-pulse">
                    <Loader2 class="w-4 h-4 animate-spin text-gray-400" />
                    <span class="text-[10px] uppercase font-bold text-gray-400 tracking-wider">生成中: {{ getBlockTitle(log.tag) }}...</span>
                 </div>
                 
                 <!-- Render Partial Content as Cards if available -->
                 <div v-if="log.tag === 'PROMPT_REFINEMENT' && log.content" class="flex flex-col gap-2 opacity-70">
                     <template v-for="(line, i) in log.content.split('\n')" :key="i">
                         <div v-if="line.trim()" class="bg-indigo-50/50 p-2 rounded-lg border border-indigo-100 flex items-start gap-2">
                             <Sparkles class="w-3.5 h-3.5 text-indigo-500 mt-0.5 shrink-0" />
                             <span class="text-xs text-gray-600 font-mono leading-snug break-all">{{ line }}</span>
                         </div>
                     </template>
                 </div>
              </div>

              <!-- Completed Block (Parsed Cards) -->
              <div v-if="log.type === 'block'" class="rounded-xl border overflow-hidden shadow-sm transition-all hover:shadow-md" :class="getBlockColor(log.tag)">
                 <div 
                   class="px-3 py-2 flex items-center justify-between cursor-pointer hover:brightness-95 transition-all"
                   @click="toggleExpand(idx)"
                 >
                    <div class="flex items-center gap-2">
                       <component :is="getBlockIcon(log.tag)" class="w-4 h-4" />
                       <span class="font-bold text-[10px] tracking-widest uppercase">{{ getBlockTitle(log.tag) }}</span>
                    </div>
                    <component :is="expandedItems.has(idx) ? ChevronDown : ChevronRight" class="w-4 h-4 opacity-50" />
                 </div>
                 
                 <div v-if="expandedItems.has(idx)" class="p-3 bg-white/60 border-t border-black/5">
                    
                    <!-- Meta (JSON Card) -->
                    <div v-if="['META'].includes(log.tag)">
                        <div v-if="parseBlockData(log.content)?.meta" class="space-y-2">
                            <div class="bg-white p-2 rounded-lg border border-orange-100 shadow-sm flex flex-col gap-1">
                                <div class="text-[10px] font-bold text-orange-400 uppercase tracking-wider">项目标题</div>
                                <div class="text-sm font-bold text-gray-700">{{ parseBlockData(log.content).meta.project_title }}</div>
                            </div>
                            <div class="bg-white p-2 rounded-lg border border-orange-100 shadow-sm flex flex-col gap-1">
                                <div class="text-[10px] font-bold text-orange-400 uppercase tracking-wider">核心梗概</div>
                                <div class="text-xs text-gray-600 leading-relaxed">{{ parseBlockData(log.content).meta.core_premise }}</div>
                            </div>
                        </div>
                        <div v-else class="text-gray-600 text-xs whitespace-pre-wrap">{{ log.content }}</div>
                    </div>

                    <!-- Outline (List) -->
                    <div v-else-if="['OUTLINE'].includes(log.tag)">
                        <div v-if="parseBlockData(log.content)?.outline" class="space-y-2">
                            <div v-for="(val, key) in parseBlockData(log.content).outline" :key="key" class="bg-white p-3 rounded-lg border border-blue-100 shadow-sm flex flex-col gap-2">
                                <div class="flex gap-2">
                                    <span class="text-[10px] font-bold text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded">{{ getOutlineLabel(key as string) }}</span>
                                    <span>{{ val }}</span>
                                </div>
                            </div>
                        </div>
                        <div v-else class="text-gray-600 text-xs whitespace-pre-wrap">{{ log.content }}</div>
                    </div>

                    <!-- Characters (Grid Cards) -->
                    <div v-else-if="log.tag === 'CHARACTERS'" class="grid grid-cols-1 gap-2">
                        <template v-if="parseBlockData(log.content)?.characters">
                            <template v-for="(char, i) in (parseBlockData(log.content).characters || [])" :key="i">
                                <div class="bg-white p-2.5 rounded-lg border border-purple-100 shadow-sm flex gap-3 items-start hover:shadow-md transition-shadow">
                                    <div class="w-9 h-9 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center font-bold text-xs shrink-0 border border-purple-200">{{ char.name?.[0] }}</div>
                                    <div class="min-w-0">
                                        <div class="flex items-center gap-2 mb-1">
                                            <span class="font-bold text-gray-700 text-xs">{{ char.name }}</span>
                                            <span class="text-[9px] bg-purple-50 text-purple-500 px-1.5 py-0.5 rounded border border-purple-100">{{ char.role }}</span>
                                        </div>
                                        <p class="text-gray-500 line-clamp-2 text-[10px] leading-snug">{{ char.description }}</p>
                                    </div>
                                </div>
                            </template>
                        </template>
                        <div v-else class="text-gray-600 text-xs whitespace-pre-wrap">{{ log.content }}</div>
                    </div>

                    <!-- Scenes (List Cards) -->
                    <div v-else-if="log.tag === 'SCENES'" class="space-y-2">
                        <template v-if="parseBlockData(log.content)?.scenes">
                            <template v-for="(scene, i) in (parseBlockData(log.content).scenes || [])" :key="i">
                                <div class="bg-white p-2.5 rounded-lg border border-green-100 shadow-sm flex flex-col gap-1 hover:shadow-md transition-shadow">
                                    <div class="flex items-center justify-between">
                                        <div class="flex items-center gap-1.5">
                                            <MapPin class="w-3.5 h-3.5 text-green-500" />
                                            <span class="font-bold text-gray-700 text-xs">{{ scene.location_name }}</span>
                                        </div>
                                        <div class="text-[9px] text-green-600 bg-green-50 px-1.5 py-0.5 rounded border border-green-100">{{ scene.mood }}</div>
                                    </div>
                                </div>
                            </template>
                        </template>
                        <div v-else class="text-gray-600 text-xs whitespace-pre-wrap">{{ log.content }}</div>
                    </div>

                    <!-- Storyboard (Shot List) -->
                    <div v-else-if="log.tag === 'STORYBOARD'" class="space-y-2">
                        <!-- Handle New Structure (with scene/characters context) -->
                        <template v-if="parseBlockData(log.content)?.storyboards">
                            <div class="bg-purple-50/50 p-2 rounded-lg border border-purple-100 text-[10px] text-purple-600 mb-2 flex flex-wrap gap-2">
                                <span v-if="parseBlockData(log.content).scene" class="font-bold flex items-center gap-1"><MapPin class="w-3 h-3"/> {{ parseBlockData(log.content).scene }}</span>
                                <span v-if="parseBlockData(log.content).characters" class="flex items-center gap-1"><User class="w-3 h-3"/> {{ parseBlockData(log.content).characters.join(', ') }}</span>
                            </div>
                            <template v-for="(shot, i) in (parseBlockData(log.content).storyboards || [])" :key="i">
                                <div class="bg-white p-2.5 rounded-lg border border-pink-100 shadow-sm flex gap-3 hover:shadow-md transition-shadow">
                                    <div class="w-7 h-7 rounded bg-pink-100 text-pink-500 flex items-center justify-center font-bold text-[10px] shrink-0 border border-pink-200">{{ shot.shot_id }}</div>
                                    <div class="flex-1 min-w-0">
                                        <div class="flex justify-between items-center mb-1">
                                            <span class="text-[9px] font-bold text-pink-500 bg-pink-50 px-1.5 py-0.5 rounded border border-pink-100">{{ shot.type || shot.shot_type }}</span>
                                            <span class="text-[9px] text-gray-400 font-mono">{{ shot.duration || (shot.end_time - shot.start_time).toFixed(1) + 's' }}</span>
                                        </div>
                                        <p class="text-gray-700 font-bold mb-1.5 text-xs leading-snug">{{ shot.description || shot.action }}</p>
                                    </div>
                                </div>
                            </template>
                        </template>
                        
                        <!-- Handle Legacy Structure -->
                        <template v-else-if="parseBlockData(log.content)?.storyboard">
                            <template v-for="(shot, i) in (parseBlockData(log.content).storyboard || [])" :key="i">
                                <div class="bg-white p-2.5 rounded-lg border border-pink-100 shadow-sm flex gap-3 hover:shadow-md transition-shadow">
                                    <div class="w-7 h-7 rounded bg-pink-100 text-pink-500 flex items-center justify-center font-bold text-[10px] shrink-0 border border-pink-200">{{ shot.shot_id }}</div>
                                    <div class="flex-1 min-w-0">
                                        <div class="flex justify-between items-center mb-1">
                                            <span class="text-[9px] font-bold text-pink-500 bg-pink-50 px-1.5 py-0.5 rounded border border-pink-100">{{ shot.shot_type }}</span>
                                            <span class="text-[9px] text-gray-400 font-mono">{{ shot.duration }}</span>
                                        </div>
                                        <p class="text-gray-700 font-bold mb-1.5 text-xs leading-snug">{{ shot.action }}</p>
                                    </div>
                                </div>
                            </template>
                        </template>
                        <div v-else class="text-gray-600 text-xs whitespace-pre-wrap">{{ log.content }}</div>
                    </div>
                    
                    <!-- Prompt Refinement (Flex Cards) -->
                    <div v-else-if="log.tag === 'PROMPT_REFINEMENT'">
                         <div class="flex flex-col gap-2">
                             <template v-for="(line, idx) in log.content.split('\n')" :key="idx">
                                 <div v-if="line.trim()" class="bg-indigo-50/50 p-2 rounded-lg border border-indigo-100 flex items-start gap-2">
                                     <Sparkles class="w-3.5 h-3.5 text-indigo-500 mt-0.5 shrink-0" />
                                     <span class="text-xs text-gray-600 font-mono leading-snug break-all">{{ line }}</span>
                                 </div>
                             </template>
                         </div>
                    </div>

                    <!-- Storyboard Array (New Format) -->
                    <div v-else-if="log.tag === 'STORYBOARD_ARRAY'" class="space-y-3">
                        <div v-if="Array.isArray(log.content)">
                            <div v-for="(segment, idx) in log.content" :key="idx" class="bg-white p-3 rounded-lg border border-pink-100 shadow-sm flex flex-col gap-2">
                                <div class="flex items-center justify-between border-b border-pink-50 pb-2 mb-1">
                                    <span class="text-[10px] font-bold text-pink-500 bg-pink-50 px-2 py-0.5 rounded-full">片段 {{ idx as number + 1 }}</span>
                                    <span class="text-[9px] text-gray-400">~15s</span>
                                </div>
                                <div class="text-xs text-gray-600 font-mono whitespace-pre-wrap leading-relaxed bg-gray-50/50 p-2 rounded">
                                    {{ segment }}
                                </div>
                            </div>
                        </div>
                        <div v-else class="text-gray-600 text-xs whitespace-pre-wrap">{{ JSON.stringify(log.content, null, 2) }}</div>
                    </div>

                 </div>
              </div>

              <!-- Tool Call -->
              <div v-if="log.type === 'tool'" class="rounded-lg border border-gray-200 bg-gray-50/50 overflow-hidden shadow-sm">
                <div 
                  class="px-3 py-2 flex items-center justify-between cursor-pointer hover:bg-white transition-colors"
                  @click="toggleExpand(idx)"
                >
                  <div class="flex items-center gap-2 overflow-hidden">
                    <span class="text-purple-600 font-bold truncate">{{ log.name }}</span>
                    <span v-if="log.status === 'running'" class="text-[9px] bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded animate-pulse font-bold">运行中</span>
                    <span v-else-if="log.status === 'error'" class="text-[9px] bg-red-100 text-red-600 px-1.5 py-0.5 rounded font-bold">失败</span>
                    <span v-else class="text-[9px] bg-green-100 text-green-600 px-1.5 py-0.5 rounded flex items-center gap-1 font-bold">
                      <Clock class="w-3 h-3" /> {{ log.duration || 0 }}s
                    </span>
                  </div>
                </div>
                <div v-if="expandedItems.has(idx)" class="border-t border-gray-200 p-3 bg-white/40 space-y-2">
                  <div>
                    <span class="text-gray-400 block mb-1 text-[9px] uppercase font-bold">输入参数</span>
                    <pre class="text-green-700 bg-green-50/50 p-2 rounded border border-green-100 overflow-x-auto custom-scroll">{{ JSON.stringify(log.input, null, 2) }}</pre>
                  </div>
                  <div v-if="log.output">
                    <span class="text-gray-400 block mb-1 text-[9px] uppercase font-bold">输出结果</span>
                    <pre class="text-gray-600 bg-gray-50 p-2 rounded border border-gray-200 overflow-x-auto custom-scroll max-h-[200px]">{{ log.output }}</pre>
                  </div>
                </div>
              </div>

              <!-- System Messages -->
              <div v-if="log.type === 'status'" class="flex items-center gap-2 text-gray-400 py-1 text-[10px] uppercase font-bold tracking-wider justify-center">
                 <div class="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></div>
                 <span>{{ log.content }}</span>
              </div>
              
              <div v-if="log.type === 'finish'" class="flex items-center gap-2 text-green-600 bg-green-50 border border-green-100 p-2 rounded-lg justify-center font-bold mt-2 shadow-sm">
                 <CheckCircle2 class="w-4 h-4" />
                 <span>全部任务完成</span>
              </div>

              <div v-if="log.type === 'error'" class="flex items-center gap-2 text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg shadow-sm">
                 <AlertCircle class="w-4 h-4 shrink-0" />
                 <span class="break-all">{{ log.content }}</span>
              </div>

            </div>
          </div>
        </div>
      </div>

      <div 
        class="absolute bottom-0 right-0 w-6 h-6 cursor-nwse-resize flex items-end justify-end p-1 text-gray-400 hover:text-gray-600 z-20"
        @mousedown="startResize"
      >
        <svg viewBox="0 0 24 24" class="w-full h-full fill-current"><path d="M22 22H20V20H22V22ZM22 18H20V16H22V18ZM18 22H16V20H18V22ZM18 18H16V16H18V18Z" /></svg>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.custom-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
.custom-scroll::-webkit-scrollbar-track { background: transparent; }
.custom-scroll::-webkit-scrollbar-thumb { background-color: #cbd5e0; border-radius: 10px; border: 2px solid #E0E5EC; }
.custom-scroll::-webkit-scrollbar-thumb:hover { background-color: #a0aec0; }
.pop-enter-active, .pop-leave-active { transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.pop-enter-from, .pop-leave-to { transform: scale(0.9) translateY(20px); opacity: 0; }
</style>