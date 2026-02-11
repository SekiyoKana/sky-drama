<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Trash2, Plus, Video, Image as ImageIcon } from 'lucide-vue-next'
import NeuButton from '@/components/base/NeuButton.vue'
import { safeRandomUUID } from '@/utils/id'

const props = defineProps<{
  storyboard: any[]
  generatingItems: Record<string, number>
}>()

const emit = defineEmits<{
  (e: 'add'): void
  (e: 'delete', index: number, item: any): void
  (e: 'edit', item: any): void
  (e: 'preview', index: number): void
  (e: 'open-video', url: string, poster: string): void
  (e: 'generate', type: 'image' | 'video', item: any, index: number): void
  (e: 'request-save'): void
}>()

// --- Drag & Drop Logic ---
const draggedIndex = ref<number>(-1)
const isDragHandleDown = ref(false)

const onGlobalMouseUp = () => {
    isDragHandleDown.value = false
}

onMounted(() => {
    window.addEventListener('mouseup', onGlobalMouseUp)
})

onUnmounted(() => {
    window.removeEventListener('mouseup', onGlobalMouseUp)
})

const onDragStart = (e: DragEvent, index: number) => {
    if (!isDragHandleDown.value) {
        e.preventDefault()
        return
    }
    
    draggedIndex.value = index
    e.dataTransfer!.effectAllowed = 'move'
    e.dataTransfer!.dropEffect = 'move'
}

const onHandleMouseDown = () => {
    isDragHandleDown.value = true
}

const reindexStoryboard = (list: any[]) => {
    list.forEach((item, index) => {
        item.shot_id = (index + 1).toString()
    })
}

const onDrop = (targetIndex: number) => {
    if (draggedIndex.value === -1 || draggedIndex.value === targetIndex) return
    
    const list = props.storyboard
    if (!list) return

    const itemToMove = list[draggedIndex.value]
    
    // Remove from old position
    list.splice(draggedIndex.value, 1)
    // Insert at new position
    list.splice(targetIndex, 0, itemToMove)
    
    // Reindex
    reindexStoryboard(list)
    
    emit('request-save')
    draggedIndex.value = -1
}

const handleInsertShot = (index: number, position: 'before' | 'after') => {
    const list = props.storyboard
    if (!list) return // Should not happen if parent passes array
    
    const uuid = safeRandomUUID()
    const newShot = {
        id: `storyboard_${uuid}`,
        shot_id: '', // Will be set by reindex
        action: '新分镜',
        shot_type: '全景',
        visual_prompt: '请点击此处编辑分镜画面...',
        image_url: ''
    }
    
    // Calculate insert index
    const insertIndex = position === 'after' ? index + 1 : index
    
    // Insert at new position
    list.splice(insertIndex, 0, newShot)
    
    reindexStoryboard(list)
    emit('request-save')
    
    // Open preview
    emit('preview', insertIndex)
}
</script>

