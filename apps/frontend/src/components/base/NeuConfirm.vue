<script setup lang="ts">
import { AlertTriangle, Check, X } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import NeuButton from '@/components/base/NeuButton.vue'
import { useConfirm } from '@/utils/useConfirm'

const { state, confirm, cancel } = useConfirm()
const { t } = useI18n()
</script>

<template>
  <transition name="fade">
    <div v-if="state.visible" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm">
      <div class="bg-[#E0E5EC] rounded-[2rem] p-6 w-full max-w-sm border border-white/50 flex flex-col gap-4 relative overflow-hidden">
        
        <!-- Header -->
        <div class="flex items-center gap-3 text-orange-500">
          <div class="w-10 h-10 rounded-full neu-flat flex items-center justify-center shrink-0">
            <AlertTriangle class="w-5 h-5" />
          </div>
          <h3 class="font-bold text-gray-700 text-lg tracking-wide">{{ state.title }}</h3>
        </div>

        <!-- Content -->
        <p class="text-gray-600 text-sm leading-relaxed pl-1 whitespace-pre-line break-words">
          {{ state.message }}
        </p>

        <!-- Actions -->
        <div class="flex gap-3 mt-2">
          <NeuButton 
            class="flex-1 py-3 text-sm font-bold text-gray-500" 
            @click="cancel"
          >
            <X class="w-4 h-4 mr-2" />
            {{ t('confirm.cancel') }}
          </NeuButton>
          <NeuButton 
            variant="primary" 
            class="flex-1 py-3 text-sm font-bold text-red-500 bg-red-50 border-red-100 hover:text-red-600" 
            @click="confirm"
          >
            <Check class="w-4 h-4 mr-2" />
            {{ t('confirm.confirm') }}
          </NeuButton>
        </div>

      </div>
    </div>
  </transition>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
