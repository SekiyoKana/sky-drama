<script setup lang="ts">
  import { ref, reactive, onMounted } from 'vue'
  import { X, Plus, GripVertical, Image as ImageIcon, FileText } from 'lucide-vue-next'
  
  const props = defineProps<{
    visible: boolean
    libraryData: Record<string, string[]> // 仅用于显示的字符串列表
    fullMap?: Record<string, any[]>       // 新增：用于查找完整数据的映射表
  }>()
  
  const emit = defineEmits<{
    (e: 'close'): void
    (e: 'add-tag', category: string): void
  }>()
  
  // --- 窗口状态 ---
  const position = reactive({ x: 0, y: 0 })
  const size = reactive({ w: 340, h: 460 }) // 稍微调高一点默认高度
  const popoverRef = ref<HTMLElement | null>(null)
  
  // --- 1. 窗口拖拽逻辑 (Move) ---
  const isMoving = ref(false)
  const moveOffset = reactive({ x: 0, y: 0 })
  
  const startMove = (e: MouseEvent) => {
    if (!popoverRef.value) return
    isMoving.value = true
    moveOffset.x = e.clientX - position.x
    moveOffset.y = e.clientY - position.y
    document.addEventListener('mousemove', handleMove)
    document.addEventListener('mouseup', stopMove)
  }
  
  const handleMove = (e: MouseEvent) => {
    if (!isMoving.value || !popoverRef.value) return
    const maxX = window.innerWidth - 50
    const maxY = window.innerHeight - 50
    position.x = Math.max(0, Math.min(e.clientX - moveOffset.x, maxX))
    position.y = Math.max(0, Math.min(e.clientY - moveOffset.y, maxY))
  }
  
  const stopMove = () => {
    isMoving.value = false
    document.removeEventListener('mousemove', handleMove)
    document.removeEventListener('mouseup', stopMove)
  }
  
  // --- 2. 标签拖拽逻辑 (Drag Tag) ---
  const handleDragStart = (e: DragEvent, category: string, tagContent: string) => {
    e.stopPropagation() 
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = 'copy'
      // 兼容旧逻辑
      e.dataTransfer.setData('type', 'tag')
      e.dataTransfer.setData('category', category)
      e.dataTransfer.setData('tag', tagContent)

      // --- 新增：构造完整 Payload (包含 data) ---
      let tagObj = { category, content: tagContent, data: null }
      
      // 尝试从 fullMap 中查找完整对象
      if (props.fullMap && props.fullMap[category]) {
        const found = props.fullMap[category].find((t: any) => t.content === tagContent)
        if (found) {
            tagObj = found
        }
      }
      
      // 将完整对象序列化放入 payload
      e.dataTransfer.setData('payload', JSON.stringify(tagObj))
    }
  }

  // 辅助函数：判断是否有附加数据（用于 UI 显示图标）
  const getTagExtraType = (category: string, tagContent: string): 'image' | 'text' | null => {
    if (!props.fullMap || !props.fullMap[category]) return null
    const found = props.fullMap[category].find((t: any) => t.content === tagContent)
    if (found && found.data) {
        if (found.data.includes('http') || found.data.includes('png') || found.data.includes('jpg')) return 'image'
        return 'text'
    }
    return null
  }
  
  // --- 3. 窗口缩放逻辑 (Resize) ---
  const isResizing = ref(false)
  
  const startResize = (e: MouseEvent) => {
    isResizing.value = true
    document.addEventListener('mousemove', handleResize)
    document.addEventListener('mouseup', stopResize)
    e.stopPropagation()
  }
  
  const handleResize = (e: MouseEvent) => {
    if (!isResizing.value) return
    const newW = e.clientX - position.x
    const newH = e.clientY - position.y
    size.w = Math.max(280, Math.min(newW, 600))
    size.h = Math.max(300, Math.min(newH, 800))
  }
  
  const stopResize = () => {
    isResizing.value = false
    document.removeEventListener('mousemove', handleResize)
    document.removeEventListener('mouseup', stopResize)
  }
  
  // 初始化位置
  onMounted(() => {
    position.x = window.innerWidth - 400
    position.y = 120
  })
  </script>
  
  <template>
    <div 
      v-if="visible"
      ref="popoverRef"
      class="fixed bg-[#E0E5EC]/95 backdrop-blur-xl rounded-[1.5rem] shadow-2xl z-[9999] flex flex-col border border-white/50"
      :style="{ left: position.x + 'px', top: position.y + 'px', width: size.w + 'px', height: size.h + 'px' }"
    >
      <div 
        class="flex justify-between items-center px-5 py-4 border-b border-gray-300/30 cursor-move shrink-0 select-none bg-gray-50/30 rounded-t-[1.5rem]"
        @mousedown="startMove"
      >
        <div class="flex items-center gap-2">
           <h4 class="font-bold text-gray-600 text-sm tracking-wide">标签素材库</h4>
        </div>
        <button 
          @click="emit('close')" 
          class="hover:text-red-500 transition-colors p-1 rounded-full hover:bg-red-50" 
          @mousedown.stop
        >
          <X class="w-4 h-4" />
        </button>
      </div>
      
      <div class="flex-1 overflow-y-auto custom-scroll px-6 py-4 space-y-6 select-none" @mousedown.stop>
        
        <div v-if="Object.keys(libraryData).length === 0" class="flex flex-col items-center justify-center h-full text-gray-400 opacity-60">
            <span class="text-xs">暂无标签数据</span>
        </div>

        <div v-for="(tags, category) in libraryData" :key="category">
          <div class="flex items-center justify-between mb-3">
            <h5 class="text-[10px] font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
              <span class="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
              {{ category }}
            </h5>
          </div>
          <div class="flex flex-wrap gap-2">
            <div 
              v-for="tag in tags" 
              :key="tag"
              draggable="true"
              @dragstart="handleDragStart($event, category as string, tag)"
              class="group flex items-center gap-1.5 px-3 py-2 rounded-xl neu-flat-sm text-[11px] font-bold text-gray-600 cursor-grab active:cursor-grabbing hover:text-blue-600 hover:-translate-y-0.5 transition-all border border-transparent hover:border-blue-100"
            >
              <GripVertical class="w-3 h-3 text-gray-300 group-hover:text-blue-300" />
              
              <ImageIcon v-if="getTagExtraType(category as string, tag) === 'image'" class="w-3 h-3 text-blue-400" />
              <FileText v-else-if="getTagExtraType(category as string, tag) === 'text'" class="w-3 h-3 text-purple-400" />
              
              {{ tag }}
            </div>
            
            <button 
              @click="emit('add-tag', category as string)" 
              class="text-gray-300 hover:text-blue-500 transition-colors p-1.5 rounded-lg border border-dashed border-gray-300 hover:border-blue-300 flex items-center justify-center w-8 h-8"
              title="添加自定义标签"
            >
              <Plus class="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
  
      <div 
        class="absolute bottom-1 right-1 cursor-nwse-resize p-2 opacity-30 hover:opacity-100 transition-opacity"
        @mousedown="startResize"
      >
        <div class="w-2 h-2 bg-gray-400 rounded-full"></div>
      </div>
    </div>
  </template>
  
  <style scoped>
  .custom-scroll::-webkit-scrollbar { width: 4px; }
  .custom-scroll::-webkit-scrollbar-track { background: transparent; }
  .custom-scroll::-webkit-scrollbar-thumb { background-color: rgba(160, 174, 192, 0.4); border-radius: 20px; }
  </style>