<script setup lang="ts">
import { ref, reactive, onUnmounted, watch } from 'vue'
import { 
  Film, Scissors, Wand2, Play, Pause, X, Volume2, VolumeX, CheckCircle2 
} from 'lucide-vue-next'
import { useMessage } from '@/utils/useMessage'

const props = defineProps<{
  tracks: any[]
  currentTime: number
  totalDuration: number
  isPlaying: boolean
  volume: number
  isMuted: boolean
  playbackRate: number
}>()

const emit = defineEmits<{
  (e: 'update:tracks', value: any[]): void
  (e: 'seek', time: number): void
  (e: 'toggle-play'): void
  (e: 'update:volume', value: number): void
  (e: 'update:is-muted', value: boolean): void
  (e: 'update:playback-rate', value: number): void
  (e: 'open-library'): void
  (e: 'persist'): void
}>()

const message = useMessage()

const isClippingMode = ref(false)
const editingClipId = ref<number | null>(null)
const showVolumeSlider = ref(false)
const rulerRef = ref<HTMLElement | null>(null)

const vFocus = {
  mounted: (el: HTMLElement) => el.focus()
}

const volBtnRef = ref<HTMLElement | null>(null)
const volBarRef = ref<HTMLElement | null>(null)
const volumePopupPos = reactive({ x: 0, y: 0 })
const isDraggingVol = ref(false)

const toggleVolumeSlider = () => {
    showVolumeSlider.value = !showVolumeSlider.value
    if (showVolumeSlider.value && volBtnRef.value) {
        const rect = volBtnRef.value.getBoundingClientRect()
        volumePopupPos.x = rect.left + rect.width / 2
        volumePopupPos.y = rect.top - 10 
    }
}

const toggleMute = () => {
    emit('update:is-muted', !props.isMuted)
    if (!props.isMuted) emit('update:volume', 0)
    else emit('update:volume', 1)
}

const startVolumeDrag = (e: MouseEvent) => {
    isDraggingVol.value = true
    updateVolumeFromEvent(e)
    document.addEventListener('mousemove', onVolumeDragMove)
    document.addEventListener('mouseup', stopVolumeDrag)
}

const onVolumeDragMove = (e: MouseEvent) => {
    if (isDraggingVol.value) updateVolumeFromEvent(e)
}

const stopVolumeDrag = () => {
    isDraggingVol.value = false
    document.removeEventListener('mousemove', onVolumeDragMove)
    document.removeEventListener('mouseup', stopVolumeDrag)
}

const updateVolumeFromEvent = (e: MouseEvent) => {
    if (!volBarRef.value) return
    const rect = volBarRef.value.getBoundingClientRect()
    const height = rect.height
    const clickY = e.clientY
    const val = Math.max(0, Math.min(1, (rect.bottom - clickY) / height))
    
    emit('update:volume', val)
    if (val === 0) emit('update:is-muted', true)
    else emit('update:is-muted', false)
}

const togglePlaybackRate = () => {
    const rates = [0.5, 1.0, 1.5, 2.0]
    const currentIndex = rates.indexOf(props.playbackRate)
    const nextIndex = (currentIndex + 1) % rates.length
    emit('update:playback-rate', rates[nextIndex] as number)
}

const startRenaming = (clip: any) => {
    editingClipId.value = clip.id
}

const finishRenaming = () => {
    editingClipId.value = null
    emit('persist')
}

const clipDialog = reactive({
    visible: false,
    x: 0,
    y: 0,
    time: 0,
    maxTime: 0,
    targetTrackIndex: -1,
    targetClip: null as any
})

const handleClipClick = (trackIndex: number, clip: any, event: MouseEvent) => {
    if (!isClippingMode.value) return
    
    clipDialog.targetTrackIndex = trackIndex
    clipDialog.targetClip = clip
    clipDialog.maxTime = clip.duration
    clipDialog.time = Number((clip.duration / 2).toFixed(1))
    
    clipDialog.x = event.clientX
    clipDialog.y = event.clientY - 80 
    clipDialog.visible = true
}

