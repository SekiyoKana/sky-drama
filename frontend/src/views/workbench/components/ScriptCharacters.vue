<script setup lang="ts">
import { ref } from 'vue'
import { Trash2, Maximize2, Image as ImageIcon, Plus, Upload } from 'lucide-vue-next'
import NeuButton from '@/components/base/NeuButton.vue'
import { resolveImageUrl } from '@/utils/assets'

defineProps<{
  characters: any[]
  generatingItems: Record<string, number>
}>()

const emit = defineEmits<{
  (e: 'delete', index: number, item: any): void
  (e: 'preview', index: number): void
  (e: 'add'): void
  (e: 'generate', type: 'image', item: any, index: number): void
  (e: 'upload-reference', item: any, index: number, file: File): void
}>()

const uploadInputs = ref<(HTMLInputElement | null)[]>([])

const triggerUpload = (index: number) => {
  uploadInputs.value[index]?.click()
}

const handleFileChange = (event: Event, item: any, index: number) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    emit('upload-reference', item, index, file)
  }
  if (target) {
    target.value = ''
  }
}
</script>

<template>
  <div class="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-5">
    <div v-for="(char, idx) in characters" :key="idx" class="neu-flat p-3 rounded-xl flex flex-col gap-3 group transition-all hover:bg-white/40 relative">
      
      <button 
        class="absolute top-2 right-2 p-1.5 rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100 z-20"
        @click.stop="emit('delete', idx, char)"
      >
        <Trash2 class="w-3.5 h-3.5" />
      </button>

      <!-- Unified Header: Avatar + Info -->
      <div class="flex items-start gap-3 pr-6">
          <!-- Avatar Column (Avatar + Role Tag) -->
          <div class="flex flex-col items-center gap-2 shrink-0">
              <!-- Avatar (Circular) -->
              <div 
                  class="w-12 h-12 rounded-full shadow-sm border-2 border-white overflow-hidden relative group/avatar bg-blue-50 flex items-center justify-center cursor-pointer"
                  @click="emit('preview', idx)"
               >
                   <img v-if="char.image_url || char.reference_image" :src="resolveImageUrl(char.image_url || char.reference_image)" class="w-full h-full object-cover transition-transform duration-500 group-hover/avatar:scale-110" />
                   <span v-else class="text-blue-500 font-bold text-lg">{{ char.name ? char.name[0] : '?' }}</span>
                   
                   <!-- Hover Overlay for Image -->
                  <div class="absolute inset-0 bg-black/10 group-hover/avatar:bg-black/30 transition-colors flex items-center justify-center opacity-0 group-hover/avatar:opacity-100">
                      <Maximize2 class="w-4 h-4 text-white drop-shadow-md" />
                  </div>
              </div>
              
              <!-- Role Tag (Moved here) -->
              <span class="text-[10px] px-1.5 py-0.5 rounded-md bg-gray-200/50 text-gray-500 font-medium border border-gray-200 shrink-0 text-center max-w-[60px] truncate">
                  {{ char.role }}
              </span>
              <span v-if="char.reference_image && !char.image_url" class="text-[10px] px-1.5 py-0.5 rounded-md bg-blue-100/80 text-blue-600 font-medium border border-blue-200 shrink-0 text-center max-w-[60px] truncate">
                  参考
              </span>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0 flex flex-col gap-1 pt-0.5">
              <div class="flex items-center gap-2 h-6">
                  <span class="font-bold text-gray-700 text-sm truncate w-full" :title="char.name">{{ char.name }}</span>
              </div>
              <!-- Description Tooltip on Hover -->
              <p class="text-[12px] text-gray-500 line-clamp-3 leading-relaxed opacity-80" :title="char.description">
                  {{ char.description }}
              </p>
          </div>
      </div>
      
      <!-- Action Button / Progress Bar -->
      <div class="mt-auto w-full">
          <div v-if="generatingItems[`chars-${idx}`] !== undefined" class="relative h-8 rounded-xl bg-gray-200/50 overflow-hidden border border-gray-300/50 flex items-center justify-center">
              <!-- Animated Progress Bar -->
              <div 
                  class="absolute inset-y-0 left-0 bg-blue-400/20 transition-all duration-300 ease-linear"
                  :style="{ width: `${generatingItems[`chars-${idx}`]}%` }"
              ></div>
              <!-- Jumping Icon Animation -->
              <div class="relative flex items-center gap-2 z-10">
                  <ImageIcon class="w-3.5 h-3.5 text-blue-500 animate-bounce" />
                  <span class="text-[10px] font-bold text-blue-600 tabular-nums">{{ generatingItems[`chars-${idx}`] }}%</span>
              </div>
          </div>
          
          <div v-else class="flex gap-2">
              <input
                type="file"
                accept="image/*"
                class="hidden"
                :ref="(el) => (uploadInputs[idx] = el as HTMLInputElement)"
                @change="(e) => handleFileChange(e, char, idx)"
              />
              <NeuButton
                size="sm"
                class="flex-1 text-xs"
                @click="triggerUpload(idx)"
                title="参考图"
                aria-label="参考图"
              >
                  <Upload class="w-3.5 h-3.5" />
              </NeuButton>
              <NeuButton 
                size="sm"
                class="flex-1 text-xs"
                @click="emit('generate', 'image', char, idx)"
                :title="char.image_url ? '重设' : '生成立绘'"
                :aria-label="char.image_url ? '重设' : '生成立绘'"
              >
                  <ImageIcon class="w-3.5 h-3.5" />
              </NeuButton>
          </div>
      </div>
    </div>

    <!-- Add Character Button -->
    <button 
       class="neu-flat p-3 rounded-xl flex flex-col items-center justify-center gap-2 text-gray-400 hover:text-blue-500 hover:bg-blue-50/50 transition-all border-2 border-dashed border-gray-300/50 hover:border-blue-300 min-h-[160px]"
       @click="emit('add')"
    >
       <div class="w-10 h-10 rounded-full bg-gray-200/50 flex items-center justify-center group-hover:bg-blue-100 transition-colors">
           <Plus class="w-5 h-5" />
       </div>
       <span class="text-xs font-bold">添加角色</span>
    </button>
  </div>
</template>
