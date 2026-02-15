<script setup lang="ts">
    import { ref } from 'vue'
    import { useI18n } from 'vue-i18n'
    import { X, PenTool, Check } from 'lucide-vue-next'
    
    const props = defineProps<{ visible: boolean }>()
    const emit = defineEmits(['close', 'confirm'])
    const { t } = useI18n()
    
    const form = ref({ name: '', description: '' })
    const loading = ref(false)
    
    const handleConfirm = async () => {
      if (!form.value.name) return
      loading.value = true
      // 模拟网络延迟增加仪式感
      setTimeout(() => {
        emit('confirm', { ...form.value })
        form.value = { name: '', description: '' }
        loading.value = false
      }, 500)
    }
    </script>
    
    <template>
      <transition name="drop-paper">
        <div v-if="visible" class="absolute inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm" @click.self="emit('close')">
          
          <div class="relative w-96 bg-[#fdfbf7] p-8 shadow-2xl rounded-sm transform rotate-1 paper-texture border border-gray-200">
            <div class="absolute -top-3 left-1/2 -translate-x-1/2 w-32 h-8 bg-yellow-200/80 shadow-sm transform -rotate-2"></div>
            
            <button @click="emit('close')" class="absolute top-2 right-2 text-gray-400 hover:text-red-500 transition-colors">
              <X class="w-5 h-5" />
            </button>
    
            <h3 class="text-xl font-serif font-black text-gray-800 mb-6 text-center border-b-2 border-gray-800 pb-2">
              {{ t('projects.createModal.title') }}
            </h3>
    
            <div class="space-y-6">
              <div class="relative group">
                <input 
                  v-model="form.name" 
                  type="text" 
                  :placeholder="t('projects.createModal.namePlaceholder')" 
                  class="w-full bg-transparent border-b border-gray-300 focus:border-blue-500 outline-none py-2 text-lg font-serif placeholder-gray-400 transition-colors"
                  autofocus
                />
                <PenTool class="absolute right-0 top-2 w-4 h-4 text-gray-300 group-focus-within:text-blue-500" />
              </div>
    
              <div class="relative">
                <textarea 
                  v-model="form.description" 
                  rows="3" 
                  :placeholder="t('projects.createModal.descriptionPlaceholder')" 
                  class="w-full bg-[#f3f4f6] rounded-lg p-3 text-sm outline-none resize-none border border-transparent focus:border-gray-300 focus:bg-white transition-all"
                ></textarea>
              </div>
    
              <button 
                @click="handleConfirm"
                :disabled="loading || !form.name"
                class="w-full py-3 bg-gray-800 text-white font-bold tracking-widest hover:bg-black transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg active:scale-95 transform duration-150"
              >
                <span v-if="loading">{{ t('projects.createModal.creating') }}</span>
                <span v-else class="flex items-center gap-2"><Check class="w-4 h-4" /> {{ t('projects.createModal.create') }}</span>
              </button>
            </div>
          </div>
        </div>
      </transition>
    </template>
    
    <style scoped>
    .paper-texture {
      background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' fill='%239C92AC' fill-opacity='0.05' fill-rule='evenodd'/%3E%3C/svg%3E");
    }
    .drop-paper-enter-active, .drop-paper-leave-active { transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
    .drop-paper-enter-from, .drop-paper-leave-to { opacity: 0; transform: scale(0.8) translateY(-50px) rotate(-10deg); }
    </style>
