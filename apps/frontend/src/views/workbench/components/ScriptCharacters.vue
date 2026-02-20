<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { Trash2, Maximize2, Image as ImageIcon, Plus, Upload } from 'lucide-vue-next'
import NeuButton from '@/components/base/NeuButton.vue'
import { resolveImageUrl } from '@/utils/assets'
import { useI18n } from 'vue-i18n'

const props = withDefaults(defineProps<{
  characters: any[]
  generatingItems: Record<string, number>
  enableMentionDrag?: boolean
}>(), {
  enableMentionDrag: true
})

const emit = defineEmits<{
  (e: 'delete', index: number, item: any): void
  (e: 'preview', index: number): void
  (e: 'add'): void
  (e: 'generate', type: 'image', item: any, index: number): void
  (e: 'upload-reference', item: any, index: number, file: File): void
}>()
const { t } = useI18n()

const pasteTargetIndex = ref<number | null>(null)
const uploadModalVisible = ref(false)
const uploadModalTargetIndex = ref<number | null>(null)
const uploadModalPreviewUrl = ref('')
const uploadModalExistingUrl = ref('')
const uploadModalFile = ref<File | null>(null)
const uploadModalInput = ref<HTMLInputElement | null>(null)

const setPasteTarget = (index: number) => {
  pasteTargetIndex.value = index
}

const handleDragStart = (event: DragEvent, char: any) => {
  if (!props.enableMentionDrag || !event.dataTransfer) return
  const payload = {
    type: 'character',
    id: String(char?.id || ''),
    name: String(char?.name || ''),
    role: String(char?.role || ''),
    description: String(char?.description || ''),
    image_url: String(char?.image_url || char?.reference_image || '')
  }
  event.dataTransfer.effectAllowed = 'copy'
  event.dataTransfer.setData('application/x-sky-mention', JSON.stringify(payload))
  event.dataTransfer.setData('text/x-sky-mention', JSON.stringify(payload))
  event.dataTransfer.setData('text/plain', `@${payload.name}`)
  event.dataTransfer.setData('text', `@${payload.name}`)
}

const clearUploadModalFile = () => {
  if (uploadModalPreviewUrl.value) {
    URL.revokeObjectURL(uploadModalPreviewUrl.value)
  }
  uploadModalPreviewUrl.value = ''
  uploadModalFile.value = null
  if (uploadModalInput.value) {
    uploadModalInput.value.value = ''
  }
}

const openUploadModal = (index: number) => {
  setPasteTarget(index)
  uploadModalTargetIndex.value = index
  clearUploadModalFile()
  const target = props.characters[index]
  uploadModalExistingUrl.value = target?.reference_image
    ? resolveImageUrl(target.reference_image)
    : ''
  uploadModalVisible.value = true
}

const closeUploadModal = () => {
  uploadModalVisible.value = false
  uploadModalTargetIndex.value = null
  uploadModalExistingUrl.value = ''
  clearUploadModalFile()
}

const setUploadModalFile = (file: File) => {
  clearUploadModalFile()
  uploadModalFile.value = file
  uploadModalPreviewUrl.value = URL.createObjectURL(file)
}

const triggerUploadModalSelect = () => {
  uploadModalInput.value?.click()
}

const handleUploadModalFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    setUploadModalFile(file)
  }
  if (target) {
    target.value = ''
  }
}

const confirmUploadModal = () => {
  const index = uploadModalTargetIndex.value
  const file = uploadModalFile.value
  if (index === null || !file) return
  const item = props.characters[index]
  if (!item) return
  emit('upload-reference', item, index, file)
  closeUploadModal()
}

const isEditableElement = (el: EventTarget | null): boolean => {
  const node = el as HTMLElement | null
  if (!node) return false
  const tag = node.tagName
  return tag === 'INPUT' || tag === 'TEXTAREA' || node.isContentEditable
}

const handlePaste = (event: ClipboardEvent) => {
  if (!uploadModalVisible.value) return
  if (isEditableElement(event.target) || isEditableElement(document.activeElement)) return

  const items = event.clipboardData?.items
  if (!items) return

  for (const item of items) {
    if (!item.type.startsWith('image/')) continue
    const file = item.getAsFile()
    if (!file) continue

    event.preventDefault()
    setUploadModalFile(file)
    break
  }
}

