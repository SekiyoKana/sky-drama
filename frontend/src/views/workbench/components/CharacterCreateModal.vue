<script setup lang="ts">
import { reactive, watch } from 'vue'
import { X, Sparkles } from 'lucide-vue-next'
import NeuButton from '@/components/base/NeuButton.vue'
import NeuInput from '@/components/base/NeuInput.vue'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits(['close', 'confirm'])

const form = reactive({
  name: '',
  role: '主角',
  description: ''
})

// Reset form when opening
watch(() => props.visible, (val) => {
  if (val) {
    form.name = ''
    form.role = '主角'
    form.description = ''
  }
})

const handleConfirm = () => {
  if (!form.name.trim()) return
  emit('confirm', { ...form })
}

const handleClose = () => {
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center pointer-events-none" @click.self="handleClose">
        <div 
            class="w-[400px] neu-flat p-6 rounded-[2rem] bg-[#E0E5EC] flex flex-col gap-6 relative overflow-hidden transition-all duration-300 transform pointer-events-auto shadow-2xl border border-white/40"
        >
          <!-- Decorative Background Effect -->
          <div class="absolute -top-10 -right-10 w-32 h-32 bg-blue-400/10 rounded-full blur-3xl pointer-events-none"></div>
          <div class="absolute -bottom-10 -left-10 w-32 h-32 bg-purple-400/10 rounded-full blur-3xl pointer-events-none"></div>

          <!-- Header -->
          <div class="flex items-center justify-between pl-2 relative z-10">
            <div class="flex items-center gap-2">
                <Sparkles class="w-5 h-5 text-blue-500 animate-pulse" />
                <h3 class="text-lg font-bold text-gray-700 tracking-wide">添加角色</h3>
            </div>
            <button @click="handleClose" class="p-2 rounded-full neu-flat hover:text-red-500 transition-all hover:scale-110 active:scale-95">
              <X class="w-5 h-5" />
            </button>
          </div>

          <!-- Form -->
          <div class="flex flex-col gap-4 relative z-10">
            <NeuInput v-model="form.name" label="角色名称" placeholder="例如：韩立" />
            <NeuInput v-model="form.role" label="角色标签" placeholder="例如：主角" />
            
            <!-- Textarea for Description -->
            <div class="flex flex-col gap-2 group">
              <label class="ml-2 text-sm font-bold text-gray-500 uppercase tracking-wide group-focus-within:text-blue-500 transition-colors">角色描述</label>
              <textarea 
                v-model="form.description"
                rows="4"
                class="w-full px-5 py-3 rounded-2xl outline-none transition-all duration-300 neu-pressed bg-transparent text-gray-700 placeholder-gray-400 resize-none focus:ring-2 focus:ring-blue-200/50"
                placeholder="外貌描写、性格特征、服装风格..."
              ></textarea>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex gap-4 mt-2 relative z-10">
            <NeuButton class="flex-1" @click="handleClose">取消</NeuButton>
            <NeuButton class="flex-1" variant="primary" @click="handleConfirm">确认添加</NeuButton>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: all 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.modal-fade-enter-to,
.modal-fade-leave-from {
  opacity: 1;
  transform: scale(1);
}
</style>
