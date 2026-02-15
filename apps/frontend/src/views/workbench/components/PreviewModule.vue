<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { Monitor, Smartphone, Play, Pause, Film, SkipForward, SkipBack } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  timeline?: any[]
}>()

const emit = defineEmits(['drop', 'update-item', 'time-update', 'duration-update', 'play-state-change'])
const { t } = useI18n()

const isPlaying = ref(false)
const aspectRatio = ref<'16:9' | '9:16'>('16:9')
const videoRef = ref<HTMLVideoElement | null>(null)
const currentIndex = ref(0)
const currentTime = ref(0)
const volume = ref(1)
const isMuted = ref(false)
const playbackRate = ref(1.0)

const playlist = computed(() => {
  if (!props.timeline) return []
  // Find the video track (assuming track type 'video' or id 1)
  const videoTrack = props.timeline.find(t => t.type === 'video')
  return videoTrack ? videoTrack.items : []
})

const currentClip = computed(() => {
  if (!playlist.value.length) return null
  return playlist.value[currentIndex.value]
})

const totalDuration = computed(() => {
    return playlist.value.reduce((acc: any, item: any) => acc + (item.duration || 0), 0)
})

watch(totalDuration, (val) => {
    emit('duration-update', val)
})

const togglePlay = () => {
  if (!videoRef.value || !currentClip.value) return
  if (isPlaying.value) {
    videoRef.value.pause()
  } else {
    videoRef.value.play()
  }
  isPlaying.value = !isPlaying.value
  emit('play-state-change', isPlaying.value)
}

const handleEnded = () => {
  if (currentIndex.value < playlist.value.length - 1) {
    // Reset time immediately to next clip start to avoid progress bar glitch
    const nextClip = playlist.value[currentIndex.value + 1]
    currentTime.value = nextClip.startTime || 0
    currentIndex.value++
    // Auto play next
    setTimeout(() => {
        if(videoRef.value) {
            videoRef.value.play()
            applyGlobalSettings() // Apply rate and volume to new video source/play
        }
    }, 100)
  } else {
    isPlaying.value = false
    emit('play-state-change', false)
    // Do not reset index, stop at end
  }
}

const setVolume = (val: number) => {
    volume.value = val
    if (videoRef.value) videoRef.value.volume = val
    isMuted.value = val === 0
}

const setPlaybackRate = (rate: number) => {
    playbackRate.value = rate
    if (videoRef.value) videoRef.value.playbackRate = rate
}

const applyGlobalSettings = () => {
    if (!videoRef.value) return
    videoRef.value.volume = isMuted.value ? 0 : volume.value
    videoRef.value.playbackRate = playbackRate.value
}

const handleTimeUpdate = () => {
    if(videoRef.value && currentClip.value) {
        currentTime.value = videoRef.value.currentTime
        
        // Calculate Global Time
        let timeBefore = 0
        for (let i = 0; i < currentIndex.value; i++) {
            timeBefore += playlist.value[i].duration || 0
        }
        
        const clipStartTime = currentClip.value.startTime || 0
        const timeInClip = Math.max(0, currentTime.value - clipStartTime)
        const globalCurrentTime = timeBefore + timeInClip
        
        emit('time-update', globalCurrentTime)
    }
}

const handleLoadedMetadata = () => {
    if (videoRef.value && currentClip.value) {
        const realDuration = videoRef.value.duration
        if (realDuration && Math.abs(realDuration - (currentClip.value.duration || 0)) > 0.5) {
             emit('update-item', { 
                 trackId: 1, // Assumption: video track is id 1
                 itemId: currentClip.value.id, 
                 updates: { duration: realDuration } 
             })
        }
    }
}

const seek = (targetGlobalTime: number) => {
    // Find target clip
    let accumulatedTime = 0
    for (let i = 0; i < playlist.value.length; i++) {
        const clipDuration = playlist.value[i].duration || 0
        if (targetGlobalTime <= accumulatedTime + clipDuration + 0.1) { // 0.1 buffer
            // Found clip
            if (currentIndex.value !== i) {
                currentIndex.value = i
                // When switching clip via seek, wait for load then apply settings
                setTimeout(() => { 
                    applyGlobalSettings()
                }, 50)
            }
            
            const seekTimeInClip = Math.max(0, targetGlobalTime - accumulatedTime)
            
            // Wait for video element update then seek
            // Use nextTick equivalent or setTimeout
            setTimeout(() => {
                if (videoRef.value) {
                    // Add start time offset
                    const startOffset = playlist.value[i].startTime || 0
                    videoRef.value.currentTime = startOffset + seekTimeInClip
                    // Ensure settings are applied (especially rate)
                    applyGlobalSettings()
                }
            }, 0)
            return
        }
        accumulatedTime += clipDuration
    }
}

