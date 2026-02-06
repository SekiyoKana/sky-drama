<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { 
  User, Image as ImageIcon,
  GripVertical, Film
} from 'lucide-vue-next'
import NeuButton from '@/components/base/NeuButton.vue'
import { useMessage } from '@/utils/useMessage'
import { useConfirm } from '@/utils/useConfirm'
import { debugLogger } from '@/utils/debugLogger'
import BookPreview from './BookPreview.vue'
import CharacterCreateModal from './CharacterCreateModal.vue'
import VideoPreviewModal from './VideoPreviewModal.vue'
import { aiApi } from '@/api'
import { useRoute } from 'vue-router'

import ScriptCharacters from './ScriptCharacters.vue'
import ScriptScenes from './ScriptScenes.vue'
import ScriptStoryboard from './ScriptStoryboard.vue'

const props = defineProps<{
  width: number
  data: any
}>()

const emit = defineEmits(['handle-down', 'drag-start', 'generate-media', 'request-save', 'init-data', 'stream-message', 'stream-start', 'stream-end'])
const message = useMessage()
const { show: showConfirm } = useConfirm()
const route = useRoute()

const activeTab = ref<'chars' | 'scenes' | 'board'>('chars')
const generatingItems = reactive<Record<string, number>>({}) // id -> progress (0-100) or undefined

// --- Preview State ---
const previewVisible = ref(false)
const previewIndex = ref(0)
const previewList = ref<any[]>([])

// --- Video Preview State ---
const videoPreviewVisible = ref(false)
const currentVideoUrl = ref('')
const currentVideoPoster = ref('')

const openVideoPreview = (url: string, poster?: string) => {
    if (!url) return
    currentVideoUrl.value = url
    currentVideoPoster.value = poster || ''
    videoPreviewVisible.value = true
}

const tabs = [
  { id: 'chars', icon: User, label: '角色' },
  { id: 'scenes', icon: ImageIcon, label: '场景' },
  { id: 'board', icon: GripVertical, label: '分镜' }
]

const standardizedData = computed(() => {
  if (!props.data) return null
  const root = props.data.generated_script || props.data
  return {
    title: root.meta?.project_title || 'Untitled Project',
    description: root.meta?.core_premise || '',
    characters: root.characters || [],
    scenes: root.scenes || [],
    storyboard: root.storyboard || []
  }
})

// --- Actions ---

const showCharModal = ref(false)

const handleAddItem = async (type: 'chars' | 'scenes' | 'board') => {
    if (!props.data) {
        const newData = {
            meta: { project_title: 'New Project' },
            characters: [],
            scenes: [],
            storyboard: []
        }
        emit('init-data', newData)
        return
    }

    if (type === 'chars') {
        showCharModal.value = true
        return
    }

    const root = props.data.generated_script || props.data
    
    // Ensure arrays exist
    if (!root.characters) root.characters = []
    if (!root.scenes) root.scenes = []
    if (!root.storyboard) root.storyboard = []

    const uuid = crypto.randomUUID()

    if (type === 'scenes') {
        const timestamp = Math.floor(Date.now() / 1000)
        const suffix = crypto.randomUUID().substring(0, 4)
        const index = root.scenes.length
        
        const newScene = {
            id: `scene_${timestamp}_${index}_${suffix}`,
            location_name: '新场景',
            mood: '中性',
            visual_prompt: '请点击此处编辑场景描述...',
            image_url: ''
        }
        root.scenes.push(newScene)
        emit('request-save')
        
        // Open preview immediately for editing
        openPreview(root.scenes, index)
        
    } else if (type === 'board') {
        const nextId = (root.storyboard.length + 1).toString()
        const newShot = {
            id: `storyboard_${uuid}`,
            shot_id: nextId,
            action: '新分镜',
            shot_type: '全景',
            visual_prompt: '请点击此处编辑分镜画面...',
            image_url: ''
        }
        root.storyboard.push(newShot)
        emit('request-save')

        // Open preview immediately for editing
        const index = root.storyboard.length - 1
        openPreview(root.storyboard, index)
    }
}

const handleEditItem = (type: 'chars' | 'scenes' | 'board', item: any) => {
    const root = props.data.generated_script || props.data
    let list: any[] = []
    
    if (type === 'chars') {
         list = root.characters
         const idx = list.findIndex((i: any) => i.id === item.id)
         if (idx !== -1) openPreview(list, idx)
    } else if (type === 'scenes') {
         list = root.scenes
         const idx = list.findIndex((i: any) => i.id === item.id)
         if (idx !== -1) openPreview(list, idx)
    } else if (type === 'board') {
         list = root.storyboard
         const idx = list.findIndex((i: any) => i.id === item.id)
         if (idx !== -1) openPreview(list, idx)
    }
}


