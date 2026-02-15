<script setup lang="ts">
    import { useMessage } from '@/utils/useMessage'
    import { X, CheckCircle2, AlertCircle, Info } from 'lucide-vue-next'
    
    const { messages, remove } = useMessage()
    
    const getIcon = (type: string) => {
      switch (type) {
        case 'success': return CheckCircle2
        case 'error': return AlertCircle
        case 'warning': return AlertCircle
        default: return Info
      }
    }
    
    const getStyles = (type: string) => {
      switch (type) {
        case 'success': return 'border-l-4 border-green-500 text-green-800 bg-[#f0fdf4]'
        case 'error': return 'border-l-4 border-red-500 text-red-800 bg-[#fef2f2]'
        case 'warning': return 'border-l-4 border-orange-500 text-orange-800 bg-[#fff7ed]'
        default: return 'border-l-4 border-blue-500 text-blue-800 bg-[#eff6ff]'
      }
    }
    </script>
    
    <template>
      <div class="fixed top-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none">
        <transition-group name="slide-fade">
          <div 
            v-for="msg in messages" 
            :key="msg.id"
            class="pointer-events-auto w-80 p-4 rounded-sm shadow-lg paper-texture flex items-start gap-3 transform rotate-1 transition-all"
            :class="getStyles(msg.type)"
          >
            <component :is="getIcon(msg.type)" class="w-5 h-5 mt-0.5 shrink-0" />
            <div class="flex-1 text-sm font-bold font-serif leading-relaxed pt-0.5">
              {{ msg.text }}
            </div>
            <button @click="remove(msg.id)" class="opacity-50 hover:opacity-100">
              <X class="w-4 h-4" />
            </button>
          </div>
        </transition-group>
      </div>
    </template>
    
    <style scoped>
    .paper-texture {
      background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7z' fill='%23000000' fill-opacity='0.03' fill-rule='evenodd'/%3E%3C/svg%3E");
    }
    
    .slide-fade-enter-active { transition: all 0.4s ease-out; }
    .slide-fade-leave-active { transition: all 0.3s cubic-bezier(1, 0.5, 0.8, 1); }
    .slide-fade-enter-from { transform: translateX(20px); opacity: 0; }
    .slide-fade-leave-to { transform: translateX(20px); opacity: 0; }
    </style>