defineExpose({
    seek,
    setVolume,
    setPlaybackRate,
    togglePlay,
    isPlaying
})

// Watch for playlist changes to reset if empty or changed significantly
watch(playlist, (newVal) => {
    if (newVal.length === 0) {
        currentIndex.value = 0
        isPlaying.value = false
        emit('play-state-change', false)
        if(videoRef.value) videoRef.value.src = ''
    } else if (!currentClip.value) {
        currentIndex.value = 0
    }
}, { deep: true })

</script>

<template>
  <main 
    class="flex-1 flex flex-col gap-6 min-w-30 h-full"
    @dragover.prevent
    @drop="emit('drop', $event)"
  >
    <div class="flex-1 rounded-[2.5rem] neu-flat p-4 relative flex flex-col overflow-hidden">
      <div class="h-10 mb-2 flex items-center justify-between px-4 border-b border-transparent select-none">
         <div class="flex items-center gap-2">
            <Film class="w-4 h-4 text-gray-400" />
            <span class="font-bold text-gray-600 text-s tracking-wider">{{ t('workbench.previewModule.title') }}</span>
         </div>
         <div class="flex bg-[#E0E5EC] rounded-lg neu-pressed-sm p-1">
               <button 
                @click="aspectRatio = '16:9'" 
                class="p-1.5 rounded-md transition-all" 
                :class="aspectRatio === '16:9' ? 'neu-flat-sm text-blue-500' : 'text-gray-400 hover:text-gray-600'"
                :title="t('workbench.previewModule.ratioLandscape')"
               >
                <Monitor class="w-4 h-4" />
               </button>
               <button 
                @click="aspectRatio = '9:16'" 
                class="p-1.5 rounded-md transition-all" 
                :class="aspectRatio === '9:16' ? 'neu-flat-sm text-blue-500' : 'text-gray-400 hover:text-gray-600'"
                :title="t('workbench.previewModule.ratioPortrait')"
               >
                <Smartphone class="w-4 h-4" />
               </button>
             </div>
      </div>

      <div class="flex-1 min-h-0 flex items-center justify-center overflow-hidden">
        <div 
          class="rounded-4xl bg-black shadow-inner relative flex items-center justify-center group h-full transition-all duration-500 border border-gray-700 max-w-full overflow-hidden"
          :class="{ 'aspect-video': aspectRatio === '16:9', 'aspect-9/16': aspectRatio === '9:16' }"
        >
          <video 
            v-if="currentClip"
            ref="videoRef"
            :src="currentClip.src"
            class="w-full h-full object-contain"
            @ended="handleEnded"
            @timeupdate="handleTimeUpdate"
            @loadedmetadata="handleLoadedMetadata; applyGlobalSettings()"
            @play="isPlaying = true; emit('play-state-change', true); applyGlobalSettings()"
            @pause="isPlaying = false; emit('play-state-change', false)"
          ></video>
          <p v-else class="text-gray-600 font-mono text-sm">{{ t('workbench.previewModule.noSignal') }}</p>
          
          <!-- Controls Overlay -->
          <div v-if="currentClip" class="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-4">
              <button @click="currentIndex = Math.max(0, currentIndex - 1)" class="p-3 rounded-full bg-white/10 backdrop-blur-md text-white hover:scale-110 transition-transform">
                  <SkipBack class="w-5 h-5 fill-current" />
              </button>
              <button @click="togglePlay" class="p-6 rounded-full bg-white/20 backdrop-blur-md text-white hover:scale-110 transition-transform">
                <component :is="isPlaying ? Pause : Play" class="w-8 h-8 fill-current" />
              </button>
              <button @click="currentIndex = Math.min(playlist.length - 1, currentIndex + 1)" class="p-3 rounded-full bg-white/10 backdrop-blur-md text-white hover:scale-110 transition-transform">
                  <SkipForward class="w-5 h-5 fill-current" />
              </button>
          </div>
          
          <!-- Clip Info -->
          <div v-if="currentClip" class="absolute top-4 left-4 bg-black/50 px-2 py-1 rounded text-xs text-white/80 font-mono">
              {{ t('workbench.previewModule.clipLabel', { current: currentIndex + 1, total: playlist.length }) }}
          </div>
        </div>
      </div>
    </div>
  </main>
</template>
