<script setup lang="ts">
    import { ref, onMounted, reactive } from 'vue'
    import { promptApi } from '@/api'
    import { Trash2, FileText, Plus, Save, Sparkles } from 'lucide-vue-next'
    import NeuButton from '@/components/base/NeuButton.vue'
    import { useMessage } from '@/utils/useMessage'
    import { useConfirm } from '@/utils/useConfirm'
    
    const message = useMessage()
    const { show: showConfirm } = useConfirm()
    const prompts = ref<any[]>([])
    const loading = ref(false)
    
    // 新增模式
    const isCreating = ref(false)
    const form = reactive({ title: '', content: '', type: 'text' })
    
    const fetchPrompts = async () => {
      loading.value = true
      try {
        const res: any = await promptApi.list()
        prompts.value = res
      } catch (e) {
        message.error('无法加载指令库')
      } finally {
        loading.value = false
      }
    }
    
    const savePrompt = async () => {
      if (!form.title || !form.content) return message.warning('标题和内容不能为空')
      
      try {
        await promptApi.create(form)
        message.success('指令已归档')
        isCreating.value = false
        form.title = ''
        form.content = ''
        fetchPrompts()
      } catch (e) {
        message.error('保存失败')
      }
    }
    
    const deletePrompt = async (id: number) => {
      const confirmed = await showConfirm('确定删除此指令？')
      if (!confirmed) return
      try {
        await promptApi.delete(id)
        message.success('指令已移除')
        fetchPrompts()
      } catch (e) { message.error('删除失败') }
    }
    
    onMounted(fetchPrompts)
    </script>
    
    <template>
      <div class="h-full p-10 flex flex-col">
        <div class="flex items-center justify-between mb-2">
          <h2 class="text-3xl font-black text-gray-800 font-serif">Prompt Studio</h2>
          <NeuButton v-if="!isCreating" size="sm" @click="isCreating = true">
            <Plus class="w-4 h-4 mr-2" /> New Prompt
          </NeuButton>
        </div>
        <p class="text-gray-500 italic font-serif mb-8">Craft the soul of your AI actors.</p>
    
        <transition name="fade">
          <div v-if="isCreating" class="bg-white p-6 rounded-xl shadow-lg border border-purple-100 mb-8 relative overflow-hidden">
            <div class="absolute top-0 left-0 w-1 h-full bg-purple-500"></div>
            <div class="mb-4">
              <input v-model="form.title" type="text" placeholder="指令标题 (e.g. 赛博朋克旁白)" class="w-full text-lg font-bold text-gray-800 placeholder-gray-300 border-b border-gray-200 pb-2 outline-none focus:border-purple-500 transition-colors" />
            </div>
            <div class="mb-4">
              <textarea v-model="form.content" rows="5" placeholder="在此输入 System Prompt..." class="w-full bg-gray-50 rounded-xl p-4 text-sm leading-relaxed border border-gray-200 outline-none focus:border-purple-500 focus:bg-white transition-all resize-none"></textarea>
            </div>
            <div class="flex justify-end gap-3">
              <button @click="isCreating = false" class="px-4 py-2 text-sm text-gray-400 hover:text-gray-600 font-bold">Cancel</button>
              <NeuButton size="sm" variant="primary" @click="savePrompt">
                <Save class="w-4 h-4 mr-2" /> Save to Library
              </NeuButton>
            </div>
          </div>
        </transition>
    
        <div class="flex-1 overflow-y-auto custom-scroll pr-2 -mr-2 space-y-4">
          <div 
            v-for="p in prompts" 
            :key="p.id"
            class="bg-white p-5 rounded-xl border border-gray-100 hover:shadow-md transition-all group relative overflow-hidden"
          >
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-purple-50 flex items-center justify-center text-purple-500">
                  <Sparkles class="w-4 h-4" />
                </div>
                <h3 class="font-bold text-gray-700">{{ p.title }}</h3>
                <span class="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full uppercase tracking-wider">{{ p.type }}</span>
              </div>
              <button @click="deletePrompt(p.id)" class="text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity">
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
            <p class="text-xs text-gray-500 bg-gray-50 p-3 rounded-lg font-mono line-clamp-3 leading-relaxed">
              {{ p.content }}
            </p>
          </div>
    
          <div v-if="prompts.length === 0 && !isCreating" class="text-center py-12 text-gray-400">
            <FileText class="w-12 h-12 mx-auto mb-4 opacity-20" />
            <p>Your library is empty.</p>
          </div>
        </div>
      </div>
    </template>
    
    <style scoped>
    .fade-enter-active, .fade-leave-active { transition: all 0.3s ease; }
    .fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-10px); }
    </style>