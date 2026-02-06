<script setup lang="ts">
    import { ref, onMounted, reactive } from 'vue'
    import { Trash2, Key, Plus, Save, Activity, XCircle } from 'lucide-vue-next'
    import { apiKeyApi, aiApi } from '@/api'
    import NeuButton from '@/components/base/NeuButton.vue'
import { useConfirm } from '@/utils/useConfirm'
import { useMessage } from '@/utils/useMessage'
import { startOnboardingTour } from '@/utils/tour'
import loginImg from '@/assets/login.png'

const message = useMessage()
const confirmDialog = useConfirm()
const keys = ref<any[]>([])
const loading = ref(false)
const testingId = ref<number | null>(null) // 当前正在测试的 ID
const isCreating = ref(false) // 👈 控制弹框
const editingId = ref<number | null>(null) // 👈 编辑模式 ID

const form = reactive({
  platform: 'openai',
  name: '',
  key: '',
  base_url: '',
  text_endpoint: '/chat/completions',
  image_endpoint: '/images/generations',
  video_endpoint: '/videos',
  video_fetch_endpoint: '/videos/{task_id}',
  audio_endpoint: ''
})

    
    const fetchKeys = async () => {
      loading.value = true
      try {
        const res: any = await apiKeyApi.list()
        keys.value = res
      } catch (e) {
        message.error('无法加载密钥列表')
      } finally {
        loading.value = false
      }
    }
    
    // 🌐 BaseURL 校验逻辑
    const validateUrl = (url: string) => {
      if (!url) return true // 允许为空（使用默认）
      const pattern = /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/
      return pattern.test(url)
    }
    
const addKey = async () => {
  if (!form.name) { // Key is optional when updating
    return message.warning('请填写完整的密钥信息')
  }
  // Only check key if creating new
  if (!editingId.value && !form.key) {
      return message.warning('请填写密钥')
  }
  
  if (!validateUrl(form.base_url)) {
    return message.error('Base URL 格式不正确 (需以 http:// 或 https:// 开头)')
  }

  try {
    let res: any;
    if (editingId.value) {
        res = await apiKeyApi.update(editingId.value, {
          platform: form.platform,
          name: form.name,
          key: form.key, // might be empty
          base_url: form.base_url,
          text_endpoint: form.text_endpoint,
          image_endpoint: form.image_endpoint,
          video_endpoint: form.video_endpoint,
          video_fetch_endpoint: form.video_fetch_endpoint,
          audio_endpoint: form.audio_endpoint
        })
        message.success('密钥已更新')
    } else {
        res = await apiKeyApi.create({
          platform: form.platform,
          name: form.name,
          key: form.key,
          base_url: form.base_url,
          text_endpoint: form.text_endpoint,
          image_endpoint: form.image_endpoint,
          video_endpoint: form.video_endpoint,
          video_fetch_endpoint: form.video_fetch_endpoint,
          audio_endpoint: form.audio_endpoint
        })
        message.success('密钥已安全存储')
    }

    // Reset and refresh
    cancelCreate() // Close modal and reset form
    await fetchKeys()
    isCreating.value = false // 👈 关闭弹框
    editingId.value = null

    // ✨ 自动触发一次连接测试
    if (res && res.id) {
        testConnection(res.id)
    }

  } catch (e) {

    message.error('保存失败，请检查网络')
  }
}

const cancelCreate = () => {
    isCreating.value = false
    editingId.value = null
    form.key = ''
    form.name = ''
    form.base_url = ''
}

    
const editKey = (k: any) => {
    editingId.value = k.id
    form.platform = k.platform
    form.name = k.name
    // 直接回显 masked_key，因为后端现在存的是明文，但 API 只返回 masked_key。
    // 如果想要在编辑时显示完整 key，需要后端 API 支持返回完整 key（目前 read_apikeys 返回的是 masked_key）。
    // 但根据需求 "直接显示密钥不要默认空"，且 "后端存明文"，我们可以尝试推断：
    // 用户希望看到原本存进去的 key。
    // 可是 read_apikeys 接口为了安全返回的是 "sk-****7890"。
    // 如果要“显示”，那只能显示这个掩码后的 key，或者要求后端返回完整 key。
    // 假设用户接受显示掩码后的 key，或者我们修改 API 返回完整 key？
    // 按照通常安全做法，不应返回完整 key。
    // 但既然用户明确要求 "移除加密" 且 "正常显示保存的 key"，那我就假设他想要前端也能看到完整 key。
    // 所以我需要修改后端 read_apikeys 返回完整 key。
    form.key = k.key || k.masked_key || '' 
    form.base_url = k.base_url
    form.text_endpoint = k.text_endpoint || '/chat/completions'
    form.image_endpoint = k.image_endpoint || '/images/generations'
    form.video_endpoint = k.video_endpoint || '/videos'
    form.video_fetch_endpoint = k.video_fetch_endpoint || '/videos/{task_id}'
    form.audio_endpoint = k.audio_endpoint || ''
    isCreating.value = true
}

