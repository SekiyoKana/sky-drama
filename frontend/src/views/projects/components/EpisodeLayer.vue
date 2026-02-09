<script setup lang="ts">
  import { ref, watch, nextTick, reactive } from 'vue'
  import { useRouter } from 'vue-router'
  import { 
    ArrowLeft, Calendar, Plus, Play, 
    Trash2, X, Check, Pencil, FileText 
  } from 'lucide-vue-next'
  import NeuButton from '@/components/base/NeuButton.vue'
  import { episodeApi } from '@/api'
  import { useMessage } from '@/utils/useMessage'
  import BookPreview from '../../workbench/components/BookPreview.vue'
  import StoryArchiveModal from './StoryArchiveModal.vue'
  
  const props = defineProps<{
    project: any | null
  }>()
  
  const emit = defineEmits(['back'])
  const router = useRouter()
  const message = useMessage()
  
  // --- 数据状态 ---
  const episodes = ref<any[]>([])
  const loading = ref(false)
  const isAdding = ref(false)
  const editingId = ref<number | null>(null)
  const tempTitle = ref('')
  const inputRef = ref<HTMLInputElement | null>(null)
  const deleteConfirmId = ref<number | null>(null)
  const scribblingId = ref<number | null>(null)
  
  // --- Preview State ---
  const previewVisible = ref(false)
  const previewList = ref<any[]>([])
  const previewIndex = ref(0)
  
  const archiveVisible = ref(false)

  const openPreview = (items: any[], index: number) => {
      previewList.value = items
      previewIndex.value = index
      previewVisible.value = true
  }

  // --- 🆕 独立的转场动画状态 ---
  const transitionState = reactive({
    active: false,
    originRect: null as DOMRect | null, // 记录原始位置
    style: {
      top: '0px',
      left: '0px',
      width: '0px',
      height: '0px',
      opacity: 1,
      borderRadius: '12px'
    }
  })
  
  const getEpisodeDuration = (ep: any) => {
      // 1. Try to get from AI config's timeline data
      if (ep.ai_config && ep.ai_config.timeline_data) {
          const mainTrack = ep.ai_config.timeline_data.find((t: any) => t.id === 1 || t.type === 'video')
          if (mainTrack && mainTrack.items && mainTrack.items.length > 0) {
              const totalSeconds = mainTrack.items.reduce((acc: number, item: any) => acc + (item.duration || 0), 0)
              
              if (totalSeconds > 0) {
                  const m = Math.floor(totalSeconds / 60).toString().padStart(2, '0')
                  const s = Math.floor(totalSeconds % 60).toString().padStart(2, '0')
                  return `${m}:${s}`
              }
          }
      }
      return '00:00'
  }

  // --- API 逻辑 ---
  const fetchEpisodes = async () => {
    if (!props.project) return
    loading.value = true
    try {
      const res: any = await episodeApi.list(props.project.id)
      episodes.value = res
    } catch (e) { episodes.value = [] } 
    finally { loading.value = false }
  }
  
  watch(() => props.project, (newVal) => {
    if (newVal) {
      fetchEpisodes()
    } else {
      episodes.value = []
      isAdding.value = false
      editingId.value = null
      deleteConfirmId.value = null
    }
  }, { immediate: true })
  
  // --- CRUD 逻辑 (保持不变) ---
  const startAdd = () => {
    isAdding.value = true
    tempTitle.value = ''
    nextTick(() => inputRef.value?.focus())
  }
  const confirmAdd = async () => {
    if (!tempTitle.value.trim()) return message.warning('标题不能为空')
    try {
      await episodeApi.create(props.project.id, { title: tempTitle.value })
      message.success('新行已写入')
      isAdding.value = false
      fetchEpisodes()
    } catch (e) { message.error('写入失败') }
  }
  const startEdit = (ep: any) => {
    editingId.value = ep.id
    tempTitle.value = ep.title
    nextTick(() => document.getElementById(`edit-input-${ep.id}`)?.focus())
  }
  const confirmEdit = async (ep: any) => {
    if (!tempTitle.value.trim()) return
    if (tempTitle.value === ep.title) { editingId.value = null; return }
    try {
      await episodeApi.update(props.project.id, ep.id, { title: tempTitle.value })
      ep.title = tempTitle.value
      editingId.value = null
      message.success('修订已保存')
    } catch (e) { message.error('修订失败') }
  }
  const handleDeleteClick = (id: number) => { deleteConfirmId.value = deleteConfirmId.value === id ? null : id }
  const confirmDelete = async (id: number) => {
    deleteConfirmId.value = null
    scribblingId.value = id
    setTimeout(async () => {
      try {
        await episodeApi.delete(props.project.id, id)
        episodes.value = episodes.value.filter(ep => ep.id !== id)
      } catch (e) { message.error('无法抹除') } 
      finally { scribblingId.value = null }
    }, 500)
  }
  
  const enterWorkbench = async (epId: number, event: MouseEvent) => {
    if (editingId.value || deleteConfirmId.value) return 
    if (!props.project) return
  
    if (props.project.assets) {
        try {
             const targetEp = episodes.value.find(e => e.id === epId)
             if (targetEp && props.project.assets) {
                 const currentConfig = targetEp.ai_config || {}
                 const script = currentConfig.generated_script || {}
                 let changed = false
                 
                 const existingCharIds = new Set((script.characters || []).map((c: any) => c.id))
                 const existingSceneIds = new Set((script.scenes || []).map((s: any) => s.id))
                 
                 const newChars = [...(script.characters || [])]
                 const newScenes = [...(script.scenes || [])]
                 
                 props.project.assets.characters.forEach((char: any) => {
                     if (!existingCharIds.has(char.id)) {
                         newChars.push(char)
                         changed = true
                     }
                 })
                 
                 props.project.assets.scenes.forEach((scene: any) => {
                     if (!existingSceneIds.has(scene.id)) {
                         newScenes.push(scene)
                         changed = true
                     }
                 })
                 
                 if (changed) {
                     if (!currentConfig.generated_script) currentConfig.generated_script = {}
                     currentConfig.generated_script.characters = newChars
                     currentConfig.generated_script.scenes = newScenes
                     
                     await episodeApi.update(props.project.id, epId, { ai_config: currentConfig } as any)
                 }
             }
        } catch (e) {
            console.error("Sync failed", e)
        }
    }

    // 1. 获取点击目标的坐标 (相对于视口)
    const target = (event.currentTarget as HTMLElement)
    const rect = target.getBoundingClientRect()
  
    // 2. 初始化遮罩位置 (完全重合)
    transitionState.style = {
      top: `${rect.top}px`,
      left: `${rect.left}px`,
      width: `${rect.width}px`,
      height: `${rect.height}px`,
      opacity: 1,
      borderRadius: '12px'
    }
    transitionState.active = true
  
    // 3. 强制渲染第一帧
    await nextTick()
  
    // 4. 下一帧执行动画：扩散到全屏
    requestAnimationFrame(() => {
      transitionState.style = {
        top: '0px',
        left: '0px',
        width: '100vw',
        height: '100vh',
        opacity: 1,
        borderRadius: '0px' // 方角
      }
    })
  
    // 5. 动画结束后跳转 (500ms 对应 CSS duration)
    setTimeout(() => {
      router.push(`/workbench/${props.project.id}/${epId}`)
      // 跳转完成后，稍微延迟再移除遮罩，避免闪烁
      setTimeout(() => {
        transitionState.active = false
      }, 100)
    }, 500)
  }
  </script>
  
