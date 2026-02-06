<script setup lang="ts">
import { reactive, watch } from 'vue'
import NeuButton from '@/components/base/NeuButton.vue'
import { X, MapPin } from 'lucide-vue-next'

const props = defineProps<{
  visible: boolean
  initialData?: any // If provided, it's edit mode
}>()

const emit = defineEmits(['close', 'confirm'])

const form = reactive({
  location_name: '',
  mood: '',
  description: ''
})

watch(() => props.visible, (newVal) => {
  if (newVal) {
    if (props.initialData) {
      form.location_name = props.initialData.location_name
      form.mood = props.initialData.mood
      form.description = props.initialData.description
    } else {
      // Reset for create mode
      form.location_name = ''
      form.mood = ''
      form.description = ''
    }
  }
})

const handleSubmit = () => {
  if (!form.location_name) return
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
        <MapPin class="w-5 h-5 text-orange-500" />
        {{ initialData ? '编辑场景' : '新建场景' }}
      </h3>

      <div class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-gray-500 mb-1 ml-1">场景名称/地点</label>
          <input 
            v-model="form.location_name"
            type="text" 
            class="w-full px-4 py-2 rounded-xl bg-[#E0E5EC] neu-pressed outline-none text-gray-700 placeholder-gray-400 focus:text-gray-900 transition-all border border-transparent focus:border-orange-300"
            placeholder="例如：咖啡厅、老旧公寓..."
          />
        </div>

        <div>
          <label class="block text-xs font-bold text-gray-500 mb-1 ml-1">氛围/时间</label>
          <input 
            v-model="form.mood"
            type="text" 
            class="w-full px-4 py-2 rounded-xl bg-[#E0E5EC] neu-pressed outline-none text-gray-700 placeholder-gray-400 focus:text-gray-900 transition-all border border-transparent focus:border-orange-300"
            placeholder="例如：午后阳光、阴雨连绵..."
          />
        </div>

        <div>
          <label class="block text-xs font-bold text-gray-500 mb-1 ml-1">场景描述</label>
          <textarea 
            v-model="form.description"
            rows="3"
            class="w-full px-4 py-2 rounded-xl bg-[#E0E5EC] neu-pressed outline-none text-gray-700 placeholder-gray-400 focus:text-gray-900 transition-all resize-none border border-transparent focus:border-orange-300"
            placeholder="详细描述场景的视觉细节..."
          ></textarea>
        </div>

        <div class="pt-2">
            <NeuButton class="w-full py-3 font-bold text-orange-600" @click="handleSubmit">
                {{ initialData ? '保存修改' : '创建场景' }}
            </NeuButton>
        </div>
      </div>
    </div>
  </div>
</template>