const handleCharConfirm = (charData: any) => {
    // Existing logic for chars...
    const root = props.data.generated_script || props.data
    if (!root.characters) root.characters = []
    
    const timestamp = Math.floor(Date.now() / 1000)
    const suffix = crypto.randomUUID().substring(0, 4)
    const index = root.characters.length

    const newChar = {
        id: `char_${timestamp}_${index}_${suffix}`,
        name: charData.name,
        role: charData.role,
        description: charData.description,
        image_url: ''
    }
    root.characters.push(newChar)
    showCharModal.value = false
    emit('request-save')
}

const handleDeleteItem = async (type: 'chars' | 'scenes' | 'board', index: number, _item: any) => {
    const confirmed = await showConfirm('确定要删除吗？')
    if (!confirmed) return
    
    try {
        const root = props.data.generated_script || props.data
        const list = type === 'chars' ? root.characters : 
                     type === 'scenes' ? root.scenes : 
                     root.storyboard
                     
        if (list) {
            list.splice(index, 1)
            emit('request-save')
            message.success('已删除')
        }
    } catch (e) {
        console.error(e)
        message.error('删除失败')
    }
}


const handleUpdateItem = async (itemId: string, updates: any) => {
    // Optimistic local update
    try {
        const root = props.data.generated_script || props.data
        const findAndUpdate = (list: any[]) => {
            if (!list) return false
            const item = list.find((i: any) => i.id === itemId)
            if (item) {
                Object.assign(item, updates)
                return true
            }
            return false
        }
        findAndUpdate(root.characters) || findAndUpdate(root.scenes) || findAndUpdate(root.storyboard)

        await aiApi.updateScriptItem({
            episode_id: Number(route.params.episodeId),
            item_id: itemId,
            updates: updates
        })
    } catch (e) {
        console.error("Update failed", e)
        message.error("更新失败")
    }
}

// Handler for updates from BookPreview (e.g. editable prompt, name, desc)
const handlePreviewUpdate = (payload: any) => {
    const { id, ...updates } = payload
    handleUpdateItem(id, updates)
}