<template>
  <div class="absolute inset-0 flex flex-col overflow-hidden z-0 paper-texture rounded-r-3xl shadow-inner border-r border-gray-300">
    <!-- Removed separate background div, integrated into paper-texture and paper-lines -->

      <div class="flex-1 p-10 relative z-10 flex flex-col h-full" v-if="project">
        
        <div class="mb-6 pb-4 border-b-2 border-gray-800/10 border-dashed shrink-0 relative z-20">
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-4">
              <button @click="emit('back')" class="p-2 rounded-full hover:bg-gray-800/5 transition-colors group">
                <ArrowLeft class="w-6 h-6 text-gray-500 group-hover:text-gray-800" />
              </button>
              <div>
                <div class="flex items-center gap-3">
                    <h1 class="text-3xl font-black text-gray-800 font-serif leading-tight tracking-tight">{{ project.name }}</h1>
                </div>
                <div class="flex items-center gap-2 text-xs text-gray-500 mt-1 font-mono">
                  <Calendar class="w-3 h-3" /> Created: {{ new Date(project.created_at).toLocaleDateString() }}
                </div>
              </div>
            </div>
            <div class="flex gap-2">
              <NeuButton @click="archiveVisible = true"  class="bg-white/50 border border-gray-300 shadow-sm text-gray-700 hover:bg-white">
                <FileText class="w-4 h-4 mr-2" />  设定集
              </NeuButton>
              <NeuButton v-if="!isAdding" @click="startAdd" class="bg-white/50 border border-gray-300 shadow-sm text-gray-700 hover:bg-white">
                <Plus class="w-4 h-4 mr-2" /> 创建剧集
              </NeuButton>
            </div>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scroll pr-2 -mr-2 space-y-0 pb-10 paper-lines">
        
        <transition name="fade">
          <div v-if="isAdding" class="flex items-center justify-between py-4 pr-4 pl-[50px] border-b border-blue-200/50 bg-blue-50/30">
            <div class="flex items-center gap-4 flex-1">
              <div class="w-8 h-8 rounded-full border-2 border-dashed border-gray-400 flex items-center justify-center text-gray-400">
                <Plus class="w-4 h-4" />
              </div>
              <input 
                ref="inputRef"
                v-model="tempTitle"
                type="text" 
                placeholder="Write title here..." 
                class="flex-1 bg-transparent outline-none text-xl font-serif text-gray-800 placeholder-gray-400"
                @keyup.enter="confirmAdd"
                @keyup.esc="isAdding = false"
              />
            </div>
            <div class="flex items-center gap-2">
              <button @click="confirmAdd" class="p-2 text-gray-400 hover:text-green-600 transition-colors"><Check class="w-4 h-4"/></button>
              <button @click="isAdding = false" class="p-2 text-gray-400 hover:text-red-500 transition-colors"><X class="w-4 h-4"/></button>
            </div>
          </div>
        </transition>

        <div 
          v-for="ep in episodes" 
          :key="ep.id"
          class="relative group/item"
        >
          <div 
            class="flex items-center justify-between pl-[50px] pr-4 py-3 min-h-[60px] hover:bg-gray-800/5 transition-all cursor-pointer border-b border-transparent"
            :class="{'opacity-50 pointer-events-none': scribblingId === ep.id}"
            @click="enterWorkbench(ep.id, $event)"
          >
            <div class="flex items-center gap-5 flex-1">
              
              <div 
                class="tactile-btn w-10 h-10 rounded-lg flex items-center justify-center transition-transform active:scale-95 bg-white shadow-sm border border-gray-200"
                @click.stop="enterWorkbench(ep.id, $event)" 
              >
                <Play class="w-4 h-4 text-gray-600 fill-current ml-0.5" />
              </div>
              
              <div v-if="editingId === ep.id" class="flex-1 mr-4" @click.stop>
                 <input 
                   :id="`edit-input-${ep.id}`"
                   v-model="tempTitle"
                   type="text"
                   class="w-full bg-transparent border-b-2 border-gray-800 outline-none text-xl font-bold font-serif text-gray-900 px-1"
                   @keyup.enter="confirmEdit(ep)"
                   @blur="confirmEdit(ep)" 
                 />
              </div>

              <div v-else class="pt-1">
                <h3 class="text-xl font-bold text-gray-800 font-serif group-hover/item:text-blue-700 transition-colors leading-none">{{ ep.title }}</h3>
                <span class="text-[10px] text-gray-400 font-mono uppercase tracking-wider">{{ ep.status }}</span>
              </div>
            </div>
            
            <div class="flex items-center gap-3" @click.stop>
              <span v-if="!editingId" class="text-gray-400 font-mono text-xs text-right min-w-[80px]">
                  {{ getEpisodeDuration(ep) }}
              </span>
              <div v-if="!editingId" class="flex items-center opacity-0 group-hover/item:opacity-100 transition-opacity gap-1">
                 <button @click="startEdit(ep)" class="p-2 text-gray-400 hover:text-blue-600 transition-all"><Pencil class="w-4 h-4" /></button>
                 <button @click="handleDeleteClick(ep.id)" class="p-2 text-gray-400 hover:text-red-600 transition-all"><Trash2 class="w-4 h-4" /></button>
              </div>
            </div>
          </div>

          <div v-if="deleteConfirmId === ep.id" class="absolute right-4 top-3 z-20 bg-[#fffefb] shadow-lg border border-gray-200 rounded-lg px-3 py-2 flex items-center gap-2 animate-in fade-in zoom-in duration-200">
            <span class="text-xs font-serif text-gray-500">Scrap?</span>
            <button @click="confirmDelete(ep.id)" class="text-red-500 hover:bg-red-50 p-1 rounded"><Check class="w-3 h-3"/></button>
            <button @click="deleteConfirmId = null" class="text-gray-400 hover:bg-gray-100 p-1 rounded"><X class="w-3 h-3"/></button>
          </div>

          <div v-if="scribblingId === ep.id" class="absolute inset-0 z-30 pointer-events-none overflow-hidden flex items-center">
             <svg width="0" height="0"><defs><filter id="roughpaper"><feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="5" result="noise" /><feDisplacementMap in="SourceGraphic" in2="noise" scale="5" /></filter></defs></svg>
             <svg viewBox="-20 -20 440 100" class="w-full h-full" preserveAspectRatio="none" style="filter: url(#roughpaper);">
               <path d="M0,40 L30,20 L60,55 L90,15 L120,50 L150,10 L180,45 L210,15 L240,55 L270,20 L300,45 L330,10 L360,50 L390,25 L410,40 L370,55 L340,25 L310,50 L280,15 L250,45 L220,20 L190,55 L160,15 L130,50 L100,20 L70,55 L40,25 L10,45 Z M5,35 L395,35" class="scribble-path" fill="none" stroke="#1e293b" stroke-width="35" stroke-linecap="round" stroke-linejoin="round" opacity="0.9" />
             </svg>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="flex-1 flex items-center justify-center text-gray-300 font-serif text-2xl">...</div>
  </div>

  <BookPreview 
    :visible="previewVisible" 
    :items="previewList" 
    :initial-index="previewIndex"
    :generating-items="{}"
    :all-characters="project?.assets?.characters || []" 
    :all-scenes="project?.assets?.scenes || []"
    :readonly="true"
    @close="previewVisible = false"
  />

  <StoryArchiveModal 
    :visible="archiveVisible"
    :project="project"
    @close="archiveVisible = false"
    @open-preview="openPreview"
  />

  <Teleport to="body">
    <div 
      v-if="transitionState.active"
      class="fixed z-[9999] pointer-events-none transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)]"
      :style="transitionState.style"
    >
      <div class="w-full h-full bg-[#E0E5EC] shadow-2xl overflow-hidden flex items-center justify-center">
        </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* Paper Theme */
