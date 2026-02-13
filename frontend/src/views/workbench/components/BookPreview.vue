<script setup lang="ts">
  import { ref, computed, watch, nextTick } from 'vue'
  import { X, ChevronLeft, ChevronRight, Loader2, Info, ChevronDown, RefreshCcw, Image as ImageIcon, Video } from 'lucide-vue-next'
  import SmartText from './SmartText.vue'
  import NeuMentionSelector from '@/components/base/NeuMentionSelector.vue'
  import { useMention } from '@/utils/useMention'
  import { resolveImageUrl } from '@/utils/assets'
  
  const props = defineProps<{
    visible: boolean
    items: any[]
    initialIndex: number
    generatingItems: Record<string, number>
    allCharacters: any[]
    allScenes: any[]
    readonly?: boolean
  }>()
  
  const emit = defineEmits(['close', 'regenerate', 'update-item'])
  
  // Logical Index (The one officially active)
  const currentIndex = ref(0)
  const manualPrompt = ref('')
  
  // Editable fields for Character
  const editableName = ref('')
  const editableRole = ref('')
  const editableDesc = ref('')
  // Editable field for Scene/Storyboard prompt
  const editableScenePrompt = ref('')
  // Editable field for Scene/Storyboard Title (Location Name or Action)
  const editableTitle = ref('')
  
  // Generation Mode (Storyboard Only)
  const generationMode = ref<'single' | 'keyframes'>('single')
  
  // Edit Mode State for Scene Prompt
  const isEditingPrompt = ref(false)
  const promptInput = ref<HTMLTextAreaElement | null>(null)

  const enableEditPrompt = () => {
      isEditingPrompt.value = true
      nextTick(() => {
          promptInput.value?.focus()
      })
  }

  const finishEditPrompt = () => {
      setTimeout(() => {
          if (!isMentionVisible.value) {
              isEditingPrompt.value = false
              handlePromptUpdate()
          }
      }, 200)
  }

  // --- Mention Handling ---
  const { 
    isMentionVisible, 
    mentionX, 
    mentionY, 
    mentionQuery, 
    mentionStartIndex, 
    handleInput,
    closeMention: hideMention 
  } = useMention(promptInput)

  const mentionItems = computed(() => {
      const chars = props.allCharacters.map(c => ({ 
          id: c.id, 
          name: c.name, 
          type: 'character' as const, 
          image_url: resolveImageUrl(c.image_url || c.reference_image) 
      }))
      const scenes = props.allScenes.map(s => ({ 
          id: s.id, 
          name: s.location_name, 
          type: 'scene' as const, 
          image_url: resolveImageUrl(s.image_url || s.reference_image) 
      }))
      return [...chars, ...scenes]
  })

  const handleKeyDown = () => {}

  const handleSelectMention = (item: any) => {
      if (!promptInput.value) return
      
      const textarea = promptInput.value
      const val = textarea.value
      const start = mentionStartIndex.value
      const end = textarea.selectionStart
      const idStr = String(item.id)
      const targetPrefix = item.type === 'character' ? 'char_' : 'scene_'
      
      let finalId = idStr
      if (!idStr.startsWith(targetPrefix)) {
          finalId = `${targetPrefix}${idStr}`
      }
      
      const tag = `{{${finalId}}}`
      const newVal = val.substring(0, start) + tag + val.substring(end)
      
      editableScenePrompt.value = newVal
      hideMention()
      
      nextTick(() => {
          textarea.focus()
          const newCursorPos = start + tag.length
          textarea.setSelectionRange(newCursorPos, newCursorPos)
      })
  }

  const closeMention = () => {
      hideMention()
  }

  const isFlipping = ref(false)
  const flipDirection = ref<'next' | 'prev'>('next')
  const flipAngle = ref(0)
  
  const baseLeftItem = ref<any>(null)
  const baseRightItem = ref<any>(null)
  const flipperFrontItem = ref<any>(null)
  const flipperBackItem = ref<any>(null) 
  
  const currentKey = computed(() => {
    const item = props.items[currentIndex.value]
    if (!item) return ''
    if (item.role) return `chars-${currentIndex.value}`
    if (item.location_name) return `scenes-${currentIndex.value}`
    if (item.action) return `board-${currentIndex.value}`
    return ''
  })
  
  const isCurrentGenerating = computed(() => {
      return props.generatingItems[currentKey.value] !== undefined
  })
  
  const currentProgress = computed(() => {
      return props.generatingItems[currentKey.value] || 0
  })

  const isCharacterMode = computed(() => {
      const item = props.items[currentIndex.value]
      return item && !!item.role
  })

  const isStoryboardMode = computed(() => {
      const item = props.items[currentIndex.value]
      return item && !!item.action && !item.location_name
  })

  const promptPlaceholder = computed(() => {
      return isStoryboardMode.value
        ? '[出场人物]:\n[场景]:\n[分镜描述]:'
        : '[场景]:\n[场景描述]:'
  })

  watch(() => props.visible, (val) => {
    if (val) {
      currentIndex.value = props.initialIndex
      resetView(props.initialIndex)
    }
  })

  watch(currentIndex, () => {
      manualPrompt.value = ''
      syncEditableFields(props.items[currentIndex.value])
  })

  watch(() => props.items, (newItems) => {
      if (newItems && newItems[currentIndex.value]) {
          const currentItem = newItems[currentIndex.value]
          
          if (!isFlipping.value) {
              baseLeftItem.value = currentItem
              baseRightItem.value = currentItem
              syncEditableFields(currentItem)
          }
      }
  }, { deep: true })
  
  const syncEditableFields = (item: any) => {
      if (item) {
          if (item.role) {
             editableName.value = item.name || ''
             editableRole.value = item.role || ''
             editableDesc.value = item.description || ''
          } else {
             editableScenePrompt.value = item.visual_prompt || item.action || ''
             editableTitle.value = item.location_name || item.action || ''
          }
      }
  }

  const resetView = (idx: number) => {
    isFlipping.value = false
    flipAngle.value = 0
    baseLeftItem.value = props.items[idx]
    baseRightItem.value = props.items[idx]
    syncEditableFields(props.items[idx])
  }

  const handleRegenerate = (type: 'text' | 'image' | 'video') => {
      if (!baseRightItem.value) return
      
      const updates: any = {}
      if (baseLeftItem.value.role) { // Is Character
          if (editableName.value !== baseLeftItem.value.name) updates.name = editableName.value
          if (editableRole.value !== baseLeftItem.value.role) updates.role = editableRole.value
          if (editableDesc.value !== baseLeftItem.value.description) updates.description = editableDesc.value
      } else { // Scene/Storyboard
          if (editableScenePrompt.value !== (baseLeftItem.value.visual_prompt || baseLeftItem.value.action)) {
              updates.visual_prompt = editableScenePrompt.value
          }
      }

      emit('regenerate', { 
          type: type,
          item: baseRightItem.value, 
          index: currentIndex.value,
          extraPrompt: manualPrompt.value, // This is the "Instruction" box at bottom
          updates: Object.keys(updates).length ? updates : undefined,
          generationMode: isStoryboardMode.value ? generationMode.value : undefined
      })
  }

  const handlePromptUpdate = () => {
      if (baseRightItem.value) {
          // If character mode, right side prompt is editable
          // If scene mode, left side prompt is editable
          const newPrompt = isCharacterMode.value ? baseRightItem.value.visual_prompt : editableScenePrompt.value
          
          emit('update-item', {
              id: baseRightItem.value.id,
              visual_prompt: newPrompt
          })
      }
  }

  const handleInfoUpdate = () => {
      if (baseLeftItem.value) {
          const updates: any = {}
          
          if (baseLeftItem.value.role) {
              if (editableName.value !== baseLeftItem.value.name) updates.name = editableName.value
              if (editableRole.value !== baseLeftItem.value.role) updates.role = editableRole.value
              if (editableDesc.value !== baseLeftItem.value.description) updates.description = editableDesc.value
          } else {
              // Scene or Storyboard
              if (baseLeftItem.value.location_name !== undefined) {
                  // Scene
                  if (editableTitle.value !== baseLeftItem.value.location_name) {
                      updates.location_name = editableTitle.value
                  }
              } else if (baseLeftItem.value.action !== undefined) {
                  // Storyboard
                  if (editableTitle.value !== baseLeftItem.value.action) {
                      updates.action = editableTitle.value
                  }
              }
          }
          
          if (Object.keys(updates).length > 0) {
              emit('update-item', {
                  id: baseLeftItem.value.id,
                  ...updates
              })
              Object.assign(baseLeftItem.value, updates)
          }
      }
  }
  
  const next = () => {
    if (currentIndex.value >= props.items.length - 1 || isFlipping.value) return
    
    // Prepare "Next" Animation
    const current = props.items[currentIndex.value]
    const nextItem = props.items[currentIndex.value + 1]
    
    // 1. Setup Layers
    baseLeftItem.value = current
    baseRightItem.value = nextItem
    
    // Flipper (The moving leaf)
    flipperFrontItem.value = current
    flipperBackItem.value = nextItem
    
    // 2. Start Animation
    isFlipping.value = true
    flipDirection.value = 'next'
    
    // Force reflow
    setTimeout(() => {
        flipAngle.value = -180
    }, 20)
    
    // 3. Cleanup after CSS transition
    setTimeout(() => {
        currentIndex.value++
        resetView(currentIndex.value)
    }, 600) // Match CSS duration
  }
  
  const prev = () => {
    if (currentIndex.value <= 0 || isFlipping.value) return
    
    // Prepare "Prev" Animation
    const current = props.items[currentIndex.value]
    const prevItem = props.items[currentIndex.value - 1]
    
    // 1. Setup Layers
    baseLeftItem.value = prevItem
    baseRightItem.value = current
    
    // Flipper (The moving leaf)
    flipperFrontItem.value = prevItem
    flipperBackItem.value = current
    
    // 2. Start Animation
    isFlipping.value = true
    flipDirection.value = 'prev'
    // Start at Left (-180)
    flipAngle.value = -180
    
    // Force reflow then animate to 0
    setTimeout(() => {
        flipAngle.value = 0
    }, 20)
    
    // 3. Cleanup
    setTimeout(() => {
        currentIndex.value--
        resetView(currentIndex.value)
    }, 600)
  }
  </script>
  
  <template>
    <Teleport to="body">
      <transition name="fade">
        <div v-if="visible" class="fixed inset-0 z-[9999] bg-black/60 backdrop-blur-sm flex items-center justify-center p-8 perspective-container" @click="emit('close')">
          
          <button @click.stop="emit('close')" class="absolute top-6 right-6 p-2 rounded-full hover:bg-white/10 text-white transition-colors z-50">
             <X class="w-8 h-8" />
          </button>
  
          <!-- Book Container -->
          <div class="relative w-full max-w-5xl aspect-[1.6/1] flex z-10 select-none book-shadow" @click.stop>
            
            <!-- Character Mode Background (REMOVED) -->
            <!-- Background image removed to match scene style -->

            <!-- === LAYER 1: BASE (Static) === -->
             <!-- Base Left Page (Text) -->
             <div class="flex-1 rounded-l-2xl border-r border-gray-300 relative overflow-hidden flex flex-col justify-center items-center z-0 bg-[#f3f4f6]">
                <div class="absolute inset-0 pointer-events-none opacity-50 mix-blend-multiply" style="background-image: repeating-linear-gradient(transparent, transparent 31px, #e5e7eb 32px);"></div>
                <div class="p-8 h-full flex flex-col justify-center items-center relative z-10 w-full">
                   <div v-if="baseLeftItem" class="text-center space-y-4 max-w-md w-full flex flex-col items-center">
                      
                      <!-- Character Layout (Restored Standard Colors) -->
                      <div v-if="baseLeftItem.role" class="flex flex-col items-center w-full">
                          <!-- Editable Name -->
                          <div v-if="readonly" class="text-4xl font-serif font-bold text-gray-800 mb-2 text-center w-full">
                              {{ baseLeftItem.name }}
                          </div>
                          <input 
                             v-else
                             v-model="editableName"
                             class="text-4xl font-serif font-bold text-gray-800 mb-2 text-center bg-transparent border-b border-transparent hover:border-gray-300 focus:border-blue-400 focus:bg-white outline-none transition-all w-full"
                             @blur="handleInfoUpdate" 
                          />
                          
                          <!-- Editable Role Tag -->
                          <div class="mb-6 relative group/role">
                              <span v-if="readonly" class="px-3 py-1 bg-blue-100 text-blue-600 text-xs font-bold uppercase tracking-wider rounded-full border border-blue-200 shadow-sm text-center">
                                  {{ baseLeftItem.role }}
                              </span>
                              <input 
                                  v-else
                                  v-model="editableRole"
                                  @blur="handleInfoUpdate"
                                  class="px-3 py-1 bg-blue-100 text-blue-600 text-xs font-bold uppercase tracking-wider rounded-full border border-blue-200 shadow-sm text-center outline-none focus:ring-2 focus:ring-blue-300 transition-all w-auto min-w-[60px]"
                              />
                          </div>
                          
                          <div class="bg-white/60 p-4 rounded-xl shadow-sm border border-gray-200/60 w-full text-left relative group">
                              <!-- Editable Description -->
                              <div v-if="readonly" class="w-full text-sm text-gray-600 leading-relaxed font-serif italic h-32 overflow-y-auto custom-scroll p-2">
                                  {{ baseLeftItem.description }}
                              </div>
                              <textarea 
                                 v-else
                                 v-model="editableDesc"
                                 class="w-full text-sm text-gray-600 leading-relaxed font-serif italic bg-transparent border-none outline-none resize-none h-32 focus:bg-white/80 rounded-lg p-2 transition-colors placeholder-gray-400"
                                 @blur="handleInfoUpdate"
                              ></textarea>
                          </div>
                      </div>

                      <!-- Scene/Storyboard Layout (Standard Book) -->
                      <template v-else>
                          <div class="w-full flex flex-col gap-1 mb-2">
                             <span v-if="baseLeftItem.shot_id" class="text-xs font-bold text-gray-400 uppercase tracking-wider text-left">Shot {{ baseLeftItem.shot_id }}</span>
                             <div v-if="readonly" class="text-2xl font-serif font-bold text-gray-800 w-full pb-1 border-b border-transparent">
                                 {{ baseLeftItem.location_name || baseLeftItem.action }}
                             </div>
                             <input 
                                v-else
                                v-model="editableTitle"
                                class="text-2xl font-serif font-bold text-gray-800 bg-transparent border-b border-transparent hover:border-gray-300 focus:border-orange-400 outline-none transition-all w-full placeholder-gray-300"
                                :placeholder="baseLeftItem.location_name ? '场景名称...' : '分镜动作...'"
                                @blur="handleInfoUpdate"
                             />
                          </div>

                          <div 
                              class="bg-white/50 p-4 rounded-lg shadow-sm border border-white/60 w-full text-left h-40 overflow-y-auto custom-scroll relative group/edit"
                              :class="{'cursor-text': !readonly}"
                              @click="!readonly && enableEditPrompt()"
                          >
                              <textarea 
                                 v-if="isEditingPrompt && !readonly"
                                 ref="promptInput"
                                 v-model="editableScenePrompt"
                                 @blur="finishEditPrompt"
                                 @input="handleInput"
                                 @keydown="handleKeyDown"
                                 class="w-full h-full text-sm text-gray-600 font-mono leading-relaxed bg-transparent border-none outline-none resize-none focus:bg-transparent p-0"
                                 :placeholder="promptPlaceholder"
                              ></textarea>
                              <SmartText 
                                 v-else 
                                 :text="(!readonly && isEditingPrompt) ? editableScenePrompt : (baseLeftItem.visual_prompt || baseLeftItem.action)" 
                                 :characters="allCharacters" 
                                 :scenes="allScenes"
                                 class="font-mono text-sm leading-relaxed"
                              />
                              <span v-if="!readonly && !isEditingPrompt && !editableScenePrompt" class="text-gray-400 text-sm italic">Click to edit prompt...</span>

                              <NeuMentionSelector 
                                 v-if="!readonly"
                                 :visible="isMentionVisible"
                                 :x="mentionX"
                                 :y="mentionY"
                                 :filter-text="mentionQuery"
                                 :items="mentionItems"
                                 placement="top"
                                 @select="handleSelectMention"
                                 @close="closeMention"
                              />
                          </div>
                      </template>
                      
                          <!-- Manual Prompt Input Area (Instruction for Regeneration) -->
                      <div v-if="!readonly" class="w-full pt-6 border-t border-gray-200/50 flex flex-col gap-3">
                          <div class="flex items-center justify-between">
                              <label class="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                                 <span class="w-1.5 h-1.5 rounded-full" :class="isCharacterMode ? 'bg-blue-400' : 'bg-orange-400'"></span>
                                 重绘 / 优化提示词
                              </label>

                              <!-- Generation Mode Config (Storyboard Only) -->
                              <div v-if="isStoryboardMode" class="flex items-center gap-3 z-20">
                                   <span class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">生成模式</span>
                                   
                                   <!-- Neumorphic Dropdown -->
                                   <div class="relative group/dropdown">
                                       <div class="flex items-center bg-[#E0E5EC] rounded-xl shadow-[3px_3px_6px_#bec3c9,-3px_-3px_6px_#ffffff] px-3 py-1.5 transition-all hover:scale-[1.02] active:scale-[0.98] active:shadow-[inset_2px_2px_5px_#bec3c9,inset_-2px_-2px_5px_#ffffff] cursor-not-allowed border border-white/50">
                                           <select v-model="generationMode" class="appearance-none bg-transparent pr-5 text-[10px] font-bold text-gray-600 outline-none pointer-events-none w-full border-none">
                                              <option value="single">单图分镜</option>
                                              <option value="keyframes">关键帧</option>
                                              <option value="keyframes">首尾帧</option>
                                           </select>
                                           <ChevronDown class="w-3 h-3 text-gray-500 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
                                       </div>
                                   </div>

                                   <!-- Info Icon with Neumorphic Tooltip -->
                                   <div class="relative group/icon">
                                       <Info class="w-4 h-4 text-gray-400 cursor-help hover:text-blue-500 transition-colors" />
                                       
                                       <!-- Neumorphic Tooltip -->
                                       <div class="absolute text-left bottom-full right-0 mb-3 w-72 p-4 bg-[#E0E5EC] text-gray-600 text-xs rounded-xl shadow-[5px_5px_10px_#bec3c9,-5px_-5px_10px_#ffffff] opacity-0 group-hover/icon:opacity-100 transition-all pointer-events-none transform translate-y-2 group-hover/icon:translate-y-0 duration-300 leading-relaxed border border-white/50 z-50">
                                           <p class="mb-2 flex gap-2">
                                               <span class="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 shrink-0"></span>
                                               <span><strong class="text-blue-600">单图分镜：</strong>生成一张包含所有关键信息的图片，作为唯一参考。</span>
                                           </p>
                                           <p class="flex gap-2">
                                               <span class="w-1.5 h-1.5 rounded-full bg-purple-400 mt-1.5 shrink-0"></span>
                                               <span><strong class="text-purple-600">关键帧：</strong>每个关键帧生成一张图片，全部返回给视频模型，当视频模型支持多图参考时开启。</span>
                                           </p>
                                           <p class="flex gap-2">
                                               <span class="w-1.5 h-1.5 rounded-full bg-orange-400 mt-1.5 shrink-0"></span>
                                               <span><strong class="text-orange-600">首尾帧：</strong>每个关键帧生成一张图片，以首位帧方式多次返回给视频模型，十分消耗资源。（5张图片就会调用5次）</span>
                                           </p>
                                           
                                           <!-- Neumorphic Arrow -->
                                           <div class="absolute -bottom-1.5 right-1.25 w-3 h-3 bg-[#E0E5EC] rotate-45 border-r border-b border-gray-300/50"></div>
                                       </div>
                                   </div>
                              </div>
                          </div>

                          <textarea 
                             v-model="manualPrompt"
                             class="w-full h-24 bg-white/60 rounded-xl p-3 text-sm text-gray-700 placeholder-gray-400 resize-none border border-transparent focus:border-blue-300 focus:bg-white focus:ring-2 focus:ring-blue-100 transition-all outline-none leading-relaxed"
                             placeholder="在此输入补充描述，或留空直接重设..."
                             :disabled="isCurrentGenerating"
                          ></textarea>
                          
                          <div class="flex gap-2">
                              <!-- Regenerate Description Button (Text) -->
                              <button 
                                 @click="handleRegenerate('text')"
                                 :disabled="isCurrentGenerating"
                                 class="flex-1 py-2.5 rounded-xl bg-white border border-gray-200 text-gray-600 font-bold text-xs uppercase tracking-wide hover:bg-gray-50 active:scale-[0.98] transition-all flex items-center justify-center gap-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                                 title="重设提示词"
                                 aria-label="重设提示词"
                              >
                                 <Loader2 v-if="isCurrentGenerating" class="w-4 h-4 animate-spin" />
                                 <RefreshCcw v-else class="w-4 h-4" />
                              </button>

                              <!-- Regenerate Image Button (Image) -->
                              <button 
                                 @click="handleRegenerate('image')" 
                                 :disabled="isCurrentGenerating"
                                 class="flex-1 py-2.5 rounded-xl bg-gray-800 text-white font-bold text-xs uppercase tracking-wide hover:bg-gray-700 active:scale-[0.98] transition-all flex items-center justify-center gap-2 shadow-lg shadow-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                                 title="生成图片"
                                 aria-label="生成图片"
                              >
                                 <Loader2 v-if="isCurrentGenerating" class="w-4 h-4 animate-spin" />
                                 <ImageIcon v-else class="w-4 h-4" />
                              </button>

                              <!-- Regenerate Video Button (Video) - Storyboard Only -->
                              <button 
                                 v-if="isStoryboardMode"
                                 @click="handleRegenerate('video')" 
                                 :disabled="isCurrentGenerating"
                                 class="flex-1 py-2.5 rounded-xl font-bold text-xs uppercase tracking-wide active:scale-[0.98] transition-all flex items-center justify-center gap-2 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed bg-purple-600 text-white hover:bg-purple-500 shadow-purple-200"
                                 title="生成视频"
                                 aria-label="生成视频"
                              >
                                 <Loader2 v-if="isCurrentGenerating" class="w-4 h-4 animate-spin" />
                                 <Video v-else class="w-4 h-4" />
                              </button>
                          </div>
                      </div>

                   </div>
                </div>
             </div>

             <!-- Base Right Page (Image/Prompt) -->
             <div class="flex-1 rounded-r-2xl relative overflow-hidden bg-gray-50 z-0 group/right flex flex-col items-center justify-end">
                
                <!-- Loading Overlay -->
                <div v-if="isCurrentGenerating" class="absolute inset-0 z-50 bg-black/50 backdrop-blur-sm flex flex-col items-center justify-center text-white rounded-r-2xl">
                    <Loader2 class="w-10 h-10 animate-spin mb-4 text-blue-400" />
                    <span class="text-sm font-bold tracking-widest animate-pulse">GENERATING... {{ currentProgress }}%</span>
                </div>

                <template v-if="baseRightItem">
                    <!-- Image Container (Pushes up on hover) -->
                    <!-- Changed: Increase pb to 64 (16rem = 256px) for ~40% space -->
                    <div 
                       class="absolute inset-0 flex items-center justify-center p-4 transition-all duration-300 ease-out"
                       :class="isCharacterMode ? 'group-hover/right:pb-64 group-hover/right:scale-95' : ''"
                    >
                        <div class="aspect-video w-full h-full relative flex items-center justify-center">
                            <img 
                            v-if="baseRightItem.image_url || baseRightItem.reference_image" 
                            :src="resolveImageUrl(baseRightItem.image_url || baseRightItem.reference_image)" 
                            class="max-w-full max-h-full object-contain shadow-2xl rounded-lg"
                            />
                            <div v-else class="text-gray-400 text-sm flex flex-col items-center gap-2">
                                <Loader2 v-if="isCurrentGenerating" class="animate-spin" />
                                <span v-else>No Image</span>
                            </div>
                        </div>
                    </div>

                    <!-- Slide-up Prompt Panel (Character Only) -->
                    <!-- Changed: Increase height to 64 (16rem) -->
                    <div 
                       v-if="isCharacterMode" 
                       class="w-full bg-white/90 backdrop-blur-md border-t border-gray-200 shadow-xl transition-transform duration-300 ease-out translate-y-full group-hover/right:translate-y-0 absolute bottom-0 left-0 right-0 z-10 h-64 flex flex-col"
                    >
                        <div class="p-6 flex flex-col gap-3 flex-1">
                            <div class="flex items-center justify-between shrink-0">
                                <h3 class="text-xs font-bold text-gray-400 uppercase tracking-widest">Visual Prompt</h3>
                                <span class="text-[10px] text-gray-400">{{ readonly ? 'Read-only' : 'Editable' }}</span>
                            </div>
                            <div v-if="readonly" class="w-full flex-1 bg-gray-50 rounded-lg p-3 text-sm font-mono leading-relaxed text-gray-600 border border-gray-200 custom-scroll overflow-y-auto">
                                {{ baseRightItem.visual_prompt }}
                            </div>
                            <textarea 
                                v-else
                                v-model="baseRightItem.visual_prompt"
                                @blur="handlePromptUpdate"
                                class="w-full flex-1 bg-gray-50 rounded-lg p-3 text-sm font-mono leading-relaxed text-gray-600 outline-none resize-none border border-gray-200 focus:bg-white focus:border-blue-400 transition-all custom-scroll"
                            ></textarea>
                        </div>
                    </div>
                </template>
             </div>
  
            <!-- === LAYER 2: FLIPPER (Animation) === -->
            <div 
              v-if="isFlipping"
              class="absolute top-0 bottom-0 left-1/2 w-1/2 transform-style-3d origin-left transition-transform duration-500 ease-in-out z-20 pointer-events-none"
              :style="{ transform: `rotateY(${flipAngle}deg)` }"
            >
               <!-- Front Face (Image Side) -->
               <div class="absolute inset-0 bg-gray-50 rounded-r-2xl backface-hidden flex items-center justify-center overflow-hidden border-l border-gray-300 will-change-transform">
                  <template v-if="flipperFrontItem">
                      <div class="w-full h-full flex items-center justify-center p-4">
                          <img 
                            v-if="flipperFrontItem.image_url || flipperFrontItem.reference_image" 
                            :src="resolveImageUrl(flipperFrontItem.image_url || flipperFrontItem.reference_image)" 
                            class="max-w-full max-h-full object-contain rounded-lg"
                          />
                      </div>
                  </template>
                  <div class="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-black/10 to-transparent pointer-events-none"></div>
               </div>
  
               <!-- Back Face (Text Side) -->
               <div class="absolute inset-0 bg-[#f3f4f6] rounded-l-2xl backface-hidden flex flex-col justify-center items-center overflow-hidden border-r border-gray-300 will-change-transform" style="transform: rotateY(180deg);">
                  <div class="absolute inset-0 pointer-events-none opacity-50 mix-blend-multiply" style="background-image: repeating-linear-gradient(transparent, transparent 31px, #e5e7eb 32px);"></div>
                  <div class="p-8 h-full flex flex-col justify-center items-center relative z-10 w-full">
                      <div v-if="flipperBackItem" class="text-center space-y-4 max-w-md w-full flex flex-col items-center">
                        
                        <!-- Character Layout -->
                        <div v-if="flipperBackItem.role" class="flex flex-col items-center w-full">
                            <div class="w-24 h-24 rounded-full bg-white shadow-md border-4 border-white flex items-center justify-center text-4xl font-bold text-blue-500 mb-4">
                                {{ flipperBackItem.name?.[0] }}
                            </div>
                            <h2 class="text-3xl font-serif font-bold text-gray-800 mb-1">{{ flipperBackItem.name }}</h2>
                            <span class="px-3 py-1 bg-blue-100 text-blue-600 text-xs font-bold uppercase tracking-wider rounded-full mb-6">{{ flipperBackItem.role }}</span>
                        </div>

                        <!-- Scene/Storyboard Layout -->
                        <template v-else>
                            <h2 class="text-2xl font-serif font-bold text-gray-800">{{ flipperBackItem.location_name || `Shot ${flipperBackItem.shot_id}` }}</h2>
                            <div class="text-sm text-gray-600 font-mono leading-relaxed bg-white/50 p-4 rounded-lg shadow-sm border border-white/60 w-full text-left">
                                <SmartText 
                                   :text="flipperBackItem.visual_prompt || flipperBackItem.action" 
                                   :characters="allCharacters" 
                                   :scenes="allScenes"
                                />
                            </div>
                        </template>
                      </div>
                  </div>
                  <div class="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-black/10 to-transparent pointer-events-none"></div>
               </div>
            </div>
  
            <!-- === CONTROLS === -->
            <button 
              v-if="currentIndex > 0 && !isFlipping" 
              @click="prev" 
              class="absolute -left-16 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white transition-all backdrop-blur-sm z-50"
            >
               <ChevronLeft class="w-8 h-8" />
            </button>
            <button 
              v-if="currentIndex < items.length - 1 && !isFlipping" 
              @click="next" 
              class="absolute -right-16 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white transition-all backdrop-blur-sm z-50"
            >
               <ChevronRight class="w-8 h-8" />
            </button>
  
          </div>
        </div>
      </transition>
    </Teleport>
  </template>
  
  <style scoped>
  .perspective-container { perspective: 2000px; }
  .transform-style-3d { transform-style: preserve-3d; }
  .backface-hidden { backface-visibility: hidden; -webkit-backface-visibility: hidden; }
  .origin-left { transform-origin: left center; }
  
  .book-shadow { filter: drop-shadow(0 20px 40px rgba(0,0,0,0.5)); }
  
  .fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
  .fade-enter-from, .fade-leave-to { opacity: 0; }

  .custom-scroll::-webkit-scrollbar { width: 4px; }
  .custom-scroll::-webkit-scrollbar-thumb { background-color: #cbd5e0; border-radius: 4px; }
  </style>
