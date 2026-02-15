<script setup lang="ts">
import { computed, ref, reactive } from 'vue'
import { User, MapPin } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  text: string
  characters: any[]
  scenes: any[]
}>()
const { t } = useI18n()

// Tooltip State
const tooltipVisible = ref(false)
const tooltipData = ref<any>(null)
const tooltipPos = reactive({ x: 0, y: 0 })

const showTooltip = (e: MouseEvent, data: any) => {
    const target = e.currentTarget as HTMLElement
    const rect = target.getBoundingClientRect()
    
    tooltipData.value = data
    // Position above the element centered
    tooltipPos.x = rect.left + rect.width / 2
    tooltipPos.y = rect.top - 8 // 8px gap
    
    tooltipVisible.value = true
}

const hideTooltip = () => {
    tooltipVisible.value = false
}

const parts = computed(() => {
  if (!props.text) return []
  // Regex to match {{char_ID}} or {{scene_ID}}
  const regex = /(\{\{(?:char|scene)_[a-zA-Z0-9_]+\}\})/g
  const split = props.text.split(regex)
  
  return split.map(part => {
    if (part.startsWith('{{char_')) {
      // Extract content inside {{ }}
      const fullId = part.slice(2, -2)
      // Find by matching ID directly (assuming ID in data includes prefix)
      let char = props.characters.find(c => c.id == fullId)
      
      return {
        type: 'character',
        content: part,
        data: char,
        label: char ? char.name : t('workbench.smartText.unknownCharacter')
      }
    } else if (part.startsWith('{{scene_')) {
      const fullId = part.slice(2, -2)
      let scene = props.scenes.find(s => s.id == fullId)
      
      return {
        type: 'scene',
        content: part,
        data: scene,
        label: scene ? scene.location_name : t('workbench.smartText.unknownScene')
      }
    } else {
      return {
        type: 'text',
        content: part
      }
    }
  })
})
</script>

<template>
  <div class="smart-text whitespace-pre-wrap font-mono text-base leading-relaxed text-gray-600">
    <template v-for="(part, idx) in parts" :key="idx">
      <!-- Character Tag -->
      <span 
        v-if="part.type === 'character'" 
        class="inline-flex items-center gap-1 px-1.5 py-0.5 mx-0.5 rounded-md text-xs font-bold bg-blue-100 text-blue-600 border border-blue-200 shadow-sm cursor-help transition-transform hover:scale-105 select-none"
        @mouseenter="(e) => showTooltip(e, part)"
        @mouseleave="hideTooltip"
      >
        <User class="w-3 h-3" />
        {{ part.label }}
      </span>

      <!-- Scene Tag -->
      <span 
        v-else-if="part.type === 'scene'" 
        class="inline-flex items-center gap-1 px-1.5 py-0.5 mx-0.5 rounded-md text-xs font-bold bg-orange-100 text-orange-600 border border-orange-200 shadow-sm cursor-help transition-transform hover:scale-105 select-none"
        @mouseenter="(e) => showTooltip(e, part)"
        @mouseleave="hideTooltip"
      >
        <MapPin class="w-3 h-3" />
        {{ part.label }}
      </span>

      <!-- Normal Text -->
      <span v-else>{{ part.content }}</span>
    </template>

    <!-- Global Teleported Tooltip -->
    <Teleport to="body">
        <transition name="pop">
            <div 
                v-if="tooltipVisible && tooltipData"
                class="fixed z-[10000] p-4 rounded-xl w-64 pointer-events-none flex flex-col gap-3 glass-panel"
                :style="{ 
                    left: tooltipPos.x + 'px', 
                    top: tooltipPos.y + 'px',
                    transform: 'translate(-50%, -100%)'
                }"
            >
                <!-- Header -->
                <div class="flex items-start gap-3 border-b border-gray-200/50 pb-3">
                    <!-- Avatar/Image -->
                    <div 
                        class="w-12 h-12 rounded-lg shadow-sm overflow-hidden shrink-0 border border-white/60 bg-gray-50 flex items-center justify-center"
                        :class="tooltipData.type === 'character' ? 'text-blue-200' : 'text-orange-200'"
                    >
                        <img v-if="tooltipData.data?.image_url" :src="tooltipData.data.image_url" class="w-full h-full object-cover" />
                        <User v-else-if="tooltipData.type === 'character'" class="w-6 h-6" />
                        <MapPin v-else class="w-6 h-6" />
                    </div>
                    
                    <div class="min-w-0 flex-1">
                        <div 
                            class="font-bold text-base truncate leading-tight drop-shadow-sm"
                            :class="tooltipData.type === 'character' ? 'text-blue-600' : 'text-orange-600'"
                        >
                            {{ tooltipData.data?.name || tooltipData.data?.location_name || t('workbench.smartText.unknown') }}
                        </div>
                        <div class="text-[10px] uppercase font-bold tracking-wider text-gray-400 mt-1">
                            <span v-if="tooltipData.type === 'scene'">{{ t('workbench.smartText.scene') }}</span>
                            <span v-else>{{ tooltipData.data.role }}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Content -->
                <div v-if="tooltipData.type === 'character'" class="text-xs text-gray-600 leading-relaxed font-medium">
                     {{ tooltipData.data?.description || tooltipData.data?.mood || t('workbench.smartText.noDetails') }}
                </div>
            </div>
        </transition>
    </Teleport>
  </div>
</template>

<style scoped>
.glass-panel {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.6);
    box-shadow: 
        0 4px 6px -1px rgba(0, 0, 0, 0.05),
        0 10px 15px -3px rgba(0, 0, 0, 0.05),
        0 0 0 1px rgba(255, 255, 255, 0.5) inset;
}

.pop-enter-active, .pop-leave-active {
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.pop-enter-from, .pop-leave-to {
    opacity: 0;
    transform: translate(-50%, -90%) scale(0.95);
}
</style>