watch(
  () => props.characters.length,
  (len) => {
    if (len <= 0) {
      pasteTargetIndex.value = null
      return
    }
    if (pasteTargetIndex.value === null || pasteTargetIndex.value >= len) {
      pasteTargetIndex.value = 0
    }
  },
  { immediate: true }
)

onMounted(() => {
  window.addEventListener('paste', handlePaste)
})

onUnmounted(() => {
  window.removeEventListener('paste', handlePaste)
  clearUploadModalFile()
})
</script>

<template>
  <div class="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-5">
    <div
      v-for="(char, idx) in characters"
      :key="idx"
      class="neu-flat p-3 rounded-xl flex flex-col gap-3 group transition-all hover:bg-white/40 relative"
      :class="pasteTargetIndex === idx ? 'ring-1 ring-blue-300/80' : ''"
      @mouseenter="setPasteTarget(idx)"
      @mousedown.capture="setPasteTarget(idx)"
      :draggable="props.enableMentionDrag"
      @dragstart="(event) => handleDragStart(event, char)"
    >
      
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
              <span
                v-if="char.reference_image"
                class="text-[10px] px-1.5 py-0.5 rounded-md bg-blue-100/80 text-blue-600 font-medium border border-blue-200 shrink-0 text-center max-w-[60px] truncate cursor-pointer hover:bg-blue-200/80 transition-colors"
                :title="t('workbench.scriptCharacters.referenceImage')"
                @click.stop="openUploadModal(idx)"
              >
                  {{ t('workbench.scriptCharacters.reference') }}
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
              <NeuButton
                size="sm"
                class="flex-1 text-xs"
                @click="openUploadModal(idx)"
                :title="`${t('workbench.scriptCharacters.referenceImage')} (Ctrl+V)`"
                :aria-label="`${t('workbench.scriptCharacters.referenceImage')} (Ctrl+V)`"
              >
                  <Upload class="w-3.5 h-3.5" />
              </NeuButton>
              <NeuButton 
                size="sm"
                class="flex-1 text-xs"
                @click="emit('generate', 'image', char, idx)"
                :title="char.image_url ? t('workbench.scriptCharacters.resetImage') : t('workbench.scriptCharacters.generatePortrait')"
                :aria-label="char.image_url ? t('workbench.scriptCharacters.resetImage') : t('workbench.scriptCharacters.generatePortrait')"
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
       <span class="text-xs font-bold">{{ t('workbench.scriptCharacters.addCharacter') }}</span>
    </button>
  </div>

  <Teleport to="body">
    <div
      v-if="uploadModalVisible"
      class="fixed inset-0 z-[70] flex items-center justify-center bg-black/30 backdrop-blur-sm"
      @click.self="closeUploadModal"
    >
      <div class="w-[360px] max-w-[92vw] bg-[#fdfbf7] border border-gray-200 shadow-2xl rounded-xl p-4">
        <h4 class="text-base font-bold text-gray-700 mb-3">{{ t('workbench.scriptCharacters.uploadReferenceTitle') }}</h4>

        <div
          class="aspect-square rounded-lg overflow-hidden border border-gray-200 bg-gray-100 cursor-pointer"
          @click="triggerUploadModalSelect"
        >
          <img
            v-if="uploadModalPreviewUrl || uploadModalExistingUrl"
            :src="uploadModalPreviewUrl || uploadModalExistingUrl"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex flex-col items-center justify-center text-gray-400 gap-2">
            <Upload class="w-7 h-7" />
            <span class="text-xs font-semibold">{{ t('workbench.scriptCharacters.clickToSelectReference') }}</span>
          </div>
          <input
            ref="uploadModalInput"
            type="file"
            accept="image/*"
            class="hidden"
            @change="handleUploadModalFileChange"
          />
        </div>

        <p class="text-[11px] text-gray-500 mt-2">
          {{
            uploadModalExistingUrl && !uploadModalFile
              ? t('workbench.scriptCharacters.currentReferenceHint')
              : t('workbench.scriptCharacters.pasteHint')
          }}
        </p>

        <div class="mt-4 flex justify-end gap-2">
          <button
            class="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700"
            @click="closeUploadModal"
          >
            {{ t('common.cancel') }}
          </button>
          <NeuButton
            size="sm"
            :disabled="!uploadModalFile"
            @click="confirmUploadModal"
          >
            <Upload class="w-3.5 h-3.5 mr-1" />
            {{ t('workbench.scriptCharacters.uploadAction') }}
          </NeuButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>
