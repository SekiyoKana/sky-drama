<script setup lang="ts">
    import { ref, onMounted } from 'vue'
    import { useI18n } from 'vue-i18n'
    import { Plus, FileText, Trash2, Archive } from 'lucide-vue-next'
    import { projectApi } from '@/api'
    import CreateProjectModal from '../components/CreateProjectModal.vue'
    import { useConfirm } from '@/utils/useConfirm'
    import { useMessage } from '@/utils/useMessage'
    import { startOnboardingTour } from '@/utils/tour'
    import helloImg from '@/assets/hello.png'
    
    const emit = defineEmits(['open-project', 'open-archive']) // 通知父组件翻页
    const confirm = useConfirm()
    const message = useMessage()
    const { t } = useI18n()
    
    const projects = ref<any[]>([])
    const loading = ref(false)
    const showCreateModal = ref(false)
    
    const fetchProjects = async () => {
      loading.value = true
      try {
        const res: any = await projectApi.list()
        projects.value = res
      } catch (e) { console.error(e) } 
      finally { loading.value = false }
    }
    
    onMounted(() => {
        fetchProjects()
        
        startOnboardingTour('workbench_tab_view', [
            { 
                element: '#tour-project-create-card', 
                theme: 'blue',
                image: helloImg,
                popover: { title: t('projects.workbench.tour.createTitle'), description: t('projects.workbench.tour.createDesc'), side: 'left' } 
            },
            { 
                element: '#tour-project-list', 
                theme: 'yellow',
                popover: { title: t('projects.workbench.tour.listTitle'), description: t('projects.workbench.tour.listDesc'), side: 'top' } 
            }
        ])
    })

    const handleCreate = async (data: any) => {
      try {
        await projectApi.create(data)
        showCreateModal.value = false
        fetchProjects()
      } catch (e) { message.error(t('projects.workbench.messages.createFailed')) }
    }
    
    const handleCardClick = (p: any) => {
      emit('open-project', p) // 触发翻页
    }

    const handleDelete = async (p: any) => {
      const confirmed = await confirm.show(
        t('projects.workbench.messages.deleteConfirmText', { name: p.name }),
        t('projects.workbench.messages.deleteConfirmTitle')
      )
      if (!confirmed) return
      
      try {
        await projectApi.delete(p.id)
        fetchProjects()
      } catch (e) {
        message.error(t('projects.workbench.messages.deleteFailed'))
      }
    }

    const handleArchive = (p: any) => {
      emit('open-archive', p)
    }
    
    // onMounted(fetchProjects) // Moved to top
    </script>
    
    <template>
      <div class="h-full flex flex-col p-10">
        <div class="flex items-center justify-between mb-8 shrink-0">
          <div>
            <h1 class="text-3xl font-black text-gray-800 font-serif">{{ t('projects.workbench.title') }}</h1>
            <p class="text-gray-500 font-serif italic">{{ t('projects.workbench.subtitle') }}</p>
          </div>
          <!-- <div class="neu-flat px-4 py-2 rounded-full flex items-center gap-2 bg-[#f3f4f6]">
            <Search class="w-4 h-4 text-gray-400" />
            <input type="text" placeholder="搜索剧本..." class="bg-transparent outline-none text-sm w-32" />
          </div> -->
        </div>
    
        <div class="flex-1 overflow-y-auto custom-scroll p-6 -mx-6" id="tour-project-list">
          <div v-if="loading" class="text-center text-gray-400 mt-20">{{ t('projects.workbench.loading') }}</div>
          
          <div v-else class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-8 pb-10">
            <div 
              v-for="p in projects" 
              :key="p.id"
              @click="handleCardClick(p)"
              class="group relative aspect-[3/4] bg-white rounded-r-xl rounded-l-sm shadow-md cursor-pointer transition-all duration-300 hover:-translate-y-3 hover:shadow-2xl hover:rotate-1 border-l-4 border-gray-800 flex flex-col hover:z-50"
            >
              <div class="flex-1 p-6 relative overflow-hidden">
                <div class="absolute -right-4 -top-4 opacity-5 group-hover:opacity-10 transition-opacity transform rotate-12">
                   <FileText class="w-32 h-32" />
                </div>
                <h3 class="text-xl font-bold font-serif text-gray-800 line-clamp-2 relative z-10">{{ p.name }}</h3>
                <p class="text-xs text-gray-400 mt-2 relative z-10 line-clamp-3">{{ p.description }}</p>
              </div>
              <div class="h-12 border-t border-gray-100 flex items-center justify-between px-4 bg-gray-50 rounded-br-xl">
                <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{{ new Date(p.created_at).toLocaleDateString() }}</span>
                
                <div class="flex items-center gap-2 relative z-50" @click.stop>
                    <button 
                        @click="handleArchive(p)"
                        class="p-1.5 rounded-full hover:bg-gray-200 text-gray-400 hover:text-blue-500 transition-colors"
                        :title="t('projects.workbench.archive')"
                    >
                        <Archive class="w-4 h-4" />
                    </button>
                    <button 
                        @click="handleDelete(p)"
                        class="p-1.5 rounded-full hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
                        :title="t('projects.workbench.delete')"
                    >
                        <Trash2 class="w-4 h-4" />
                    </button>
                </div>
              </div>
            </div>
    
            <div 
              @click="showCreateModal = true"
              id="tour-project-create-card"
              class="aspect-[3/4] border-2 border-dashed border-gray-300 rounded-xl flex flex-col items-center justify-center gap-4 cursor-pointer hover:border-blue-400 hover:bg-blue-50/30 transition-colors group hover:-translate-y-2 hover:shadow-lg"
            >
              <div class="w-12 h-12 rounded-full bg-gray-200 group-hover:bg-blue-100 flex items-center justify-center transition-colors">
                <Plus class="w-6 h-6 text-gray-400 group-hover:text-blue-500" />
              </div>
              <span class="text-sm font-bold text-gray-400 group-hover:text-blue-500">{{ t('projects.workbench.newProject') }}</span>
            </div>
          </div>
        </div>
    
        <CreateProjectModal 
          :visible="showCreateModal" 
          @close="showCreateModal = false"
          @confirm="handleCreate"
        />
      </div>
    </template>
