<script setup lang="ts">
import { reactive, watch } from 'vue'
import NeuButton from '@/components/base/NeuButton.vue'
import { X, Film } from 'lucide-vue-next'

const props = defineProps<{
  visible: boolean
  initialData?: any // If provided, it's edit mode
  nextShotId?: string
}>()

const emit = defineEmits(['close', 'confirm'])

const form = reactive({
  shot_id: '',
  action: '',
  shot_type: '全景',
  visual_prompt: ''
})

const shotTypes = ['特写', '近景', '中景', '全景', '远景', '大远景']

watch(() => props.visible, (newVal) => {
  if (newVal) {
    if (props.initialData) {
      form.shot_id = props.initialData.shot_id
      form.action = props.initialData.action
      form.shot_type = props.initialData.shot_type || '全景'
      form.visual_prompt = props.initialData.visual_prompt
    } else {
      // Create mode
      form.shot_id = props.nextShotId || '1'
      form.action = ''
      form.shot_type = '全景'
      form.visual_prompt = ''
    }
  }
})

const handleSubmit = () => {
  if (!form.action) return
  emit('confirm', { ...form })
  emit('close')
}
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm" @click.self="$emit('close')">
    <div class="bg-[#E0E5EC] rounded-2xl p-6 w-96 shadow-2xl neu-flat relative border border-white/50">
      <button class="absolute top-4 right-4 text-gray-400 hover:text-gray-600" @click="$emit('close')">
        <X class="w-5 h-5" />
      </button>

      <h3 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
        <Film class="w-5 h-5 text-pink-500" />
        {{ initialData ? '编辑分镜' : '新建分镜' }}
      </h3>

      <div class="space-y-4">
        <div class="flex gap-4">
            <div class="w-24">
                <label class="block text-xs font-bold text-gray-500 mb-1 ml-1">镜号</label>
                <input 
                    v-model="form.shot_id"
                    type="text" 
                    class="w-full px-4 py-2 rounded-xl bg-[#E0E5EC] neu-pressed outline-none text-gray-700 text-center font-mono font-bold"
                />
            </div>
            <div class="flex-1">
                <label class="block text-xs font-bold text-gray-500 mb-1 ml-1">景别</label>
                <select 
                    v-model="form.shot_type"
                    class="w-full px-4 py-2 rounded-xl bg-[#E0E5EC] neu-pressed outline-none text-gray-700 border-r-[16px] border-transparent"
                >
                    <option v-for="t in shotTypes" :key="t" :value="t">{{ t }}</option>
                </select>
            </div>
        </div>

        <div>
          <label class="block text-xs font-bold text-gray-500 mb-1 ml-1">画面内容/动作</label>
          <textarea 
            v-model="form.action"
            rows="3"
            class="w-full px-4 py-2 rounded-xl bg-[#E0E5EC] neu-pressed outline-none text-gray-700 placeholder-gray-400 focus:text-gray-900 transition-all resize-none border border-transparent focus:border-pink-300"
            placeholder="描述画面中发生的事情..."
          ></textarea>
        </div>
        
        <div>
          <label class="block text-xs font-bold text-gray-500 mb-1 ml-1">画面提示词 (可选)</label>
          <textarea 
            v-model="form.visual_prompt"
            rows="2"
            class="w-full px-4 py-2 rounded-xl bg-[#E0E5EC] neu-pressed outline-none text-gray-500 text-xs placeholder-gray-400 focus:text-gray-700 transition-all resize-none"
            placeholder="AI 绘图提示词..."
          ></textarea>
        </div>

        <div class="pt-2">
            <NeuButton class="w-full py-3 font-bold text-pink-600" @click="handleSubmit">
                {{ initialData ? '保存修改' : '创建分镜' }}
            </NeuButton>
        </div>
      </div>
    </div>
  </div>
</template>