const handleGenerate = async (type: 'image' | 'video' | 'text', item: any, index: number, extraPrompt?: string, updates?: any, generationMode?: string) => {
  const itemId = `${activeTab.value}-${index}`
  if (generatingItems[itemId] !== undefined) return

  // If there are updates (name/desc), save them first
  if (updates && item.id) {
      await handleUpdateItem(item.id, updates)
      // Update local item reference to reflect changes immediately in UI
      Object.assign(item, updates)
  }

  generatingItems[itemId] = 0 // Start progress
  message.info(`开始生成 ${type === 'image' ? '图片' : (type === 'video' ? '视频' : '提示词')}...`)

  // Construct prompt
  let finalPrompt = item.visual_prompt || item.description || item.action || 'No prompt'
  if (type === 'text') {
      // Prompt Refinement Logic
      const parts = []
      
      // 1. Original Context
      if (activeTab.value === 'chars') {
          parts.push(`[Character Info]\nName: ${item.name}\nDescription: ${item.description}`)
      } else if (activeTab.value === 'scenes') {
          parts.push(`[Scene Info]\nLocation: ${item.location_name}\nMood: ${item.mood}`)
      } else if (activeTab.value === 'board') {
          parts.push(`[Shot Info]\nAction: ${item.action}\nType: ${item.shot_type}`)
      }
      
      // 2. Current Visual Prompt (if exists)
      if (item.visual_prompt) {
          parts.push(`[Current Visual Prompt]\n${item.visual_prompt}`)
      }
      
      // 3. User Instruction (or default)
      if (extraPrompt) {
          parts.push(`[Refinement Instruction]\n${extraPrompt}`)
      } else {
          parts.push(`[Instruction]\nOptimize the visual prompt for better image generation consistency and detail.`)
      }
      
      finalPrompt = parts.join('\n\n')
  } else {
      if (extraPrompt) {
          finalPrompt = `${finalPrompt}. 要求: ${extraPrompt}`
      }
  }

  try {
      const payloadType = type === 'text' ? 'text' : type;      
      // Filter context based on usage in prompt
      const allChars = standardizedData.value?.characters || []
      const allScenes = standardizedData.value?.scenes || []
      const contextCharacters = allChars.filter((c: any) => c.id && finalPrompt.includes(c.id))
      const contextScenes = allScenes.filter((s: any) => s.id && finalPrompt.includes(s.id))

      const data: any = { 
          category: activeTab.value === 'chars' ? 'character' : (activeTab.value === 'scenes' ? 'scene' : 'storyboard'),
          context_characters: contextCharacters,
          context_scenes: contextScenes
      }

      if (generationMode) {
          data.generation_mode = generationMode
      }

      if (type === 'video' && item.image_url) {
          data.input_reference = item.image_url
      }
      console.log(type, payloadType, finalPrompt, data)
      await aiApi.skillsStream({
          projectId: Number(route.params.projectId),
          episodeId: Number(route.params.episodeId),
          prompt: finalPrompt,
          type: payloadType, 
          skill: type === 'text' ? 'short-video-prompt-engineer' : undefined,
          data: data
      } as any, {
          onMessage: (msg) => {
              if (msg.type === 'progress') {
                  generatingItems[itemId] = msg.payload
              } else if (msg.type === 'finish') {
                  if (type === 'image' || type === 'video') {
                      let url = '';
                      if (typeof msg.payload === 'string') {
                          try {
                              const json = JSON.parse(msg.payload);
                              url = json.url;
                          } catch (e) {
                              if (msg.payload.startsWith('http')) url = msg.payload;
                          }
                      } else if (msg.payload?.url) {
                          url = msg.payload.url;
                      }

                      if (url) {
                          if (type === 'video') {
                              item.video_url = url
                              handleUpdateItem(item.id, { video_url: url })
                          } else {
                              item.image_url = url
                              handleUpdateItem(item.id, { image_url: url })
                          }
                          
                          let mediaName = `${type}-${index}`
                          if (item.action) mediaName = item.action
                          else if (item.name) mediaName = item.name
                          else if (item.location_name) mediaName = item.location_name

                          emit('generate-media', {
                              type: type,
                              src: url,
                              name: mediaName,
                              duration: 5,
                              refData: item
                          })
                      }
                  } 
                  
                  if (msg.type === 'message' && type === 'text') {
                       item.visual_prompt = msg.payload
                  }
                  if (msg.type === 'finish' && type === 'text' && typeof msg.payload === 'string') {
                       item.visual_prompt = msg.payload
                  }

                  message.success('生成成功')
                  delete generatingItems[itemId]
                  
                  if (type === 'text' && item.visual_prompt) {
                      handleUpdateItem(item.id, { visual_prompt: item.visual_prompt })
                  }

              } else if (msg.type === 'text_finish') {
                  // Handle plain text completion (prompt refinement fallback)
                  let refinedPrompt = ''
                  if (typeof msg.payload === 'string') {
                      refinedPrompt = msg.payload
                  } else if (msg.payload?.text) {
                      refinedPrompt = msg.payload.text
                  }

                  if (refinedPrompt) {
                      item.visual_prompt = refinedPrompt
                      handleUpdateItem(item.id, { visual_prompt: refinedPrompt })
                      message.success('提示词优化完成')
                  }
                  delete generatingItems[itemId]

              } else if (msg.type === 'error') {
                  console.error('Gen Error:', msg.payload)
                  debugLogger.addLog('backend', `[Stream Error] ${msg.payload}`, 'error')
                  
                  // Clean error message for display
                  let errorText = msg.payload;
                  if (typeof errorText !== 'string') {
                      errorText = JSON.stringify(errorText);
                  }
                  
                  // Extract core error if it's a "Skill not found" or similar backend traceback
                  if (errorText.includes('Execution error:')) {
                      errorText = errorText.split('Execution error:')[1].trim();
                  }
                  
                  message.error('生成出错: ' + errorText)
                  delete generatingItems[itemId]
              }
           },
           onError: (err) => {
              debugLogger.addLog('backend', `[Stream Connect Error] ${err.message}`, 'error', err.stack)
              message.error('生成请求失败')
              delete generatingItems[itemId]
           }
      })
    } catch (e) {

      console.error(e)
      message.error('生成失败')
      delete generatingItems[itemId]
  }
}

const openPreview = (items: any[], index: number) => {
  previewList.value = items
  previewIndex.value = index
  previewVisible.value = true
}
</script>