.paper-texture {
  background-color: #fdfbf7;
  background-image: 
    /* Red Margin Line (Fixed on the left) */
    linear-gradient(90deg, transparent 31px, #fca5a5 32px, transparent 33px),
    /* Subtle Noise */
    url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.03'/%3E%3C/svg%3E");
}

.paper-lines {
  /* Blue Horizontal Lines (Scrolls with content) */
  background-image: repeating-linear-gradient(transparent, transparent 29px, #cbd5e1 30px);
  background-attachment: local;
  background-position: 0 10px; /* Offset to align with text */
}

/* Custom Scrollbar */
.custom-scroll::-webkit-scrollbar {
  width: 6px;
}
.custom-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scroll::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 10px;
}
.custom-scroll::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.2);
}

/* 拟物化实体按键 */
.tactile-btn {
  background: linear-gradient(145deg, #ffffff, #f0f0f0);
  box-shadow: 
    2px 2px 4px #d1d1d1, 
    -2px -2px 4px #ffffff;
  border: 1px solid #f0f0f0;
}
.tactile-btn:active {
  background: linear-gradient(145deg, #f0f0f0, #ffffff);
  box-shadow: 
    inset 2px 2px 4px #d1d1d1, 
    inset -2px -2px 4px #ffffff;
}

.scribble-path {
  stroke-dasharray: 1500;
  stroke-dashoffset: 1500;
  animation: scribble 0.5s cubic-bezier(0.25, 0.1, 0.25, 1) forwards;
}
@keyframes scribble { to { stroke-dashoffset: 0; } }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