const confirmSplit = () => {
    if (!clipDialog.targetClip) return
    
    const splitTime = Number(clipDialog.time)
    const clip = clipDialog.targetClip
    
    if (isNaN(splitTime) || splitTime <= 0 || splitTime >= clip.duration) {
        return message.warning('无效的时间点')
    }
    
    const track = props.tracks[clipDialog.targetTrackIndex]
    const clipIndex = track.items.findIndex((i: any) => i.id === clip.id)
    if (clipIndex === -1) return
    
    const cleanSrc = clip.src.split('#')[0]
    const currentStart = clip.startTime || 0
    
    const part1 = {
        ...clip,
        id: Date.now(),
        name: `${clip.name} (Part 1)`,
        duration: splitTime,
        startTime: currentStart,
    }
    
    const part2 = {
        ...clip,
        id: Date.now() + 1,
        name: `${clip.name} (Part 2)`,
        duration: clip.duration - splitTime,
        startTime: currentStart + splitTime
    }
    
    part1.src = `${cleanSrc}#t=${part1.startTime},${part1.startTime + part1.duration}`
    part2.src = `${cleanSrc}#t=${part2.startTime},${part2.startTime + part2.duration}`
    
    track.items.splice(clipIndex, 1, part1, part2)
    
    message.success('裁剪完成')
    emit('persist')
    
    clipDialog.visible = false
    isClippingMode.value = false 
}

const dropIndicator = reactive({
    visible: false,
    trackIndex: -1,
    left: 0,
    insertIndex: -1
})

const handleTrackDragOver = (e: DragEvent, trackIndex: number) => {
    e.preventDefault()
    if(e.dataTransfer) e.dataTransfer.dropEffect = 'move'
    
    const container = e.currentTarget as HTMLElement
    const children = Array.from(container.children).filter(el => {
        return el.classList.contains('group') && !el.classList.contains('pointer-events-none') 
    }) as HTMLElement[]

    const rect = container.getBoundingClientRect()
    const mouseX = e.clientX - rect.left 
    
    let closestIndex = children.length
    let closestLeft = 0
    
    if (children.length === 0) {
        closestIndex = 0
        closestLeft = 8 // pl-2
    } else {
        let found = false
        for (let i = 0; i < children.length; i++) {
            const el = children[i]
            if (el) {
                const elCenter = el.offsetLeft + el.offsetWidth / 2
                if (mouseX < elCenter) {
                    closestIndex = i
                    closestLeft = el.offsetLeft - 2 
                    found = true
                    break
                }
            }
        }
        if (!found) {
            const last = children[children.length - 1]
            if (last) {
                closestIndex = children.length
                closestLeft = last.offsetLeft + last.offsetWidth + 2
            }
        }
    }
    
    dropIndicator.visible = true
    dropIndicator.trackIndex = trackIndex
    dropIndicator.left = closestLeft
    dropIndicator.insertIndex = closestIndex
}

const handleTrackDragLeave = (e: DragEvent) => {
    const target = e.currentTarget as HTMLElement
    const related = e.relatedTarget as HTMLElement
    if (target.contains(related)) return
    dropIndicator.visible = false
}

