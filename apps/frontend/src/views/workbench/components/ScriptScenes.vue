<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { Trash2, MapPin, Maximize2, Image as ImageIcon, Plus, Upload } from 'lucide-vue-next'
import NeuButton from '@/components/base/NeuButton.vue'
import { resolveImageUrl } from '@/utils/assets'
import { useI18n } from 'vue-i18n'

const props = withDefaults(defineProps<{
  scenes: any[]
  generatingItems: Record<string, number>
  enableMentionDrag?: boolean
}>(), {
  enableMentionDrag: true
})

const emit = defineEmits<{
  (e: 'delete', index: number, item: any): void
  (e: 'edit', item: any): void
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

const handleDragStart = (event: DragEvent, scene: any) => {
  if (!props.enableMentionDrag || !event.dataTransfer) return
  const payload = {
    type: 'scene',
    id: String(scene?.id || ''),
    name: String(scene?.location_name || ''),
    mood: String(scene?.mood || ''),
    description: String(scene?.description || ''),
    image_url: String(scene?.image_url || scene?.reference_image || '')
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
  const target = props.scenes[index]
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
  const item = props.scenes[index]
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
  () => props.scenes.length,
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
  <div class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-5">
      <div
        v-for="(scene, idx) in scenes"
        :key="idx"
        class="neu-flat p-3 rounded-xl transition-transform flex flex-col relative group"
        :class="pasteTargetIndex === idx ? 'ring-1 ring-orange-300/80' : ''"
        @mouseenter="setPasteTarget(idx)"
        @mousedown.capture="setPasteTarget(idx)"
        :draggable="props.enableMentionDrag"
        @dragstart="(event) => handleDragStart(event, scene)"
      >
          <button
              class="absolute top-2 right-2 p-1.5 rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100 z-10"
              @click.stop="emit('delete', idx, scene)"
          >
              <Trash2 class="w-3.5 h-3.5" />
          </button>
            <div class="flex items-center justify-between mb-2 mr-6">
              <div class="flex items-center gap-2 cursor-pointer hover:bg-black/5 rounded px-1 transition-colors" @click="emit('edit', scene)" :title="t('workbench.scriptScenes.clickToEdit')">
                  <MapPin class="w-4 h-4 text-orange-500" />
                  <span class="text-xs font-bold text-gray-700 truncate max-w-[140px]">{{ scene.location_name }}</span>
              </div>
              <span class="text-[10px] font-bold text-gray-400">{{ t('workbench.scriptScenes.sceneNumber', { number: idx + 1 }) }}</span>
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
                {{ t('workbench.scriptScenes.noImage') }}
             </div>

             <div
               v-if="scene.reference_image"
               class="absolute top-2 left-2 px-2 py-0.5 text-[10px] font-semibold bg-orange-100/90 text-orange-700 border border-orange-200 rounded cursor-pointer hover:bg-orange-200/90 transition-colors"
               :title="t('workbench.scriptScenes.referenceImage')"
               @click.stop="openUploadModal(idx)"
             >
                {{ t('workbench.scriptScenes.reference') }}
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
                  <NeuButton
                    size="sm"
                    class="flex-1 text-xs"
                    @click="openUploadModal(idx)"
                    :title="`${t('workbench.scriptScenes.referenceImage')} (Ctrl+V)`"
                    :aria-label="`${t('workbench.scriptScenes.referenceImage')} (Ctrl+V)`"
                  >
                     <Upload class="w-3.5 h-3.5" />
                  </NeuButton>
                  <NeuButton
                    size="sm"
                    class="flex-1 text-xs"
                    @click="emit('generate', 'image', scene, idx)"
                    :title="scene.image_url ? t('workbench.scriptScenes.resetImage') : t('workbench.scriptScenes.generateSceneImage')"
                    :aria-label="scene.image_url ? t('workbench.scriptScenes.resetImage') : t('workbench.scriptScenes.generateSceneImage')"
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
         <span class="text-xs font-bold">{{ t('workbench.scriptScenes.addScene') }}</span>
      </button>
  </div>

  <Teleport to="body">
    <div
      v-if="uploadModalVisible"
      class="fixed inset-0 z-[70] flex items-center justify-center bg-black/30 backdrop-blur-sm"
      @click.self="closeUploadModal"
    >
      <div class="w-[360px] max-w-[92vw] bg-[#fdfbf7] border border-gray-200 shadow-2xl rounded-xl p-4">
        <h4 class="text-base font-bold text-gray-700 mb-3">{{ t('workbench.scriptScenes.uploadReferenceTitle') }}</h4>

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
            <span class="text-xs font-semibold">{{ t('workbench.scriptScenes.clickToSelectReference') }}</span>
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
              ? t('workbench.scriptScenes.currentReferenceHint')
              : t('workbench.scriptScenes.pasteHint')
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
            {{ t('workbench.scriptScenes.uploadAction') }}
          </NeuButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>