<template>
  <aside 
    class="flex flex-col rounded-[2.5rem] neu-flat py-6 shrink-0 z-10 overflow-hidden bg-[#E0E5EC]"
    :style="{ width: width + 'px' }"
  >
    <!-- Header -->
    <div 
      class="flex items-center justify-between cursor-grab active:cursor-grabbing pb-2 shrink-0 select-none border-b border-gray-200/40" 
      @mousedown="emit('handle-down')"
    >
      <div class="px-6 flex items-center gap-2 overflow-hidden text-gray-500">
         <div class="w-2.5 h-2.5 rounded-full bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.6)]"></div>
         <h3 class="font-bold text-gray-600 text-s tracking-wider">剧本工作台</h3>
      </div>
    </div>

    <!-- Tabs (Neu Toggle) -->
    <div class="flex items-center justify-center gap-4 px-8 py-1 rounded-xl mb-4 shrink-0 bg-[#E0E5EC]">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        @click="activeTab = tab.id as any"
        class="flex-1 max-w-28 min-w-20 py-2 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition-all"
        :class="activeTab === tab.id 
          ? 'neu-pressed text-blue-500' 
          : 'neu-flat text-gray-500 hover:text-gray-600'"
      >
        <component :is="tab.icon" class="w-4 h-4" />
        {{ tab.label }}
      </button>
    </div>

    <!-- Content Area -->
    <div class="flex-1 overflow-y-auto custom-scroll py-4 px-8">
        <div v-if="!standardizedData" class="h-full flex flex-col items-center justify-center text-gray-400 gap-3 opacity-50">
           <Film class="w-10 h-10" />
           <span class="text-sm">等待 AI 生成...</span>
           <NeuButton size="sm" @click="handleAddItem('chars')">手动创建剧本</NeuButton>
        </div>

        <template v-else>
            <!-- Characters -->
            <ScriptCharacters 
              v-if="activeTab === 'chars'"
              :characters="standardizedData.characters"
              :generating-items="generatingItems"
              @delete="(idx, item) => handleDeleteItem('chars', idx, item)"
              @preview="(idx) => openPreview(standardizedData?.characters || [], idx)"
              @add="handleAddItem('chars')"
              @generate="handleGenerate"
            />

            <!-- Scenes -->
            <ScriptScenes 
              v-if="activeTab === 'scenes'"
              :scenes="standardizedData.scenes"
              :generating-items="generatingItems"
              @delete="(idx, item) => handleDeleteItem('scenes', idx, item)"
              @edit="(item) => handleEditItem('scenes', item)"
              @preview="(idx) => openPreview(standardizedData?.scenes || [], idx)"
              @add="handleAddItem('scenes')"
              @generate="handleGenerate"
            />

            <!-- Storyboard -->
            <ScriptStoryboard 
              v-if="activeTab === 'board'"
              :storyboard="standardizedData.storyboard"
              :generating-items="generatingItems"
              @delete="(idx, item) => handleDeleteItem('board', idx, item)"
              @edit="(item) => handleEditItem('board', item)"
              @preview="(idx) => openPreview(standardizedData?.storyboard || [], idx)"
              @open-video="openVideoPreview"
              @generate="handleGenerate"
              @request-save="emit('request-save')"
              @add="handleAddItem('board')"
            />
        </template>
    </div>

    <!-- Reusable Book Preview Component -->
    <BookPreview 
      :visible="previewVisible" 
      :items="previewList" 
      :initial-index="previewIndex"
      :generating-items="generatingItems"
      :all-characters="standardizedData?.characters || []"
      :all-scenes="standardizedData?.scenes || []"
      @close="previewVisible = false"
      @regenerate="(payload) => handleGenerate(payload.type || 'image', payload.item, payload.index, payload.extraPrompt, payload.updates, payload.generationMode)"
      @update-item="handlePreviewUpdate"
    />

    <CharacterCreateModal 
      :visible="showCharModal"
      @close="showCharModal = false"
      @confirm="handleCharConfirm"
    />

    <Teleport to="body">
      <VideoPreviewModal
        :visible="videoPreviewVisible"
        :video-url="currentVideoUrl"
        :poster-url="currentVideoPoster"
        @close="videoPreviewVisible = false"
      />
    </Teleport>
  </aside>
</template>

<style scoped>
.custom-scroll::-webkit-scrollbar { width: 4px; }
.custom-scroll::-webkit-scrollbar-thumb { background-color: #cbd5e0; border-radius: 4px; border: 1px solid #E0E5EC; }
</style>