const handleTrackDrop = async (e: DragEvent, trackIndex: number) => {
    dropIndicator.visible = false
    const insertIndex = dropIndicator.insertIndex !== -1 ? dropIndicator.insertIndex : -1
    
    const raw = e.dataTransfer?.getData('payload')
    const type = e.dataTransfer?.getData('type')
    
    // Reorder
    if (type === 'timeline-clip' && raw) {
         const { trackIndex: sourceTrackIndex, itemIndex: sourceItemIndex } = JSON.parse(raw)
         const sourceTrack = props.tracks[sourceTrackIndex]
         const targetTrack = props.tracks[trackIndex]
         
         if (sourceTrack.type !== targetTrack.type) return message.warning('不能跨不同类型的轨道移动')
         
         const item = sourceTrack.items[sourceItemIndex]
         
         let finalIndex = insertIndex
         if (insertIndex === -1) finalIndex = targetTrack.items.length

         if (sourceTrackIndex === trackIndex) {
             if (sourceItemIndex < finalIndex) {
                 finalIndex--
             }
         }

         sourceTrack.items.splice(sourceItemIndex, 1)
         targetTrack.items.splice(finalIndex, 0, item)
         
         emit('persist')
         return
    }

    if (e.dataTransfer?.files?.length) {
        const file = e.dataTransfer.files[0]
        if (file?.type.startsWith('audio/')) {
             if (props.tracks[trackIndex].type !== 'audio') {
                 message.warning('音频文件只能拖入音轨')
                 return
             }
             
             const newItem = {
                 id: Date.now(),
                 name: file.name,
                 duration: 10, 
                 type: 'audio',
                 src: URL.createObjectURL(file) 
             }

             if (insertIndex >= 0) props.tracks[trackIndex].items.splice(insertIndex, 0, newItem)
             else props.tracks[trackIndex].items.push(newItem)

             message.success('已添加音频')
             return
        }
    }

    if (raw) {
       try {
        const item = JSON.parse(raw)
        const targetTrack = props.tracks[trackIndex]
        
        if (targetTrack.type === 'video' && item.type !== 'video') {
             return message.warning('只能将视频拖入主轨道')
        }
        if (targetTrack.type === 'audio' && item.type !== 'audio') {
             return message.warning('只能将音频拖入音轨')
        }

        const newItem = {
          id: Date.now(),
          name: item.name,
          duration: item.duration || 5,
          type: item.type || 'video',
          src: item.src
        }

        if (insertIndex >= 0) targetTrack.items.splice(insertIndex, 0, newItem)
        else targetTrack.items.push(newItem)

        message.success(`已添加到轨道`)
        emit('persist')
       } catch(e) {}
    }
}

const handleClipDragStart = (e: DragEvent, trackIndex: number, itemIndex: number, _clip: any) => {
    if (e.dataTransfer) {
        e.dataTransfer.effectAllowed = 'move'
        e.dataTransfer.setData('type', 'timeline-clip')
        e.dataTransfer.setData('payload', JSON.stringify({ trackIndex, itemIndex }))
    }
}

const deleteTimelineItem = (trackIndex: number, itemId: number) => {
    const track = props.tracks[trackIndex]
    track.items = track.items.filter((i: any) => i.id !== itemId)
    emit('persist')
}

const isScrubbing = ref(false)
const wasPlayingBeforeScrub = ref(false)

const startScrubbing = (e: MouseEvent) => {
    e.stopPropagation()
    isScrubbing.value = true
    document.body.style.cursor = 'grabbing'
    
    wasPlayingBeforeScrub.value = props.isPlaying
    if (props.isPlaying) emit('toggle-play')

    updateTimeFromEvent(e)
    document.addEventListener('mousemove', onScrubDrag)
    document.addEventListener('mouseup', stopScrubbing)
}

const onScrubDrag = (e: MouseEvent) => {
    if (isScrubbing.value) updateTimeFromEvent(e)
}

const stopScrubbing = () => {
    isScrubbing.value = false
    document.body.style.cursor = ''
    document.removeEventListener('mousemove', onScrubDrag)
    document.removeEventListener('mouseup', stopScrubbing)
    
    if (wasPlayingBeforeScrub.value && !props.isPlaying) {
        emit('toggle-play')
    }
}

const updateTimeFromEvent = (e: MouseEvent) => {
    if (!rulerRef.value) return
    const rect = rulerRef.value.getBoundingClientRect()
    const clickX = e.clientX - rect.left
    const targetTime = Math.max(0, (clickX - 8) / 15)
    
    emit('seek', targetTime)
}

