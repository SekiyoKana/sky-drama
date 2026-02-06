<script setup lang="ts">
import { X, Film } from 'lucide-vue-next'

defineProps<{
  visible: boolean
  videoUrl: string
  posterUrl?: string
}>()

const emit = defineEmits(['close'])
</script>

<template>
  <transition name="fade">
    <div v-if="visible" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="emit('close')">
      <div class="relative bg-[#E0E5EC] rounded-2xl shadow-2xl overflow-hidden max-w-4xl w-full mx-4 border border-white/40">
        <!-- Header -->
        <div class="px-4 py-3 bg-[#E0E5EC] border-b border-gray-200/40 flex items-center justify-between">
          <h3 class="font-bold text-gray-500 text-sm tracking-wider flex items-center gap-2 uppercase">
            <Film class="w-4 h-4 text-blue-400" /> 视频预览
          </h3>
          <button @click="emit('close')" class="p-1.5 rounded-full neu-flat hover:text-red-500 active:neu-pressed transition-all text-gray-400">
            <X class="w-4 h-4" />
          </button>
        </div>
        
        <!-- Video Player -->
        <div class="aspect-video bg-black flex items-center justify-center relative group">
          <video 
            v-if="videoUrl"
            :src="videoUrl" 
            :poster="posterUrl"
            controls 
            autoplay
            class="w-full h-full object-contain"
          ></video>
          <div v-else class="text-white/50 flex flex-col items-center gap-2">
            <Film class="w-10 h-10 opacity-50" />
            <span>暂无视频源</span>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
