<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { User, MapPin } from 'lucide-vue-next'

const props = defineProps<{
  visible: boolean
  x: number
  y: number
  filterText: string
  items: Array<{ id: number | string, name: string, type: 'character' | 'scene', image_url?: string }>
}>()

const emit = defineEmits(['select', 'close'])

const activeIndex = ref(0)
const containerRef = ref<HTMLElement | null>(null)

const filteredItems = computed(() => {
  const query = props.filterText.toLowerCase()
  return props.items.filter(item => 
    item.name.toLowerCase().includes(query)
  )
})

watch(() => props.filterText, () => {
  activeIndex.value = 0
})

watch(() => props.visible, (val) => {
    if (val) {
        activeIndex.value = 0
        // Reset scroll position when showing
        if (containerRef.value) containerRef.value.scrollTop = 0
    }
})

const handleKeydown = (e: KeyboardEvent) => {
  if (!props.visible) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    activeIndex.value = (activeIndex.value + 1) % filteredItems.value.length
    scrollToActive()
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    activeIndex.value = (activeIndex.value - 1 + filteredItems.value.length) % filteredItems.value.length
    scrollToActive()
  } else if (e.key === 'Enter' || e.key === 'Tab') {
    e.preventDefault()
    selectItem(filteredItems.value[activeIndex.value])
  } else if (e.key === 'Escape') {
    e.preventDefault()
    emit('close')
  }
}

const selectItem = (item: any) => {
  if (item) {
    emit('select', item)
  }
}

const scrollToActive = () => {
  if (!containerRef.value) return
  const activeEl = containerRef.value.children[activeIndex.value] as HTMLElement
  if (activeEl) {
    const containerTop = containerRef.value.scrollTop
    const containerBottom = containerTop + containerRef.value.clientHeight
    const elTop = activeEl.offsetTop
    const elBottom = elTop + activeEl.offsetHeight
    
    if (elTop < containerTop) {
      containerRef.value.scrollTop = elTop
    } else if (elBottom > containerBottom) {
      containerRef.value.scrollTop = elBottom - containerRef.value.clientHeight
    }
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown, true) // Capture phase to prevent textarea default
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown, true)
})
</script>

<template>
  <Teleport to="body">
    <div 
      v-show="visible && filteredItems.length > 0"
      class="fixed z-[10000] bg-[#E0E5EC] rounded-xl shadow-[6px_6px_12px_#b8b9be,-6px_-6px_12px_#ffffff] border border-white/20 w-64 max-h-64 overflow-hidden flex flex-col"
      :style="{ left: x + 'px', top: y + 'px' }"
    >
      <div class="px-3 py-2 text-[10px] font-bold text-gray-400 uppercase tracking-wider border-b border-gray-200/50">
          Mention...
      </div>
      <div 
        ref="containerRef"
        class="overflow-y-auto custom-scroll flex-1 p-1"
      >
        <button
          v-for="(item, index) in filteredItems"
          :key="item.type + item.id"
          class="w-full text-left px-3 py-2 rounded-lg flex items-center gap-3 transition-all text-sm group"
          :class="index === activeIndex ? 'neu-pressed text-gray-800' : 'hover:bg-white/40 text-gray-600'"
          @click="selectItem(item)"
          @mousemove="activeIndex = index"
        >
          <!-- Icon/Avatar -->
          <div 
            class="w-6 h-6 rounded-full flex items-center justify-center shrink-0 border border-white/50 overflow-hidden shadow-sm"
            :class="item.type === 'character' ? 'bg-blue-100' : 'bg-orange-100'"
          >
             <img v-if="item.image_url" :src="item.image_url" class="w-full h-full object-cover" />
             <User v-else-if="item.type === 'character'" class="w-3.5 h-3.5 text-blue-500" />
             <MapPin v-else class="w-3.5 h-3.5 text-orange-500" />
          </div>
          
          <div class="flex-1 min-w-0">
              <div class="font-bold truncate leading-tight">{{ item.name }}</div>
              <div class="text-[10px] text-gray-400 truncate">{{ item.type === 'character' ? 'Character' : 'Scene' }}</div>
          </div>
        </button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.custom-scroll::-webkit-scrollbar { width: 4px; }
.custom-scroll::-webkit-scrollbar-thumb { background-color: #cbd5e0; border-radius: 4px; }
.neu-pressed {
    background: #E0E5EC;
    box-shadow: inset 2px 2px 5px #b8b9be, inset -3px -3px 7px #ffffff;
}
</style>