<template>
  <div class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-5">
      <div v-for="(shot, idx) in storyboard" 
          :key="idx" 
          class="neu-flat p-3 rounded-xl transition-all flex flex-col relative group"
          draggable="true"
          @dragstart="onDragStart($event, idx)"
          @dragover.prevent
          @dragenter.prevent
          @drop="onDrop(idx)"
      >
          <button 
              class="absolute top-2 right-2 p-1.5 rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100 z-10"
              @click.stop="emit('delete', idx, shot)"
          >
              <Trash2 class="w-3.5 h-3.5" />
          </button>
          
          <!-- Insert Button (Left Side - Before) -->
          <div 
              class="absolute -left-6.5 top-1/2 -translate-y-1/2 z-20 opacity-0 group-hover:opacity-100 transition-all duration-300 ease-out flex items-center justify-center w-8 h-full pointer-events-none"
          >
               <button 
                  class="w-8 h-8 rounded-full bg-[#E0E5EC] shadow-[3px_3px_6px_#bec3c9,-3px_-3px_6px_#ffffff] flex items-center justify-center text-gray-400 hover:text-blue-500 hover:scale-110 active:scale-95 transition-all duration-300 transform scale-0 group-hover:scale-100 rotate-90 group-hover:rotate-0 pointer-events-auto cursor-pointer border border-white/50"
                  title="在此前插入分镜"
                  @click.stop="handleInsertShot(idx, 'before')"
              >
                  <Plus class="w-3.5 h-3.5" />
              </button>
          </div>

          <!-- Insert Button (Right Side - After) -->
          <div 
              class="absolute -right-6.5 top-1/2 -translate-y-1/2 z-20 opacity-0 group-hover:opacity-100 transition-all duration-300 ease-out flex items-center justify-center w-8 h-full pointer-events-none"
          >
              <button 
                  class="w-8 h-8 rounded-full bg-[#E0E5EC] shadow-[3px_3px_6px_#bec3c9,-3px_-3px_6px_#ffffff] flex items-center justify-center text-gray-400 hover:text-blue-500 hover:scale-110 active:scale-95 transition-all duration-300 transform scale-0 group-hover:scale-100 -rotate-90 group-hover:rotate-0 pointer-events-auto cursor-pointer border border-white/50"
                  title="在此后插入分镜"
                  @click.stop="handleInsertShot(idx, 'after')"
              >
                  <Plus class="w-3.5 h-3.5" />
              </button>
          </div>

          <div class="flex gap-3 mb-2 mr-6">
              <div 
                  class="drag-handle w-8 h-8 rounded-lg neu-flat flex items-center justify-center font-bold text-gray-400 text-xs shrink-0 cursor-grab active:cursor-grabbing hover:text-pink-500 transition-colors select-none" 
                  @mousedown="onHandleMouseDown"
                  @click="emit('edit', shot)" 
                  title="按住拖拽排序 / 点击编辑"
              >
                  {{ shot.shot_id }}
              </div>
              <div class="flex-1 flex justify-start items-center min-w-0 cursor-pointer hover:bg-black/5 rounded px-1 transition-colors" @click="emit('edit', shot)" title="点击编辑">
                  <p class="text-sm font-bold text-gray-700 leading-snug truncate">{{ shot.action }}</p>
              </div>
          </div>

           <!-- Image with Overlay -->
           <div 
             class="mb-3 rounded-lg overflow-hidden relative group cursor-pointer border border-gray-200 bg-gray-100 aspect-video"
             @click="emit('preview', idx)"
           >
              <!-- Video Indicator -->
              <button 
                v-if="shot.video_url"
                class="absolute top-2 right-2 z-20 p-1.5 rounded-full bg-black/50 text-white hover:bg-blue-500 hover:scale-110 transition-all backdrop-blur-sm"
                @click.stop="emit('open-video', shot.video_url, shot.image_url)"
                title="预览视频"
              >
                 <Video class="w-3.5 h-3.5" />
              </button>

              <img v-if="shot.image_url" :src="shot.image_url" class="w-full h-full object-cover" />
             <div v-else class="w-full h-full flex items-center justify-center text-gray-400 text-xs italic">
                暂无预览
             </div>

              <!-- Translucent Overlay -->
             <div class="absolute bottom-0 left-0 right-0 p-2 bg-black/40 backdrop-blur-sm border-t border-white/10 transition-transform duration-300 transform translate-y-full group-hover:translate-y-0">
                <p class="text-sm text-white/90 line-clamp-2 leading-tight">
                   {{ shot.visual_prompt }}
                </p>
             </div>
          </div>
          
          <!-- Action Button / Progress Bar -->
          <div class="mt-auto w-full">
              <div v-if="generatingItems[`board-${idx}`] !== undefined" class="relative h-8 rounded-xl bg-gray-200/50 overflow-hidden border border-gray-300/50 flex items-center justify-center">
                  <!-- Animated Progress Bar -->
                  <div 
                      class="absolute inset-y-0 left-0 bg-pink-400/20 transition-all duration-300 ease-linear"
                      :style="{ width: `${generatingItems[`board-${idx}`]}%` }"
                  ></div>
                  <!-- Jumping Icon Animation -->
                  <div class="relative flex items-center gap-2 z-10">
                      <Video class="w-3.5 h-3.5 text-pink-500 animate-bounce" />
                      <span class="text-[10px] font-bold text-pink-600 tabular-nums">{{ generatingItems[`board-${idx}`] }}%</span>
                  </div>
              </div>
              
              <div v-else class="flex gap-2">
                   <NeuButton 
                      size="sm" 
                      class="flex-1 text-xs"
                      @click="emit('generate', 'image', shot, idx)"
                  >
                     <ImageIcon class="w-3.5 h-3.5 mr-1" />
                     {{ shot.image_url ? '重绘' : '绘图' }}
                  </NeuButton>

                  <NeuButton 
                      size="sm" 
                      class="flex-1 text-xs"
                      variant="primary"
                      @click="emit('generate', 'video', shot, idx)"
                      :disabled="!shot.image_url"
                      :title="!shot.image_url ? '需先生成分镜图' : ''"
                  >
                     <Video class="w-3.5 h-3.5 mr-1" />
                     {{ shot.video_url ? '重制' : '视频' }}
                  </NeuButton>
              </div>
          </div>
      </div>
      
      <!-- Add Shot Button -->
      <button 
         class="neu-flat p-3 rounded-xl flex flex-col items-center justify-center gap-2 text-gray-400 hover:text-purple-500 hover:bg-purple-50/50 transition-all border-2 border-dashed border-gray-300/50 hover:border-purple-300 min-h-[160px]"
         @click="emit('add')"
      >
         <div class="w-10 h-10 rounded-full bg-gray-200/50 flex items-center justify-center group-hover:bg-purple-100 transition-colors">
             <Plus class="w-5 h-5" />
         </div>
         <span class="text-xs font-bold">添加分镜</span>
      </button>
  </div>
</template>
