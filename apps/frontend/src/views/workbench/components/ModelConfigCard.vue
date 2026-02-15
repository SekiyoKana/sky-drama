<script setup lang="ts">
  import { ref, watch, onMounted, onUnmounted, reactive, computed } from 'vue'
  import { Type, Image, Video, Save, Cpu, CheckCircle2, X, Palette } from 'lucide-vue-next'
  import { apiKeyApi, aiApi, styleApi } from '@/api'
  import NeuButton from '@/components/base/NeuButton.vue'
  import NeuSelect from '@/components/base/NeuSelect.vue'
  import NeuSwitch from '@/components/base/NeuSwitch.vue'
  import { useI18n } from 'vue-i18n'
  
  const props = defineProps<{
    initialConfig?: any
    visible: boolean
  }>()
  
  const emit = defineEmits(['close', 'save', 'handle-down'])
  const { t } = useI18n()
  
  // --- Window State (Draggable & Resizable) ---
  const windowState = reactive({
    x: window.innerWidth - 340,
    y: 150,
    w: 320,
    h: 650
  })

  // --- Drag Logic ---
  let isDragging = false
  let dragOffset = { x: 0, y: 0 }

  const startDrag = (e: MouseEvent) => {
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
    const newW = Math.max(300, e.clientX - windowState.x)
    const newH = Math.max(400, e.clientY - windowState.y)
    windowState.w = Math.min(newW, window.innerWidth - windowState.x)
    windowState.h = Math.min(newH, window.innerHeight - windowState.y)
  }

  const stopResize = () => {
    isResizing = false
    document.removeEventListener('mousemove', onResize)
    document.removeEventListener('mouseup', stopResize)
  }
  
  // 状态管理
  const activeTab = ref<'text'|'image'|'video'|'audio'|'style'>('text')
  const loadingKeys = ref(false)
  const fetchingModels = ref(false)
  const availableKeys = ref<any[]>([]) 
  const modelOptions = ref<string[]>([]) 
  const availableStyles = ref<any[]>([])
  const modelCache = ref<Record<string, string[]>>({})
  const voiceLanguageOptions = computed(() => [
    { label: t('workbench.modelConfig.voiceLanguages.unspecified'), value: '' },
    { label: t('workbench.modelConfig.voiceLanguages.chinese'), value: '汉语' },
    { label: t('workbench.modelConfig.voiceLanguages.english'), value: '英语' },
    { label: t('workbench.modelConfig.voiceLanguages.japanese'), value: '日语' },
    { label: t('workbench.modelConfig.voiceLanguages.korean'), value: '韩语' },
    { label: t('workbench.modelConfig.voiceLanguages.french'), value: '法语' },
    { label: t('workbench.modelConfig.voiceLanguages.german'), value: '德语' },
    { label: t('workbench.modelConfig.voiceLanguages.spanish'), value: '西语' }
  ])
  
  const config = ref<any>({
    text: { key_id: '', model: '' },
    image: { key_id: '', model: '' },
    video: { key_id: '', model: '', remove_bgm: true, keep_voice: true, keep_sfx: true, voice_language: '' },
    audio: { key_id: '', model: '' },
    style: { id: null }
  })
  
  const tabs = computed(() => [
    { id: 'text', label: t('workbench.modelConfig.tabs.script'), icon: Type, color: 'text-blue-600' },
    { id: 'image', label: t('workbench.modelConfig.tabs.image'), icon: Image, color: 'text-purple-600' },
    { id: 'video', label: t('workbench.modelConfig.tabs.video'), icon: Video, color: 'text-orange-600' },
    // { id: 'audio', label: '声音', icon: Music, color: 'text-green-600' },
    { id: 'style', label: t('workbench.modelConfig.tabs.style'), icon: Palette, color: 'text-pink-600' },
  ])
  
  const fetchModels = async (keyId: string) => {
    modelOptions.value = [] 
    if (!keyId) return
  
    if (modelCache.value[keyId]) {
      modelOptions.value = modelCache.value[keyId]
      return
    }
  
    fetchingModels.value = true
    try {
      const res: any = await aiApi.testConnection(Number(keyId))
      if (res.models && Array.isArray(res.models)) {
        modelOptions.value = res.models
        modelCache.value[keyId] = res.models
      }
    } catch (e) {
      console.error('Fetch Models Failed', e)
    } finally {
      fetchingModels.value = false
    }
  }

  watch(() => props.initialConfig, (newVal) => {
    if (newVal) {
      config.value = {
        text: { ...config.value.text, ...(newVal.text || {}) },
        image: { ...config.value.image, ...(newVal.image || {}) },
        video: { ...config.value.video, ...(newVal.video || {}) },
        audio: { ...config.value.audio, ...(newVal.audio || {}) },
        style: { ...config.value.style, ...(newVal.style || {}) }
      }

      if (newVal.video && newVal.video.keep_voice_sfx !== undefined) {
        if (newVal.video.keep_voice === undefined) config.value.video.keep_voice = !!newVal.video.keep_voice_sfx
        if (newVal.video.keep_sfx === undefined) config.value.video.keep_sfx = !!newVal.video.keep_voice_sfx
      }
    }
  }, { immediate: true, deep: true })
  
  // 2. 监听 Tab 切换或当前 Tab 的 Key 变化
  watch([() => activeTab.value, () => config.value[activeTab.value]?.key_id], ([newTab, newKey], [oldTab, oldKey]) => {
    if (newTab === 'style') return // Style tab doesn't use keys
    if (newKey !== oldKey || newTab !== oldTab) {
      fetchModels(newKey)
    }
  })
  
  onMounted(async () => {
    document.addEventListener('mousemove', onDrag)
    
    loadingKeys.value = true
    try {
      const [keysRes, stylesRes]: [any, any] = await Promise.all([
          apiKeyApi.list(),
          styleApi.list()
      ])
      
      availableKeys.value = keysRes.map((k: any) => ({ 
        label: `${k.name} (${k.platform})`, 
        value: k.id 
      }))

      availableStyles.value = stylesRes.map((s: any) => ({
          label: s.name,
          value: s.id,
          image_url: s.image_url
      }))

    } finally {
      loadingKeys.value = false
    }
  })
  
  onUnmounted(() => {
    document.removeEventListener('mousemove', onDrag)
    document.removeEventListener('mouseup', stopDrag)
    document.removeEventListener('mousemove', onResize)
    document.removeEventListener('mouseup', stopResize)
  })
  
  // 4. 保存逻辑
  const handleSave = () => {
    emit('save', JSON.parse(JSON.stringify(config.value)))
  }
  </script>
  
  <template>
    <transition name="pop-up">
      <div 
        v-if="visible" 
        ref="cardRef"
        class="fixed z-40 bg-[#E0E5EC] rounded-3xl flex flex-col overflow-hidden shadow-2xl border border-white/40 font-sans text-xs text-gray-600"
        :style="{ left: windowState.x + 'px', top: windowState.y + 'px', width: windowState.w + 'px', height: windowState.h + 'px' }"
      >
        <!-- Header -->
        <div 
            class="px-4 py-3 bg-[#E0E5EC] border-b border-gray-200/40 flex items-center justify-between cursor-move select-none shrink-0" 
            @mousedown="startDrag"
        >
            <div class="flex items-center gap-2 text-gray-500">
                <Cpu class="w-4 h-4 text-blue-500" />
                <span class="font-bold font-serif text-sm tracking-wide uppercase">{{ t('workbench.modelConfig.title') }}</span>
            </div>
            <button @click="emit('close')" class="p-1.5 rounded-full neu-flat hover:text-red-500 active:neu-pressed transition-all text-gray-400" @mousedown.stop>
                <X class="w-3.5 h-3.5" />
            </button>
        </div>

        <!-- Tabs -->
        <div class="flex p-2 mb-3 gap-1 bg-[#E0E5EC] shrink-0">
          <button 
            v-for="t in tabs" 
            :key="t.id"
            @click="activeTab = t.id as any"
            class="flex-1 py-2 rounded-lg flex flex-col items-center justify-center gap-1 transition-all text-[10px] font-bold uppercase tracking-wider"
            :class="activeTab === t.id ? 'neu-pressed ' + t.color : 'neu-flat text-gray-400 hover:text-gray-600'"
          >
            <component :is="t.icon" class="w-4 h-4" />
            {{ t.label }}
          </button>
        </div>

        <!-- Content Area -->
        <div class="flex-1 bg-[#E0E5EC] overflow-hidden flex flex-col relative">
            
          <!-- Style Tab Content -->
          <div v-if="activeTab === 'style'" class="h-full flex flex-col">
              <div class="px-5 pt-5 pb-3 shrink-0">
                <label class="text-xs font-bold text-gray-500 uppercase">{{ t('workbench.modelConfig.selectStyle') }}</label>
              </div>
              
              <div class="grid grid-cols-3 gap-3 overflow-y-auto px-5 pb-5 custom-scroll min-h-0 flex-1 content-start">
                  <div 
                    v-for="style in availableStyles" 
                    :key="style.value"
                    class="aspect-square h-full rounded-xl relative overflow-hidden cursor-pointer border-2 transition-all group hover:shadow-md shrink-0"
                    :class="config.style.id === style.value ? 'border-blue-500 ring-2 ring-blue-200 shadow-lg' : 'border-gray-200 hover:border-blue-300'"
                    @click="config.style.id = style.value"
                  >
                      <img :src="style.image_url" class="w-full h-full object-cover" />
                      <div class="absolute inset-x-0 bottom-0 bg-linear-to-t from-black/70 to-transparent p-2 text-center">
                          <span class="text-[10px] text-white font-bold truncate block drop-shadow">{{ style.label }}</span>
                      </div>
                      <div v-if="config.style.id === style.value" class="absolute top-1 right-1 bg-blue-500 text-white rounded-full p-1 shadow-lg">
                          <CheckCircle2 class="w-3 h-3" />
                      </div>
                  </div>
                  
                  <div 
                    class="aspect-square rounded-xl border-2 border-dashed flex flex-col items-center justify-center gap-2 text-gray-400 cursor-pointer hover:bg-gray-100/50 hover:border-gray-400 transition-all shrink-0"
                    :class="!config.style.id ? 'border-blue-500 ring-2 ring-blue-200 bg-blue-50/50 shadow-lg' : 'border-gray-300'"
                    @click="config.style.id = null"
                  >
                      <X class="w-6 h-6" />
                      <span class="text-[10px] font-bold">{{ t('workbench.modelConfig.noStyle') }}</span>
                  </div>
              </div>
          </div>

          <!-- Model Config Content (Text/Image/Video/Audio) -->
          <div v-else class="h-full overflow-y-auto p-5 space-y-6 custom-scroll">
            <div class="space-y-2">
              <label class="text-xs font-bold text-gray-500 uppercase flex justify-between">
                {{ t('workbench.modelConfig.apiConnection') }} <span v-if="loadingKeys" class="animate-pulse">{{ t('workbench.modelConfig.loading') }}</span>
              </label>
              <NeuSelect 
                v-model="config[activeTab].key_id" 
                :options="availableKeys" 
                :placeholder="t('workbench.modelConfig.selectConnection')" 
                size="mini"
              />
            </div>
  
            <div class="space-y-2">
              <label class="text-xs font-bold text-gray-500 uppercase flex justify-between">
                {{ t('workbench.modelConfig.targetModel') }} <span v-if="fetchingModels" class="text-blue-500 animate-pulse">{{ t('workbench.modelConfig.fetching') }}</span>
              </label>
              <NeuSelect 
                v-model="config[activeTab].model" 
                :options="modelOptions" 
                :disabled="!config[activeTab].key_id || fetchingModels"
                :placeholder="t('workbench.modelConfig.autoDefault')"
                size="mini"
              />
              
              <div v-if="config[activeTab].model" class="flex items-center gap-1.5 text-[10px] text-green-600 bg-green-50 px-2 py-1 rounded border border-green-100 animate-in fade-in slide-in-from-top-1 mt-2">
                <CheckCircle2 class="w-3 h-3" /> {{ t('workbench.modelConfig.ready') }}
              </div>
            </div>

            <div v-if="activeTab === 'video'" class="space-y-3">
              <div class="space-y-2 mb-6">
                <label class="text-xs font-bold text-gray-500 uppercase">{{ t('workbench.modelConfig.voiceLanguage') }}</label>
                <NeuSelect
                    v-model="config.video.voice_language"
                    :options="voiceLanguageOptions"
                    :placeholder="t('workbench.modelConfig.voiceLanguagePlaceholder')"
                    size="mini"
                    class="mt-2"
                  />
              </div>

              <div class="space-y-2">
                <label class="text-xs font-bold text-gray-500 uppercase">{{ t('workbench.modelConfig.videoPrompt') }}</label>
                <div class="neu-flat rounded-xl p-3 flex flex-col gap-3 border border-white/40 mt-2">
                  <NeuSwitch v-model="config.video.remove_bgm" :label="t('workbench.modelConfig.removeBgm')" />
                  <NeuSwitch v-model="config.video.keep_voice" :label="t('workbench.modelConfig.keepVoice')" />
                  <NeuSwitch v-model="config.video.keep_sfx" :label="t('workbench.modelConfig.keepSfx')" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="p-4 border-t border-gray-200/40 bg-[#E0E5EC] flex justify-end relative shrink-0">
          <NeuButton size="xs" variant="primary" @click="handleSave" class="text-xs px-3 py-1.5">
            <Save class="w-3 h-3 mr-1.5" /> {{ t('common.save') }}
          </NeuButton>
          
          <div 
            class="absolute bottom-0 right-0 w-6 h-6 cursor-nwse-resize flex items-end justify-end p-1 text-gray-400 hover:text-gray-600 z-10" 
            @mousedown="startResize"
          >
              <svg viewBox="0 0 24 24" class="w-full h-full fill-current opacity-50"><path d="M22 22H20V20H22V22ZM22 18H20V16H22V18ZM18 22H16V20H18V22ZM18 18H16V16H18V18Z" /></svg>
          </div>
        </div>

      </div>
    </transition>
  </template>
  
  <style scoped>
  .custom-scroll::-webkit-scrollbar { width: 4px; }
  .custom-scroll::-webkit-scrollbar-thumb { background-color: #cbd5e0; border-radius: 4px; border: 1px solid #E0E5EC; }
  
  .pop-up-enter-active, .pop-up-leave-active { transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
  .pop-up-enter-from, .pop-up-leave-to { opacity: 0; transform: scale(0.9) translateY(-10px); }
  </style>
