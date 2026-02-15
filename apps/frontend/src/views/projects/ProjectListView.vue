<script setup lang="ts">
  import { ref, onMounted, computed } from 'vue'
  import { useRouter, useRoute } from 'vue-router'
  import { useI18n } from 'vue-i18n'
  import { BookOpen, Key, Lock, Palette, FileText } from 'lucide-vue-next'
  import NeuMessage from '@/components/base/NeuMessage.vue'
  import NeuConfirm from '@/components/base/NeuConfirm.vue'
  import WorkbenchTab from './components/WorkbenchTab.vue'
  import ApiMatrixTab from './components/ApiMatrixTab.vue'
  import SecurityTab from './components/SecurityTab.vue'
  // import PromptsTab from './components/PromptsTab.vue'
  import StylesTab from './components/StylesTab.vue'
  import EpisodeLayer from './components/EpisodeLayer.vue'
  import StoryArchiveModal from './components/StoryArchiveModal.vue'
  import { startOnboardingTour } from '@/utils/tour'
  import { projectApi } from '@/api'
  
import defaultImg from '@/assets/default.png'
import loginImg from '@/assets/login.png'
import logoImg from '@/assets/logo.png'
import helloImg from '@/assets/hello.png'

  const router = useRouter()
  const route = useRoute()
  const { t } = useI18n()
  
  const isFlipped = ref(false)
  const isFlipComplete = ref(false)
  const currentTab = ref('projects') 
  const currentProject = ref<any>(null)
  
  // Archive Modal State
  const archiveVisible = ref(false)
  const archiveProject = ref<any>(null)
  
  // Preview (Read-only) State - Reuse BookPreview from EpisodeLayer logic?
  // Actually StoryArchiveModal emits 'open-preview'.
  // But BookPreview is inside EpisodeLayer currently.
  // We should either move BookPreview up OR simply use StoryArchiveModal to show data.
  // The requirement just says "View Archives".
  // StoryArchiveModal handles the view.
  // But clicking an item inside Archive opens "BookPreview".
  // So we need BookPreview here too if we want full functionality from the root list.
  
  import BookPreview from '../workbench/components/BookPreview.vue'
  const previewVisible = ref(false)
  const previewList = ref<any[]>([])
  const previewIndex = ref(0)

  const openPreview = (items: any[], index: number) => {
      previewList.value = items
      previewIndex.value = index
      previewVisible.value = true
  }

  const bookmarks = computed(() => [
    { id: 'projects', label: t('projects.tabs.projects'), icon: BookOpen, color: 'bg-blue-500', component: WorkbenchTab },
    { id: 'styles', label: t('projects.tabs.styles'), icon: Palette, color: 'bg-teal-500', component: StylesTab },
    { id: 'api', label: t('projects.tabs.api'), icon: Key, color: 'bg-orange-500', component: ApiMatrixTab },
    // { id: 'prompts', label: '指令工坊', icon: Sparkles, color: 'bg-purple-500', component: PromptsTab },
    { id: 'password', label: t('projects.tabs.password'), icon: Lock, color: 'bg-red-500', component: SecurityTab },
  ])
  
  // --- 路由与状态同步逻辑 ---
  
  // 1. 打开项目 (添加 URL 参数)
  const handleOpenProject = async (project: any) => {
    currentProject.value = project
    isFlipped.value = true
    isFlipComplete.value = false
    // 替换 URL 但不刷新页面
    router.replace({ query: { ...route.query, id: project.id } })
    
    // Fetch aggregated assets
    try {
        const assets: any = await projectApi.getAssets(project.id)
        currentProject.value = { ...currentProject.value, assets }
    } catch (e) {
        console.error("Failed to fetch assets", e)
    }
  }

  const handleTransitionEnd = (e: TransitionEvent) => {
      if (e.propertyName === 'transform' && isFlipped.value) {
          isFlipComplete.value = true
      }
  }

  const handleOpenArchive = async (project: any) => {
      archiveProject.value = project
      archiveVisible.value = true
      
      // Ensure assets are loaded
      try {
          const assets: any = await projectApi.getAssets(project.id)
          archiveProject.value = { ...archiveProject.value, assets }
      } catch (e) {
          console.error("Failed to fetch assets", e)
      }
  }
  
  const handleBack = () => {
    isFlipped.value = false
    isFlipComplete.value = false
    router.replace({ query: { ...route.query, id: undefined } })
    setTimeout(() => { currentProject.value = null }, 800)
  }
  
  const initFromUrl = async () => {
    const projectId = route.query.id
    if (projectId) {
      try {
        // 需要先获取项目详情，确保有数据传给 EpisodeLayer
        const res: any = await projectApi.get(Number(projectId))
        currentProject.value = res
        isFlipped.value = true
        isFlipComplete.value = true // Immediately hide if loaded from URL
        
        // Fetch aggregated assets
        const assets: any = await projectApi.getAssets(Number(projectId))
        currentProject.value = { ...currentProject.value, assets }
      } catch (e) {
        console.error("Project not found", e)
        // 如果项目不存在，清理 URL
        handleBack()
      }
    }
  }
  
  const switchTab = (tabId: string) => {
    if (isFlipped.value) {
      isFlipped.value = false
      isFlipComplete.value = false
      // 切换 Tab 时也退出项目详情
      router.replace({ query: { ...route.query, id: undefined } })
      setTimeout(() => { currentTab.value = tabId; currentProject.value = null }, 600)
    } else {
      currentTab.value = tabId
    }
  }
  
  onMounted(() => {
    initFromUrl()
    
    // Start Project List Tour
    startOnboardingTour('project_list_view', [
        { 
            element: '#tour-bookmarks-projects', 
            theme: 'blue',
            image: logoImg,
            popover: { title: t('projects.tour.workbenchTitle'), description: t('projects.tour.workbenchDesc'), side: 'left' } 
        },
        { 
            element: '#tour-bookmarks-styles', 
            theme: 'green',
            image: defaultImg,
            popover: { title: t('projects.tour.stylesTitle'), description: t('projects.tour.stylesDesc'), side: 'left' } 
        },
        { 
            element: '#tour-bookmarks-api', 
            theme: 'yellow',
            image: loginImg,
            popover: { title: t('projects.tour.apiTitle'), description: t('projects.tour.apiDesc'), side: 'left' } 
        },
        { 
            element: '#tour-bookmarks-password', 
            theme: 'pink',
            image: helloImg,
            popover: { title: t('projects.tour.securityTitle'), description: t('projects.tour.securityDesc'), side: 'left' } 
        },
        { 
            element: '#tour-project-list-area', 
            theme: 'yellow',
            image: helloImg,
            popover: { title: t('projects.tour.listTitle'), description: t('projects.tour.listDesc'), side: 'right' } 
        }
    ])
  })
  </script>
  
  <template>
    <NeuMessage />
    <NeuConfirm />
  
    <div class="min-h-screen bg-[#E0E5EC] flex items-center justify-center p-8 overflow-hidden perspective-container">
      <div class="absolute inset-0 pointer-events-none opacity-20" style="background-image: radial-gradient(#9ca3af 1px, transparent 1px); background-size: 20px 20px;"></div>
  
      <div class="relative w-full max-w-6xl h-[85vh] flex z-10">
        
        <div class="w-16 h-full bg-gray-800 rounded-l-3xl flex flex-col items-center py-10 gap-6 z-50 shadow-2xl relative">
          <div v-for="i in 10" :key="i" class="w-4 h-4 rounded-full bg-[#E0E5EC] shadow-inner ring-1 ring-gray-600"></div>
        </div>
  
        <div class="flex-1 relative perspective-page z-20">
          
          <EpisodeLayer :project="currentProject" @back="handleBack" />
  
          <div 
            class="absolute inset-0 w-full h-full transform-style-3d transition-transform duration-1000 origin-left z-20 will-change-transform"
            :class="{ 'is-open': isFlipped, 'pointer-events-none opacity-0': isFlipped && isFlipComplete }"
            @transitionend="handleTransitionEnd"
          >
            <div class="absolute inset-0 paper-texture rounded-r-3xl shadow-xl border-r border-gray-300 backface-hidden flex flex-col overflow-hidden will-change-transform">
              <div class="absolute inset-0 pointer-events-none opacity-50 mix-blend-multiply" style="background-image: repeating-linear-gradient(transparent, transparent 29px, #cbd5e1 30px);"></div>
              <div class="flex-1 relative z-10 h-full" id="tour-project-list-area">
                <transition name="fade" mode="out-in">
                  <component 
                    :is="bookmarks.find((b: any) => b.id === currentTab)?.component" 
                    @open-project="handleOpenProject"
                    @open-archive="handleOpenArchive"
                  />
                </transition>
              </div>
              <!-- <div class="absolute bottom-4 right-6 text-gray-300 font-serif italic text-xs select-none">Page 1 of ∞</div> -->
            </div>
  
            <div 
              class="absolute inset-0 bg-[#e5e7eb] rounded-l-3xl border-l border-gray-400 shadow-inner flex flex-col items-center justify-center text-gray-400 backface-hidden will-change-transform"
              style="transform: rotateY(180deg);"
            >
               <div class="transform scale-x-[-1] opacity-20">
                  <FileText class="w-32 h-32 mb-4" />
                  <h2 class="text-2xl font-serif font-bold">{{ t('projects.archiveTitle') }}</h2>
               </div>
            </div>
          </div>
  
        </div>
  
        <div class="absolute top-12 -right-12 flex flex-col gap-4 z-0">
          <button 
            v-for="bm in bookmarks" 
            :key="bm.id"
            :id="`tour-bookmarks-${bm.id}`"
            @click="switchTab(bm.id)"
            class="w-14 h-32 rounded-r-lg shadow-md flex flex-col items-center justify-center gap-2 transition-all duration-300 hover:w-16 cursor-pointer group"
            :class="[bm.color, (currentTab === bm.id && !isFlipped) ? 'translate-x-0 shadow-inner brightness-110' : '-translate-x-2 brightness-90 hover:translate-x-0']"
          >
            <span class="text-white font-bold text-xs writing-vertical tracking-widest opacity-80 group-hover:opacity-100">{{ bm.label }}</span>
            <component :is="bm.icon" class="w-4 h-4 text-white" />
          </button>
        </div>
  
      </div>
    </div>

    <!-- Global Modals for List View -->
    <StoryArchiveModal 
        :visible="archiveVisible"
        :project="archiveProject"
        @close="archiveVisible = false"
        @open-preview="openPreview"
    />

    <BookPreview 
        :visible="previewVisible" 
        :items="previewList" 
        :initial-index="previewIndex"
        :generating-items="{}"
        :all-characters="[]" 
        :all-scenes="[]"
        :readonly="true"
        @close="previewVisible = false"
    />
  </template>
  
  <style scoped>
  .perspective-container { perspective: 1500px; }
  .perspective-page { perspective: 2500px; transform-style: preserve-3d; }
  .transform-style-3d { transform-style: preserve-3d; }
  .origin-left { transform-origin: left center; }
  .is-open { transform: rotateY(-180deg); }
  .backface-hidden { backface-visibility: hidden; -webkit-backface-visibility: hidden; }
  .writing-vertical { writing-mode: vertical-rl; text-orientation: mixed; }
  .fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
  .fade-enter-from, .fade-leave-to { opacity: 0; }

  /* Paper Theme */
  .paper-texture {
    background-color: #fdfbf7;
    background-image: 
      /* Red Margin Line (Fixed on the left) */
      linear-gradient(90deg, transparent 31px, #fca5a5 32px, transparent 33px),
      /* Subtle Noise */
      url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.03'/%3E%3C/svg%3E");
  }
  </style>
