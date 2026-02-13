<script setup lang="ts">
import { ref } from 'vue'
import { Trash2, MapPin, Maximize2, Image as ImageIcon, Plus, Upload } from 'lucide-vue-next'
import NeuButton from '@/components/base/NeuButton.vue'
import { resolveImageUrl } from '@/utils/assets'

defineProps<{
  scenes: any[]
  generatingItems: Record<string, number>
}>()

const emit = defineEmits<{
  (e: 'delete', index: number, item: any): void
  (e: 'edit', item: any): void
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
  <div class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-5">
      <div v-for="(scene, idx) in scenes" :key="idx" class="neu-flat p-3 rounded-xl transition-transform flex flex-col relative group">
          <button 
              class="absolute top-2 right-2 p-1.5 rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100 z-10"
              @click.stop="emit('delete', idx, scene)"
          >
              <Trash2 class="w-3.5 h-3.5" />
          </button>
            <div class="flex items-center justify-between mb-2 mr-6">
              <div class="flex items-center gap-2 cursor-pointer hover:bg-black/5 rounded px-1 transition-colors" @click="emit('edit', scene)" title="点击编辑">
                  <MapPin class="w-4 h-4 text-orange-500" />
                  <span class="text-xs font-bold text-gray-700 truncate max-w-[140px]">{{ scene.location_name }}</span>
              </div>
              <span class="text-[10px] font-bold text-gray-400">第 {{ idx + 1 }} 场</span>
          </div>
          
          <!-- Scene Card with Image & Overlay -->
          <div 
            class="mb-3 rounded-lg overflow-hidden relative group cursor-pointer border border-gray-200 bg-gray-100"
            style="aspect-ratio: 16/9;"
            @click="emit('preview', idx)"
          >
             <!-- Image or Placeholder -->
             <img v-if="scene.image_url || scene.reference_image" :src="resolveImageUrl(scene.image_url || scene.reference_image)" class="w-full h-full object-cover" />
             <div v-else class="w-full h-full flex items-center justify-center text-gray-400 text-xs italic">
                暂无图片
             </div>

             <div v-if="scene.reference_image && !scene.image_url" class="absolute top-2 left-2 px-2 py-0.5 text-[10px] font-semibold bg-orange-100/90 text-orange-700 border border-orange-200 rounded">
                参考
             </div>

             <!-- Translucent Prompt Overlay -->
             <div class="absolute bottom-0 left-0 right-0 p-2 bg-black/40 backdrop-blur-sm border-t border-white/10 transition-transform duration-300 transform translate-y-full group-hover:translate-y-0">
                <p class="text-sm text-white/90 line-clamp-2 leading-tight drop-shadow-md">
                   {{ scene.visual_prompt }}
                </p>
             </div>
             
             <!-- Maximize Icon -->
             <div class="absolute top-2 right-2 p-1.5 bg-black/30 rounded-full text-white opacity-0 group-hover:opacity-100 transition-opacity">
                <Maximize2 class="w-3 h-3" />
             </div>
          </div>
          
          <!-- Action Button / Progress Bar -->
          <div class="mt-auto w-full">
              <div v-if="generatingItems[`scenes-${idx}`] !== undefined" class="relative h-8 rounded-xl bg-gray-200/50 overflow-hidden border border-gray-300/50 flex items-center justify-center">
                  <!-- Animated Progress Bar -->
                  <div 
                      class="absolute inset-y-0 left-0 bg-orange-400/20 transition-all duration-300 ease-linear"
                      :style="{ width: `${generatingItems[`scenes-${idx}`]}%` }"
                  ></div>
                  <!-- Jumping Icon Animation -->
                  <div class="relative flex items-center gap-2 z-10">
                      <ImageIcon class="w-3.5 h-3.5 text-orange-500 animate-bounce" />
                      <span class="text-[10px] font-bold text-orange-600 tabular-nums">{{ generatingItems[`scenes-${idx}`] }}%</span>
                  </div>
              </div>
              
              <div v-else class="flex gap-2">
                  <input
                    type="file"
                    accept="image/*"
                    class="hidden"
                    :ref="(el) => (uploadInputs[idx] = el as HTMLInputElement)"
                    @change="(e) => handleFileChange(e, scene, idx)"
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
                    @click="emit('generate', 'image', scene, idx)"
                    :title="scene.image_url ? '重设' : '生成场景图'"
                    :aria-label="scene.image_url ? '重设' : '生成场景图'"
                  >
                     <ImageIcon class="w-3.5 h-3.5" />
                  </NeuButton>
              </div>
          </div>
      </div>

      <!-- Add Scene Button -->
      <button 
         class="neu-flat p-3 rounded-xl flex flex-col items-center justify-center gap-2 text-gray-400 hover:text-orange-500 hover:bg-orange-50/50 transition-all border-2 border-dashed border-gray-300/50 hover:border-orange-300 min-h-[200px]"
         @click="emit('add')"
      >
         <div class="w-10 h-10 rounded-full bg-gray-200/50 flex items-center justify-center group-hover:bg-orange-100 transition-colors">
             <Plus class="w-5 h-5" />
         </div>
         <span class="text-xs font-bold">添加场景</span>
      </button>
  </div>
</template>
