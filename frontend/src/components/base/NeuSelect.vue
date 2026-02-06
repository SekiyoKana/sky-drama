<script setup lang="ts">
    import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
    import { ChevronDown, Check, Search } from 'lucide-vue-next'
    
    const props = defineProps<{
      modelValue: string | number
      options: Array<{ label: string, value: string | number }> | string[]
      placeholder?: string
      disabled?: boolean
    }>()
    
    const emit = defineEmits(['update:modelValue'])
    
    const isOpen = ref(false)
    const containerRef = ref<HTMLElement | null>(null)
    const dropdownStyle = ref({ top: '0px', left: '0px', width: '0px' })
    const searchQuery = ref('')
    
    // 1. 统一数据格式
    const formattedOptions = computed(() => {
      return props.options.map(opt => {
        if (typeof opt === 'object') return opt
        return { label: opt, value: opt }
      })
    })
    
    // 2. 搜索过滤
    const filteredOptions = computed(() => {
      if (!searchQuery.value) return formattedOptions.value
      return formattedOptions.value.filter(opt => 
        String(opt.label).toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    })
    
    const currentLabel = computed(() => {
      const found = formattedOptions.value.find(o => o.value === props.modelValue)
      return found ? found.label : props.placeholder || 'Select...'
    })
    
    // 3. 计算绝对位置 (防止父级 overflow:hidden 遮挡)
    const updatePosition = () => {
      if (containerRef.value) {
        const rect = containerRef.value.getBoundingClientRect()
        dropdownStyle.value = {
          top: `${rect.bottom + window.scrollY + 8}px`, // 向下偏移一点
          left: `${rect.left + window.scrollX}px`,
          width: `${rect.width}px`
        }
      }
    }
    
    const toggle = async () => {
      if (!props.disabled) {
        isOpen.value = !isOpen.value
        if (isOpen.value) {
          searchQuery.value = '' 
          await nextTick()
          updatePosition()
        }
      }
    }
    
    const select = (value: string | number) => {
      emit('update:modelValue', value)
      isOpen.value = false
    }
    
    // 4. 点击外部关闭逻辑
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      const dropdownEl = document.getElementById('neu-select-dropdown')
      
      // 如果点击的既不是触发按钮内部，也不是下拉框内部
      if (containerRef.value && !containerRef.value.contains(target)) {
        if (dropdownEl && !dropdownEl.contains(target)) {
          isOpen.value = false
        }
      }
    }
    
    onMounted(() => {
      document.addEventListener('click', handleClickOutside)
      window.addEventListener('resize', updatePosition)
      window.addEventListener('scroll', updatePosition, true)
    })
    onUnmounted(() => {
      document.removeEventListener('click', handleClickOutside)
      window.removeEventListener('resize', updatePosition)
      window.removeEventListener('scroll', updatePosition, true)
    })
    </script>
    
    <template>
      <div ref="containerRef" class="relative w-full font-serif">
        <div 
          @click="toggle"
          class="flex items-center justify-between px-4 py-3 rounded-xl cursor-pointer transition-all border border-transparent select-none bg-white shadow-sm"
          :class="[
            disabled ? 'opacity-50 cursor-not-allowed bg-gray-50' : 
            isOpen ? 'ring-2 ring-blue-100 border-blue-300 text-blue-600' : 'hover:border-gray-300 text-gray-700 border-gray-200'
          ]"
        >
          <span class="text-sm font-bold truncate">{{ currentLabel }}</span>
          <ChevronDown 
            class="w-4 h-4 transition-transform duration-300 text-gray-400"
            :class="{ 'rotate-180': isOpen }"
          />
        </div>
    
        <Teleport to="body">
          <transition name="dropdown">
            <div 
              v-if="isOpen"
              id="neu-select-dropdown" 
              class="fixed z-[9999] bg-[#E0E5EC] rounded-xl neu-flat overflow-hidden flex flex-col"
              :style="dropdownStyle"
            >
              <div class="p-2 border-b border-gray-200/50">
                <div class="relative">
                  <Search class="w-3 h-3 absolute left-2 top-2.5 text-gray-400" />
                  <input 
                    v-model="searchQuery"
                    type="text" 
                    placeholder="Search model..." 
                    class="w-full bg-gray-100/50 rounded-lg py-1.5 pl-7 pr-2 text-xs font-bold text-gray-600 outline-none focus:bg-white transition-colors"
                    @click.stop
                  />
                </div>
              </div>
    
              <div class="max-h-60 overflow-y-auto custom-scroll p-2 space-y-1">
                <div 
                  v-for="opt in filteredOptions" 
                  :key="opt.value"
                  @click="select(opt.value)"
                  class="flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-all text-xs font-bold"
                  :class="modelValue === opt.value ? 'neu-pressed-sm text-blue-600' : 'hover:bg-gray-200/50 text-gray-600'"
                >
                  <span class="truncate">{{ opt.label }}</span>
                  <Check v-if="modelValue === opt.value" class="w-3 h-3 shrink-0 ml-2" />
                </div>
                
                <div v-if="filteredOptions.length === 0" class="p-4 text-center text-xs text-gray-400 font-mono">
                  No results
                </div>
              </div>
            </div>
          </transition>
        </Teleport>
      </div>
    </template>
    
    <style scoped>
    .dropdown-enter-active, .dropdown-leave-active { transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1); }
    .dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(-10px) scale(0.98); }
    
    /* 定制细滚动条 */
    .custom-scroll::-webkit-scrollbar { width: 4px; }
    .custom-scroll::-webkit-scrollbar-track { background: transparent; }
    .custom-scroll::-webkit-scrollbar-thumb { background-color: #cbd5e0; border-radius: 4px; }
    .custom-scroll::-webkit-scrollbar-thumb:hover { background-color: #a0aec0; }
    
    .neu-flat { background: #E0E5EC; box-shadow: 5px 5px 15px rgba(163,177,198,0.6), -5px -5px 15px rgba(255,255,255, 0.5); }
    .neu-pressed-sm { background: #E0E5EC; box-shadow: inset 2px 2px 5px rgba(163,177,198,0.6), inset -2px -2px 5px rgba(255,255,255, 0.8); }
    </style>