const handleTrackAreaClick = (e: MouseEvent) => {
    if (!rulerRef.value) return
    const rect = rulerRef.value.getBoundingClientRect()
    const clickX = e.clientX - rect.left
    const targetTime = Math.max(0, (clickX - 8) / 15)
    
    emit('seek', targetTime)
}

const formattedTime = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = Math.floor(seconds % 60)
    const ms = Math.floor((seconds % 1) * 100)
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`
}

const getVideoDuration = (src: string): Promise<number> => {
    return new Promise((resolve, reject) => {
        const video = document.createElement('video')
        video.preload = 'metadata'
        video.src = src
        video.onloadedmetadata = () => resolve(video.duration)
        video.onerror = reject
    })
}

const checkDurations = async () => {
    const videoTrack = props.tracks.find(t => t.type === 'video')
    if (!videoTrack) return

    for (const item of videoTrack.items) {
        if (!item.realDurationChecked && item.src) {
            try {
                const duration = await getVideoDuration(item.src)
                item.duration = duration
                item.realDurationChecked = true
            } catch (e) {
                console.warn('Failed to get duration for', item.name)
            }
        }
    }
    emit('persist')
}

watch(() => props.tracks.map(t => t.items.length), () => {
    checkDurations()
}, { deep: true })

const tooltipVisible = ref(false)
const tooltipText = ref('')
const tooltipPos = reactive({ x: 0, y: 0 })

const showTooltip = (e: MouseEvent, text: string) => {
    tooltipText.value = text
    tooltipVisible.value = true
    updateTooltipPos(e)
}
const hideTooltip = () => {
    tooltipVisible.value = false
}
const updateTooltipPos = (e: MouseEvent) => {
    if (!tooltipVisible.value) return
    tooltipPos.x = e.clientX
    tooltipPos.y = e.clientY - 40 
}

onUnmounted(() => {
    document.removeEventListener('mousemove', onScrubDrag)
    document.removeEventListener('mouseup', stopScrubbing)
    document.removeEventListener('mousemove', onVolumeDragMove)
    document.removeEventListener('mouseup', stopVolumeDrag)
})
</script>

<template>
  <footer class="rounded-[2rem] neu-flat shrink-0 relative overflow-hidden flex flex-col bg-[#E0E5EC] z-20 p-6">
       <div class="shrink-0 flex items-center justify-between pb-5 border-b border-gray-200/40 bg-[#E0E5EC]">
          <div class="flex items-center gap-4">
             <button 
               @click="emit('open-library')" 
               class="px-3 py-1.5 rounded-xl transition-all flex items-center gap-2 text-xs font-bold neu-flat hover:text-blue-500 text-gray-500"
             >
                <Film class="w-4 h-4" /> 素材库
             </button>
             <div class="w-px h-5 bg-gray-300 mx-1"></div>
              <div class="flex gap-3">
                <button 
                  @click="isClippingMode = !isClippingMode"
                  class="p-2 rounded-xl transition-all" 
                  :class="isClippingMode ? 'neu-pressed text-red-500' : 'neu-flat hover:text-blue-500 text-gray-500'"
                  title="剪辑模式 (点击开启后，点击视频块进行裁剪)"
                >
                   <Scissors class="w-4 h-4" />
                </button>
                <button class="p-2 rounded-xl neu-flat hover:text-purple-500 active:neu-pressed transition-all text-gray-500 cursor-not-allowed" title="转场效果(开发中)">
                  <Wand2 class="w-4 h-4" />
               </button>
               
               <div class="flex items-center gap-3 ml-4 pl-4 border-l border-gray-300/50">
                   
                   <div class="relative flex items-center justify-center">
                       <button 
                         ref="volBtnRef"
                         @click="toggleVolumeSlider" 
                         class="p-2 rounded-xl transition-all"
                         :class="showVolumeSlider ? 'neu-pressed text-blue-500' : 'neu-flat hover:text-blue-500 text-gray-500'"
                       >
                           <component :is="isMuted || volume === 0 ? VolumeX : Volume2" class="w-4 h-4" />
                       </button>
                   </div>

                   <button 
                     @click="emit('toggle-play')"
                     class="p-2 rounded-full neu-flat hover:text-blue-500 active:neu-pressed transition-all text-gray-500"
                   >
                       <component :is="isPlaying ? Pause : Play" class="w-4 h-4 fill-current" />
                   </button>

                   <button 
                     @click="togglePlaybackRate" 
                     class="flex items-center justify-center p-2 rounded-xl transition-all neu-flat hover:text-blue-500 text-gray-500 text-[10px] font-bold w-8 h-8"
                     title="倍速播放"
                   >
                       {{ playbackRate }}x
                   </button>

                   <span class="font-mono text-[10px] font-bold text-gray-400 min-w-[80px] text-center">
                       {{ formattedTime(currentTime) }} / {{ formattedTime(totalDuration) }}
                   </span>
               </div>

             </div>
          </div>
       </div>
       
       <div 
         class="flex-1 relative overflow-x-auto custom-scroll flex flex-col justify-center gap-3 bg-[#E0E5EC] py-2 pl-4"
         @click.self="handleTrackAreaClick"
       >
          
          <div class="relative min-w-full pb-4 pointer-events-none">
              
              <div class="h-6 w-full mb-2 relative select-none flex px-4 gap-4 z-20 pointer-events-auto">
                  <div class="w-20 shrink-0"></div>
                  
                  <div 
                    ref="rulerRef"
                    class="flex-1 relative cursor-pointer group/ruler pl-2 h-full z-30"
                    @mousedown="startScrubbing"
                  >
                      <div class="absolute inset-0 border-b border-white/20"></div>
                      <div class="absolute inset-0 overflow-hidden opacity-60 pointer-events-none">
                          <div 
                            class="h-full w-full"
                            style="background-image: 
                                repeating-linear-gradient(90deg, #a0aec0 0 1px, transparent 1px 15px),
                                repeating-linear-gradient(90deg, #ffffff 0 1px, transparent 1px 75px);
                                background-size: 75px 100%;
                                background-position-x: 8px;"
                          ></div>
                          <div 
                            class="absolute bottom-0 left-0 right-0 h-2 w-full opacity-40"
                            style="background-image: 
                                repeating-linear-gradient(90deg, transparent, transparent 14px, #a0aec0 14px, #a0aec0 15px, transparent 15px);
                                background-size: 15px 100%;"
                          ></div>
                      </div>
                      
                       <div 
                         class="absolute top-0 -ml-[7px] w-[15px] h-[24px] z-30 cursor-grab active:cursor-grabbing group/head flex flex-col items-center hover:scale-110 transition-transform"
                         :style="{ left: (currentTime * 15) + 15 + 'px', transform: isScrubbing ? 'translateX(-50%) scale(1.1)' : 'translateX(-50%)' }"
                         @mousedown.stop="startScrubbing"
                       >
                            <div class="w-full h-[14px] rounded-t-sm bg-gradient-to-b from-red-400 to-red-600 shadow-[0_2px_4px_rgba(0,0,0,0.3),inset_0_1px_2px_rgba(255,255,255,0.4)] border-x border-t border-red-300 relative flex items-center justify-center">
                                <div class="flex gap-0.5">
                                    <div class="w-px h-2 bg-red-800/20"></div>
                                    <div class="w-px h-2 bg-red-800/20"></div>
                                    <div class="w-px h-2 bg-red-800/20"></div>
                                </div>
                            </div>
                            <div class="w-0 h-0 border-l-[7px] border-l-transparent border-r-[7px] border-r-transparent border-t-[8px] border-t-red-600 drop-shadow-md -mt-[1px]"></div>
                       </div>
                  </div>
              </div>

              <div 
                 class="absolute top-6 bottom-0 w-px bg-red-500/50 z-10 pointer-events-none transition-transform duration-75 shadow-[0_0_4px_rgba(239,68,68,0.4)]"
                 :style="{ left: (120 + currentTime * 15) + 'px', height: (tracks.length * 80) + 'px' }" 
              ></div>

              <div class="flex flex-col gap-3 relative z-0 pointer-events-auto">
                  <div 
                    v-for="(track, index) in tracks" 
                    :key="track.id"
                    class="h-16 neu-pressed rounded-xl flex items-center px-4 gap-4 relative border border-white/20 shrink-0 min-w-full"
                  >

           <div class="w-20 text-[10px] font-bold text-gray-400 uppercase shrink-0 flex flex-col justify-center border-r border-gray-300/50 pr-4 select-none h-full">
             <span class="tracking-widest">{{ track.type === 'video' ? '主轨道' : '音频' }}</span>
           </div>
           
           <div 
             class="flex-1 h-full flex items-center relative overflow-hidden pl-2"
             @dragover="handleTrackDragOver($event, index)"
             @dragleave="handleTrackDragLeave"
             @drop="handleTrackDrop($event, index)"
             @click="handleTrackAreaClick"
           >
             <div v-if="track.items.length === 0" class="text-xs text-gray-400 font-bold italic select-none pointer-events-none opacity-50">
                {{ track.type === 'video' ? 'Drag videos here' : 'Drag audio here' }}
             </div>
             
             <div 
                v-if="dropIndicator.visible && dropIndicator.trackIndex === index"
                class="absolute top-2 bottom-2 w-1 bg-blue-500 z-50 rounded-full shadow-[0_0_8px_rgba(59,130,246,0.8)] pointer-events-none transition-all duration-75"
                :style="{ left: dropIndicator.left + 'px' }"
             ></div>

              <div 
                v-for="(clip, clipIndex) in track.items" 
                :key="clip.id"
                :draggable="editingClipId !== clip.id"
                class="h-10 rounded-lg flex items-center justify-center px-3 text-xs font-bold shadow-sm whitespace-nowrap hover:-translate-y-0.5 transition-all relative group border active:neu-pressed pr-6"
                :class="[
                    track.type === 'video' ? 'neu-flat text-blue-600 border-blue-100/10' : 'bg-green-100 border-green-200 text-green-700',
                    isClippingMode ? 'cursor-crosshair hover:bg-red-50 hover:border-red-200' : (editingClipId === clip.id ? '' : 'cursor-grab active:cursor-grabbing')
                ]"
                :style="{ width: (clip.duration * 15) + 'px' }" 
                @dragstart="(e) => handleClipDragStart(e, index, clipIndex as number, clip)"
                @click.stop="(e) => handleClipClick(index, clip, e)"
                @dblclick.stop="startRenaming(clip)"
                @mouseenter="(e) => showTooltip(e, clip.name)"
                @mouseleave="hideTooltip"
                @mousemove="updateTooltipPos"
              >
                <input 
                    v-if="editingClipId === clip.id"
                    v-model="clip.name"
                    @blur="finishRenaming"
                    @keydown.enter="finishRenaming"
                    @click.stop
                    v-focus
                    class="bg-transparent outline-none text-center w-full h-full z-20 relative min-w-[20px]"
                />
                <span v-else class="truncate max-w-full z-10 relative pointer-events-none">{{ clip.name }}</span>
                <button 
                    v-if="editingClipId !== clip.id"
                    @click.stop="deleteTimelineItem(index, clip.id)"
                    class="absolute top-1 right-1 p-0.5 rounded-full hover:bg-red-500 hover:text-white text-gray-400 opacity-0 group-hover:opacity-100 transition-all z-20"
                >
                    <X class="w-3 h-3" />
                </button>
                <div class="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-10 transition-opacity" :class="track.type === 'video' ? 'bg-blue-500' : 'bg-green-500'"></div>
              </div>
           </div>
          </div>
        </div>
       </div>
      </div>

      <Teleport to="body">
         <transition name="fade">
           <div 
             v-if="showVolumeSlider"
             class="fixed w-8 h-32 bg-[#E0E5EC] rounded-lg neu-flat flex flex-col items-center justify-end py-3 z-[120] border border-white/40 shadow-xl"
             :style="{ left: volumePopupPos.x + 'px', top: volumePopupPos.y + 'px', transform: 'translate(-50%, -100%)' }"
           >
               <div 
                 ref="volBarRef"
                 class="relative w-1.5 h-24 bg-gray-300 rounded-full overflow-hidden flex flex-col justify-end cursor-pointer group/track"
                 @mousedown="startVolumeDrag"
               >
                   <div 
                     class="w-full bg-blue-500 rounded-full group-hover/track:bg-blue-400 pointer-events-none"
                     :class="{ 'transition-all': !isDraggingVol }"
                     :style="{ height: (isMuted ? 0 : volume * 100) + '%' }"
                   ></div>
               </div>
               <button @click="toggleMute" class="mt-2 text-[10px] font-mono text-gray-500 hover:text-blue-500 font-bold">
                   {{ isMuted ? '0' : Math.round(volume * 100) }}
               </button>
           </div>
       </transition>
       <div v-if="showVolumeSlider" class="fixed inset-0 z-[115]" @click="showVolumeSlider = false"></div>

        <div 
            v-if="tooltipVisible"
            class="fixed px-3 py-1.5 bg-black/80 backdrop-blur-sm text-white text-xs rounded-lg pointer-events-none z-[100] shadow-xl border border-white/10"
            :style="{ left: tooltipPos.x + 'px', top: tooltipPos.y + 'px', transform: 'translate(-50%, -100%)' }"
        >
            {{ tooltipText }}
        </div>

        <!-- Clip Dialog (Split) -->
        <div 
            v-if="clipDialog.visible"
            class="fixed p-4 bg-[#E0E5EC] rounded-2xl shadow-2xl border border-white/40 z-[110] flex flex-col gap-3 w-64"
            :style="{ left: clipDialog.x + 'px', top: clipDialog.y + 'px', transform: 'translate(-50%, -100%)' }"
        >
            <div class="flex items-center justify-between">
                <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-2">
                    <Scissors class="w-3.5 h-3.5 text-blue-500" /> 裁剪视频
                </h4>
                <button @click="clipDialog.visible = false" class="p-1 rounded-full hover:bg-gray-200 text-gray-400"><X class="w-3.5 h-3.5" /></button>
            </div>
            
            <div class="flex flex-col gap-1">
                <label class="text-[10px] text-gray-400 font-bold ml-1">分割点 (秒)</label>
                <div class="flex items-center gap-2">
                    <input 
                        v-model="clipDialog.time" 
                        type="number" 
                        :max="clipDialog.maxTime" 
                        min="0"
                        step="0.1"
                        @keydown.enter="confirmSplit"
                        class="flex-1 px-3 py-2 rounded-xl neu-pressed text-sm font-bold text-gray-700 outline-none focus:ring-2 focus:ring-blue-400/30 transition-all text-center"
                        autofocus
                    />
                    <span class="text-xs text-gray-400 font-mono">/ {{ clipDialog.maxTime.toFixed(1) }}s</span>
                </div>
            </div>

            <button 
                @click="confirmSplit"
                class="w-full py-2 rounded-xl neu-flat hover:text-blue-500 active:neu-pressed transition-all text-xs font-bold flex items-center justify-center gap-2"
            >
                <CheckCircle2 class="w-3.5 h-3.5" /> 确认裁剪
            </button>
        </div>
    </Teleport>

  </footer>
</template>

<style scoped>
.custom-scroll::-webkit-scrollbar { width: 5px; height: 5px; }
.custom-scroll::-webkit-scrollbar-track { background: transparent; }
.custom-scroll::-webkit-scrollbar-thumb { background-color: #cbd5e0; border-radius: 10px; border: 1px solid #E0E5EC; }
.custom-scroll::-webkit-scrollbar-thumb:hover { background-color: #a0aec0; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>