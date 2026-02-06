<script setup lang="ts">
    import { ref } from 'vue'
    import { Video, Image, Type, Music, Plus, Trash2 } from 'lucide-vue-next'
    import NeuButton from '@/components/base/NeuButton.vue'
    
    // 配置类型
    const activeType = ref<'text'|'image'|'video'|'audio'>('text')
    const configTypes = [
      { id: 'text', label: '剧本/对话', icon: Type },
      { id: 'image', label: '图像生成', icon: Image },
      { id: 'video', label: '视频生成', icon: Video },
      { id: 'audio', label: '语音/音效', icon: Music },
    ]
    
    // 模拟数据 (真实场景应从 props 传入或 API 获取)
    const configs = ref({
      text: { provider: 'openai', key: '', url: '', prompts: [{ title: '默认导演', content: '' }] },
      image: { provider: 'midjourney', key: '', url: '', prompts: [] },
      video: { provider: 'luma', key: '', url: '', prompts: [] },
      audio: { provider: 'suno', key: '', url: '', prompts: [] }
    })
    
    const addPrompt = () => {
      // @ts-ignore
      configs.value[activeType.value].prompts.push({ title: '新指令', content: '' })
    }
    </script>
    
    <template>
      <div class="flex h-full gap-6">
        <div class="w-40 flex flex-col gap-2 border-r border-gray-200 pr-4">
          <button 
            v-for="t in configTypes" 
            :key="t.id"
            @click="activeType = t.id as any"
            class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-bold text-sm text-left"
            :class="activeType === t.id ? 'bg-blue-50 text-blue-600 neu-pressed-sm' : 'hover:bg-gray-100 text-gray-500'"
          >
            <component :is="t.icon" class="w-4 h-4" />
            {{ t.label }}
          </button>
        </div>
    
        <div class="flex-1 overflow-y-auto custom-scroll pr-2">
          <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
            <span class="capitalize">{{ activeType }}</span> API Configuration
          </h3>
          
          <div class="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm space-y-4 mb-8">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="text-xs font-bold text-gray-400 uppercase">Provider</label>
                <select v-model="configs[activeType].provider" class="w-full mt-1 p-2 bg-gray-50 rounded-lg border border-gray-200 outline-none">
                  <option value="openai">OpenAI</option>
                  <option value="gemini">Gemini</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
              <div>
                <label class="text-xs font-bold text-gray-400 uppercase">Base URL</label>
                <input v-model="configs[activeType].url" type="text" class="w-full mt-1 p-2 bg-gray-50 rounded-lg border border-gray-200 outline-none" placeholder="https://api..." />
              </div>
            </div>
            <div>
              <label class="text-xs font-bold text-gray-400 uppercase">API Key</label>
              <input v-model="configs[activeType].key" type="password" class="w-full mt-1 p-2 bg-gray-50 rounded-lg border border-gray-200 outline-none" placeholder="sk-..." />
            </div>
          </div>
    
          <div class="flex items-center justify-between mb-4">
            <h4 class="font-bold text-gray-600">通用指令库 (System Prompts)</h4>
            <button @click="addPrompt" class="text-xs font-bold text-blue-500 hover:underline flex items-center gap-1"><Plus class="w-3 h-3"/> 新增</button>
          </div>
    
          <div class="space-y-4">
            <div v-for="(p, idx) in configs[activeType].prompts" :key="idx" class="relative group">
              <input v-model="p.title" class="block w-full text-sm font-bold text-gray-700 mb-1 bg-transparent outline-none border-b border-transparent focus:border-blue-300" />
              <textarea v-model="p.content" rows="3" class="w-full bg-[#f8f9fa] rounded-xl p-3 text-xs leading-relaxed border border-gray-200 outline-none focus:border-blue-300 transition-colors" placeholder="输入系统提示词..."></textarea>
              <button @click="configs[activeType].prompts.splice(idx, 1)" class="absolute top-2 right-2 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity">
                <Trash2 class="w-3 h-3" />
              </button>
            </div>
          </div>
    
          <div class="mt-8 flex justify-end">
            <NeuButton variant="primary" size="sm">保存 {{ activeType }} 配置</NeuButton>
          </div>
        </div>
      </div>
    </template>