const deleteKey = async (id: number) => {
  if(!await confirmDialog.show('确定将此密钥销毁？此操作不可逆。', '销毁密钥')) return
  
  try {
    await apiKeyApi.delete(id)
    message.success('密钥已销毁')
    fetchKeys()
  } catch (e) { message.error('删除失败') }
}

    
    // 🧪 测试连接逻辑
    const testConnection = async (id: number) => {
      testingId.value = id
      try {
        const res: any = await aiApi.testConnection(id)
        console.log(res)
        message.success(`联通成功！可用模型: ${res.models.slice(0, 3).join(', ')}...`)
      } catch (e: any) {
        message.error(`连接失败: ${e.response?.data?.detail || '网络错误'}`)
      } finally {
        testingId.value = null
      }
    }
    
    onMounted(() => {
      fetchKeys()
      
      startOnboardingTour('api_matrix_view', [
          { 
              element: '#tour-api-create-btn', 
              theme: 'pink',
              image: loginImg,
              popover: { title: '连接模型', description: '点击添加新的 API Key。', side: 'left' } 
          },
          { 
              element: '#tour-api-list', 
              theme: 'yellow',
              popover: { title: '密钥管理', description: '这里显示已保存的密钥。你可以测试连接状态，或删除无效密钥。', side: 'top' } 
          }
      ])
    })
    </script>
    
    <template>
      <div class="h-full p-10 flex flex-col relative">
        <div class="flex items-center justify-between mb-2">
            <h2 class="text-3xl font-black text-gray-800 font-serif">API 设置</h2>
            <NeuButton v-if="!isCreating" size="sm" @click="isCreating = true" id="tour-api-create-btn">
                <Plus class="w-4 h-4 mr-2" /> 新建密钥
            </NeuButton>
        </div>
        <p class="text-gray-500 italic font-serif mb-8">管理您的 APIKEY。</p>

    <transition name="drop-paper">
      <div v-if="isCreating" class="absolute inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm" @click.self="cancelCreate">
         <div class="relative w-[500px] bg-[#fdfbf7] p-8 shadow-2xl rounded-sm transform rotate-1 border border-gray-200 paper-texture flex flex-col max-h-[90vh]" @click.stop>
            <!-- Tape -->
            <div class="absolute -top-3 left-1/2 -translate-x-1/2 w-32 h-8 bg-yellow-200/80 shadow-sm transform -rotate-2 z-10"></div>

            <button @click="cancelCreate" class="absolute top-2 right-2 text-gray-400 hover:text-red-500 transition-colors z-20">
                <XCircle class="w-6 h-6" />
            </button>

            <h3 class="text-xl font-black text-gray-800 font-serif mb-6 text-center border-b-2 border-gray-800 pb-2">
                {{ editingId ? '编辑连接' : '新建连接' }}
            </h3>

            <div class="space-y-4 overflow-y-auto custom-scroll pr-2 flex-1">
               <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-xs font-bold text-gray-500 uppercase mb-1">平台类型</label>
                    <input v-model="form.platform" type="text" class="w-full bg-white/50 border-b border-gray-300 px-3 py-2 text-sm focus:border-blue-500 outline-none font-serif placeholder-gray-400 transition-colors" placeholder="openai" />
                  </div>
                  <div>
                    <label class="block text-xs font-bold text-gray-500 uppercase mb-1">连接名称</label>
                    <input v-model="form.name" type="text" class="w-full bg-white/50 border-b border-gray-300 px-3 py-2 text-sm focus:border-blue-500 outline-none font-serif placeholder-gray-400 transition-colors" placeholder="My LLM" />
                  </div>
               </div>

               <div>
                  <label class="block text-xs font-bold text-gray-500 uppercase mb-1">接口地址 (Base URL)</label>
                  <input v-model="form.base_url" type="text" class="w-full bg-white/50 border-b border-gray-300 px-3 py-2 text-sm focus:border-blue-500 outline-none font-mono placeholder-gray-400 transition-colors" placeholder="https://api.openai.com/v1" />
               </div>

               <div>
                  <label class="block text-xs font-bold text-gray-500 uppercase mb-1">密钥 (API Key) {{ editingId ? '(留空不修改)' : '' }}</label>
                  <div class="relative group">
                    <input v-model="form.key" type="password" class="w-full bg-white/50 border-b border-gray-300 px-3 py-2 text-sm focus:border-blue-500 outline-none font-mono pr-8 placeholder-gray-400 transition-colors" placeholder="sk-..." />
                    <Key class="w-4 h-4 text-gray-300 absolute right-2 top-2 group-focus-within:text-blue-500 transition-colors" />
                  </div>
               </div>

               <div class="pt-4 border-t border-gray-100">
                  <p class="text-xs font-bold text-gray-400 uppercase mb-3">接口重写 (Endpoint Overrides)</p>
                  <div class="space-y-3">
                     <div class="flex items-center gap-3">
                        <span class="text-xs font-mono text-gray-400 w-16 text-right">对话 Chat</span>
                        <input v-model="form.text_endpoint" class="flex-1 bg-gray-50 border-none rounded px-2 py-1.5 text-xs font-mono focus:ring-1 focus:ring-blue-300 outline-none" placeholder="/chat/completions" />
                     </div>
                     <div class="flex items-center gap-3">
                        <span class="text-xs font-mono text-gray-400 w-16 text-right">绘图 Image</span>
                        <input v-model="form.image_endpoint" class="flex-1 bg-gray-50 border-none rounded px-2 py-1.5 text-xs font-mono focus:ring-1 focus:ring-blue-300 outline-none" placeholder="/images/generations" />
                     </div>
                     <div class="flex items-center gap-3">
                        <span class="text-xs font-mono text-gray-400 w-16 text-right">视频 Video</span>
                        <input v-model="form.video_endpoint" class="flex-1 bg-gray-50 border-none rounded px-2 py-1.5 text-xs font-mono focus:ring-1 focus:ring-blue-300 outline-none" placeholder="/videos" />
                     </div>
                     <div class="flex items-center gap-3">
                        <span class="text-xs font-mono text-gray-400 w-16 text-right">获取视频 Fetch</span>
                        <input v-model="form.video_fetch_endpoint" class="flex-1 bg-gray-50 border-none rounded px-2 py-1.5 text-xs font-mono focus:ring-1 focus:ring-blue-300 outline-none cursor-not-allowed opacity-75" placeholder="/videos/{task_id}" readonly />
                     </div>
                     <div class="flex items-center gap-3">
                        <span class="text-xs font-mono text-gray-400 w-16 text-right">音频 Audio</span>
                        <input v-model="form.audio_endpoint" class="flex-1 bg-gray-50 border-none rounded px-2 py-1.5 text-xs font-mono focus:ring-1 focus:ring-blue-300 outline-none" />
                     </div>
                  </div>
               </div>
            </div>

            <div class="mt-6 pt-4 border-t border-gray-800/10 flex justify-end gap-3">
               <button @click="cancelCreate" class="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 font-bold transition-colors">取消</button>
               <button 
                 @click="addKey" 
                 class="px-6 py-2 bg-gray-800 text-white font-bold tracking-widest hover:bg-black transition-colors flex items-center shadow-lg active:scale-95 transform duration-150 text-sm"
               >
                 <Save class="w-4 h-4 mr-2" /> 保存设置
               </button>
            </div>
         </div>
      </div>
    </transition>
    
        <div class="flex-1 overflow-y-auto custom-scroll pr-2 -mr-2" id="tour-api-list">
          <h3 class="text-sm font-bold text-gray-700 uppercase mb-4">活跃 APIKEY</h3>
          <div class="space-y-3">

             <div 
               v-for="k in keys" 
               :key="k.id"
               class="flex items-center justify-between p-4 bg-white rounded-xl border border-gray-100 hover:shadow-md transition-all group cursor-pointer hover:border-orange-200"
               @click="editKey(k)"
             >

              <div class="flex items-center gap-4">
                 <div class="w-10 h-10 rounded-full bg-orange-50 flex items-center justify-center text-orange-500 border border-orange-100">
                   <Key class="w-5 h-5" />
                 </div>
                 <div>
                   <div class="font-bold text-gray-700 flex items-center gap-2">
                     {{ k.name }}
                     <span class="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">{{ k.masked_key }}</span>
                   </div>
                   <div class="text-xs text-gray-400 font-mono mt-1">{{ k.platform }} • {{ k.base_url || '默认节点' }}</div>
                 </div>
               </div>
               
               <div class="flex items-center gap-2" @click.stop>
                 <button 
                   @click="testConnection(k.id)" 
                   class="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors"

                  :class="testingId === k.id ? 'bg-blue-50 text-blue-600' : 'bg-gray-50 text-gray-600 hover:bg-green-50 hover:text-green-600'"
                  :disabled="testingId === k.id"
                >
                  <Activity class="w-3 h-3" :class="{'animate-pulse': testingId === k.id}" />
                  {{ testingId === k.id ? '测试中...' : '测试' }}
                </button>
                
                <button @click="deleteKey(k.id)" class="text-gray-300 hover:text-red-500 transition-colors p-2 hover:bg-red-50 rounded-lg">
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </div>
            
            <div v-if="keys.length === 0" class="text-center py-10 text-gray-400 text-sm border-2 border-dashed border-gray-200 rounded-xl bg-gray-50/50">
               暂无活跃密钥。请添加一个以开始生成。
            </div>
          </div>
        </div>
      </div>
    </template>
    <style scoped>
    .paper-texture {
      background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' fill='%239C92AC' fill-opacity='0.05' fill-rule='evenodd'/%3E%3C/svg%3E");
    }
    
    .drop-paper-enter-active, .drop-paper-leave-active { transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
    .drop-paper-enter-from, .drop-paper-leave-to { opacity: 0; transform: scale(0.8) translateY(-50px) rotate(-10deg); }
    </style>
