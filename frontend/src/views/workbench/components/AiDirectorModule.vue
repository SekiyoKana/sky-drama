<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue'
import { 
  Wand2, Sparkles, Loader2,
  FileText, X, Scissors
} from 'lucide-vue-next'
import NeuButton from '@/components/base/NeuButton.vue'

const props = defineProps<{ 
  visible: boolean
  loading?: boolean 
}>()

const emit = defineEmits(['close', 'generate', 'stop', 'handle-down'])
const promptText = ref('')
const moduleRef = ref<HTMLElement | null>(null)

// Tabs
const activeTab = ref<'script' | 'split'>('script')
const tabs = [
  { id: 'script', label: '剧本', icon: FileText },
  { id: 'split', label: '分镜拆分', icon: Scissors },
]

// --- Window State ---
const windowState = reactive({
  x: window.innerWidth - 340, // Default to top-right
  y: 80,
  w: 300,
  h: 400
})

// --- Drag Logic ---
let isDragging = false
let dragOffset = { x: 0, y: 0 }

const startDrag = (e: MouseEvent) => {
  if (!moduleRef.value) return
  isDragging = true
  dragOffset.x = e.clientX - windowState.x
  dragOffset.y = e.clientY - windowState.y
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.body.style.userSelect = 'none'
  emit('handle-down')
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

// --- Resize Logic ---
let isResizing = false
const startResize = (e: MouseEvent) => {
  isResizing = true
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
  e.stopPropagation()
  emit('handle-down')
}

const onResize = (e: MouseEvent) => {
  if (!isResizing) return
  const newW = Math.max(250, e.clientX - windowState.x)
  const newH = Math.max(300, e.clientY - windowState.y)
  windowState.w = Math.min(newW, window.innerWidth - windowState.x)
  windowState.h = Math.min(newH, window.innerHeight - windowState.y)
}

const stopResize = () => {
  isResizing = false
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
})

const handleGenerate = () => {
  emit('generate', { 
      prompt: promptText.value, 
      tags: {
          mode: activeTab.value 
      }
  })
}
</script>
  
<template>
  <transition name="pop">
    <div 
      v-if="visible"
      ref="moduleRef"
      class="fixed z-[50] bg-[#E0E5EC] rounded-[1.5rem] flex flex-col overflow-hidden shadow-2xl border border-white/40"
      :style="{ left: windowState.x + 'px', top: windowState.y + 'px', width: windowState.w + 'px', height: windowState.h + 'px' }"
    >
      <div 
        class="flex items-center justify-between px-4 py-3 bg-[#E0E5EC] border-b border-gray-200/40 cursor-move select-none shrink-0" 
        @mousedown="startDrag"
      >
        <div class="flex items-center gap-2 overflow-hidden text-gray-500">
           <Sparkles class="w-4 h-4 text-purple-500" />
           <h3 class="font-bold text-gray-600 text-xs tracking-wider uppercase">AI 导演</h3>
        </div>
        <button 
          @click="emit('close')" 
          class="p-1.5 rounded-full neu-flat hover:text-red-500 active:neu-pressed transition-all text-gray-400"
          @mousedown.stop
        >
          <X class="w-3.5 h-3.5" />
        </button>
      </div>
      
      <div class="flex-1 flex flex-col p-4 gap-4 min-h-0 bg-[#E0E5EC]">
          <div class="flex gap-2 p-1 rounded-xl shrink-0 bg-[#E0E5EC]">
              <button 
                  v-for="tab in tabs" 
                  :key="tab.id"
                  @click="activeTab = tab.id as any"
                  class="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-bold transition-all"
                  :class="activeTab === tab.id 
                      ? 'neu-pressed text-blue-500' 
                      : 'neu-flat text-gray-500 hover:text-gray-600'"
              >
                  <component :is="tab.icon" class="w-3.5 h-3.5" />
                  {{ tab.label }}
              </button>
          </div>
  
          <div class="flex-1 flex flex-col gap-3 min-h-0">
              <div class="h-full neu-pressed rounded-2xl p-3 relative border border-white/20">
                <textarea 
                  v-model="promptText" 
                  class="w-full h-full bg-transparent outline-none resize-none text-sm text-gray-600 placeholder-gray-400 leading-relaxed custom-scroll" 
                  placeholder="输入你的指令..."
                ></textarea>
              </div>
              
              <NeuButton 
                block 
                variant="primary" 
                class="h-11 rounded-xl flex items-center justify-center gap-2 shadow-md active:shadow-inner transition-all shrink-0" 
                :class="{ 'bg-red-50 text-red-500 hover:text-red-600 border-red-200': loading }"
                @click="loading ? emit('stop') : handleGenerate()"
              >
                <template v-if="loading">
                  <Loader2 class="w-4 h-4 animate-spin" />
                  <span class="text-xs font-bold">停止生成</span>
                </template>
                <template v-else>
                  <Wand2 class="w-4 h-4" />
                  <span class="text-xs font-bold">发送指令</span>
                </template>
              </NeuButton>
          </div>
      </div>

      <div 
        class="absolute bottom-0 right-0 w-6 h-6 cursor-nwse-resize flex items-end justify-end p-1 text-gray-400 hover:text-gray-600 z-10" 
        @mousedown="startResize"
      ></div>
    </div>
  </transition>
</template>
  
<style scoped>
.custom-scroll::-webkit-scrollbar { width: 4px; }
.custom-scroll::-webkit-scrollbar-thumb { background-color: #cbd5e0; border-radius: 4px; border: 1px solid #E0E5EC; }

.pop-enter-active, .pop-leave-active { transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); transform-origin: top right; }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: scale(0.95); }
</style>