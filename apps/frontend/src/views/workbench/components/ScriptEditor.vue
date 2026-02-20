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
import { resolveImageUrl } from '@/utils/assets'
import { safeRandomUUID } from '@/utils/id'
import { sanitizeThinkPayload, stripThinkTags } from '@/utils/thinkFilter'
import BookPreview from './BookPreview.vue'
import CharacterCreateModal from './CharacterCreateModal.vue'
import VideoPreviewModal from './VideoPreviewModal.vue'
import { aiApi, episodeApi } from '@/api'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

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
const { t } = useI18n()

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

const tabs = computed(() => [
  { id: 'chars', icon: User, label: t('workbench.scriptEditor.tabs.characters') },
  { id: 'scenes', icon: ImageIcon, label: t('workbench.scriptEditor.tabs.scenes') },
  { id: 'board', icon: GripVertical, label: t('workbench.scriptEditor.tabs.storyboard') }
])

const standardizedData = computed(() => {
  if (!props.data) return null
  const root = props.data.generated_script || props.data
  return {
    title: root.meta?.project_title || t('workbench.scriptEditor.defaults.untitledProject'),
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
            meta: { project_title: t('workbench.scriptEditor.defaults.newProjectTitle') },
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

    const uuid = safeRandomUUID()

    if (type === 'scenes') {
        const timestamp = Math.floor(Date.now() / 1000)
        const suffix = safeRandomUUID().substring(0, 4)
        const index = root.scenes.length
        
        const newScene = {
            id: `scene_${timestamp}_${index}_${suffix}`,
            location_name: t('workbench.scriptEditor.defaults.newScene'),
            mood: t('workbench.scriptEditor.defaults.neutralMood'),
            visual_prompt: t('workbench.scriptEditor.defaults.newScenePrompt'),
            image_url: '',
            reference_image: ''
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
            action: t('workbench.scriptEditor.defaults.newShot'),
            shot_type: t('workbench.scriptEditor.defaults.wideShot'),
            visual_prompt: t('workbench.scriptEditor.defaults.newShotPrompt'),
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
    const suffix = safeRandomUUID().substring(0, 4)
    const index = root.characters.length

    const newChar = {
        id: `char_${timestamp}_${index}_${suffix}`,
        name: charData.name,
        role: charData.role,
        description: charData.description,
        image_url: '',
        reference_image: ''
    }
    root.characters.push(newChar)
    showCharModal.value = false
    emit('request-save')
}

const normalizeEntityId = (type: 'chars' | 'scenes', rawId: string) => {
    const idText = String(rawId || '').trim()
    const prefix = type === 'chars' ? 'char_' : 'scene_'
    return idText.startsWith(prefix) ? idText : `${prefix}${idText}`
}

const escapeRegExp = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

const hasEntityReference = (text: string, entityId: string) => {
    const raw = String(text || '')
    if (!raw || !entityId) return false
    const escaped = escapeRegExp(entityId)
    const mentionRe = new RegExp(`\\{\\{\\s*${escaped}\\s*\\}\\}`)
    const plainRe = new RegExp(`(^|[^A-Za-z0-9_])${escaped}([^A-Za-z0-9_]|$)`)
    return mentionRe.test(raw) || plainRe.test(raw)
}

const hasNamedMentionReference = (text: string, entityName: string) => {
    const raw = String(text || '')
    const name = String(entityName || '').trim()
    if (!raw || !name) return false
    const escaped = escapeRegExp(name)
    const mentionRe = new RegExp(`(^|[^A-Za-z0-9_])@${escaped}([^A-Za-z0-9_]|$)`)
    return mentionRe.test(raw)
}

const collectNovelUsagePaths = async (type: 'chars' | 'scenes', rawId: string) => {
    const targetId = normalizeEntityId(type, rawId)
    const out = new Set<string>()
    try {
        const rows: any = await episodeApi.list(Number(route.params.projectId))
        const list = Array.isArray(rows) ? rows : (Array.isArray(rows?.data) ? rows.data : [])
        const current = list.find((row: any) => Number(row?.id) === Number(route.params.episodeId))
        const novel = current?.ai_config?.novel
        if (!novel || typeof novel !== 'object') return []

        const configRows = Array.isArray(novel[type === 'chars' ? 'characters' : 'scenes'])
            ? novel[type === 'chars' ? 'characters' : 'scenes']
            : []
        const matchedRow = configRows.find((row: any) => normalizeEntityId(type, String(row?.id || '')) === targetId)
        const targetName = String(
            type === 'chars'
                ? matchedRow?.name
                : (matchedRow?.location_name || matchedRow?.name)
        ).trim()

        if (
            hasEntityReference(String(novel.draft_text || ''), targetId) ||
            hasNamedMentionReference(String(novel.draft_text || ''), targetName)
        ) {
            out.add('novel.draft_text')
        }

        if (configRows.some((row: any) => normalizeEntityId(type, String(row?.id || '')) === targetId)) {
            out.add(type === 'chars' ? 'novel.characters' : 'novel.scenes')
        }

        const selectedRows = Array.isArray(novel?.snowflake?.[type === 'chars' ? 'selected_character_ids' : 'selected_scene_ids'])
            ? novel.snowflake[type === 'chars' ? 'selected_character_ids' : 'selected_scene_ids']
            : []
        if (selectedRows.some((id: any) => normalizeEntityId(type, String(id || '')) === targetId)) {
            out.add(type === 'chars' ? 'novel.snowflake.selected_character_ids' : 'novel.snowflake.selected_scene_ids')
        }

        const walk = (node: any, path: string) => {
            if (out.size >= 12) return
            if (typeof node === 'string') {
                if (
                    hasEntityReference(node, targetId) ||
                    hasNamedMentionReference(node, targetName)
                ) out.add(path)
                return
            }
            if (Array.isArray(node)) {
                node.forEach((item, idx) => walk(item, `${path}[${idx}]`))
                return
            }
            if (node && typeof node === 'object') {
                Object.entries(node).forEach(([key, value]) => walk(value, `${path}.${key}`))
            }
        }

        walk(novel.snowflake?.plan, 'novel.snowflake.plan')
    } catch (error) {
        console.warn('[ScriptEditor] failed to collect novel usage paths', error)
    }
    return Array.from(out).slice(0, 12)
}

const handleDeleteItem = async (type: 'chars' | 'scenes' | 'board', index: number, _item: any) => {
    const confirmed = await showConfirm(t('workbench.scriptEditor.messages.confirmDelete'))
    if (!confirmed) return
    
    try {
        const root = props.data.generated_script || props.data
        const list = type === 'chars' ? root.characters : 
                     type === 'scenes' ? root.scenes : 
                     root.storyboard
                     
        if (list) {
            if ((type === 'chars' || type === 'scenes') && index >= 0 && index < list.length) {
                const target = list[index]
                const usagePaths = await collectNovelUsagePaths(type, String(target?.id || ''))
                if (usagePaths.length > 0) {
                    const usageLines = usagePaths.map((item) => `- ${item}`).join('\n')
                    const crossConfirmed = await showConfirm(t('workbench.scriptEditor.messages.crossWorkspaceDeleteConfirm', {
                        target: type === 'chars'
                            ? t('workbench.scriptEditor.tabs.characters')
                            : t('workbench.scriptEditor.tabs.scenes'),
                        usages: usageLines
                    }))
                    if (!crossConfirmed) return
                }
            }
            list.splice(index, 1)
            emit('request-save')
            message.success(t('workbench.scriptEditor.messages.deleted'))
        }
    } catch (e) {
        console.error(e)
        message.error(t('workbench.scriptEditor.messages.deleteFailed'))
    }
}


const handleUpdateItem = async (
    itemId: string,
    updates: any,
    options: { silent?: boolean } = {}
) => {
    // Optimistic local update
    try {
        const sanitizedUpdates = sanitizeThinkPayload(updates)
        const root = props.data.generated_script || props.data
        const findAndUpdate = (list: any[]) => {
            if (!list) return false
            const item = list.find((i: any) => i.id === itemId)
            if (item) {
                Object.assign(item, sanitizedUpdates)
                return true
            }
            return false
        }
        findAndUpdate(root.characters) || findAndUpdate(root.scenes) || findAndUpdate(root.storyboard)

        await aiApi.updateScriptItem({
            episode_id: Number(route.params.episodeId),
            item_id: itemId,
            updates: sanitizedUpdates
        })
        return true
    } catch (e) {
        console.error("Update failed", e)
        if (!options.silent) {
            message.error(t('workbench.scriptEditor.messages.updateFailed'))
        }
        return false
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
      const sanitizedUpdates = sanitizeThinkPayload(updates)
      await handleUpdateItem(item.id, sanitizedUpdates)
      // Update local item reference to reflect changes immediately in UI
      Object.assign(item, sanitizedUpdates)
  }

  const category = activeTab.value === 'chars' ? 'character' : (activeTab.value === 'scenes' ? 'scene' : 'storyboard')
  if (type === 'image' && item.reference_image && (category === 'character' || category === 'scene')) {
      const confirmed = await showConfirm(t('workbench.scriptEditor.messages.referenceConfirm'))
      if (!confirmed) return
  }

  generatingItems[itemId] = 0 // Start progress
  const typeLabel = type === 'image'
    ? t('workbench.scriptEditor.generateTypes.image')
    : (type === 'video' ? t('workbench.scriptEditor.generateTypes.video') : t('workbench.scriptEditor.generateTypes.prompt'))
  message.info(t('workbench.scriptEditor.messages.startGenerating', { type: typeLabel }))

  // Construct prompt
  let finalPrompt = stripThinkTags(item.visual_prompt || item.description || item.action || t('workbench.scriptEditor.defaults.noPrompt'))
  if (type === 'text') {
      // Prompt Refinement Logic
      const parts = []
      
      // 1. Original Context
      if (activeTab.value === 'chars') {
          parts.push(`[Character Info]\nName: ${stripThinkTags(String(item.name || ''))}\nDescription: ${stripThinkTags(String(item.description || ''))}`)
      } else if (activeTab.value === 'scenes') {
          parts.push(`[Scene Info]\nLocation: ${stripThinkTags(String(item.location_name || ''))}\nMood: ${stripThinkTags(String(item.mood || ''))}`)
      } else if (activeTab.value === 'board') {
          parts.push(`[Shot Info]\nAction: ${stripThinkTags(String(item.action || ''))}\nType: ${stripThinkTags(String(item.shot_type || ''))}`)
      }
      
      // 2. Current Visual Prompt (if exists)
      if (item.visual_prompt) {
          parts.push(`[Current Visual Prompt]\n${stripThinkTags(String(item.visual_prompt || ''))}`)
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
          finalPrompt = `${finalPrompt}. ${t('workbench.scriptEditor.prompts.requirementPrefix')} ${extraPrompt}`
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
          category,
          context_characters: contextCharacters,
          context_scenes: contextScenes
      }

      if (generationMode) {
          data.generation_mode = generationMode
      }

      if (data.category !== 'storyboard' && item.reference_image) {
          data.reference_image = item.reference_image
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
                      let finalGenerationPrompt = ''
                      if (typeof msg.payload === 'string') {
                          try {
                              const json = JSON.parse(msg.payload);
                              url = json.url;
                              if (type === 'video') {
                                finalGenerationPrompt = stripThinkTags(
                                  String(json.video_request_prompt || json.prompt || '')
                                )
                              } else {
                                finalGenerationPrompt = stripThinkTags(
                                  String(json.provider_prompt || json.final_prompt || '')
                                )
                              }
                          } catch (e) {
                              if (msg.payload.startsWith('http')) url = msg.payload;
                          }
                      } else if (msg.payload?.url) {
                          url = msg.payload.url;
                          if (type === 'video') {
                            finalGenerationPrompt = stripThinkTags(
                              String(msg.payload.video_request_prompt || msg.payload.prompt || '')
                            )
                          } else {
                            finalGenerationPrompt = stripThinkTags(
                              String(msg.payload.provider_prompt || msg.payload.final_prompt || '')
                            )
                          }
                      }

                      if (url) {
                          const normalizedUrl = resolveImageUrl(url)
                          const updates: Record<string, any> = {}
                          if (type === 'video') {
                              item.video_url = normalizedUrl
                              updates.video_url = normalizedUrl
                              if (finalGenerationPrompt) {
                                item.video_generation_prompt = finalGenerationPrompt
                                updates.video_generation_prompt = finalGenerationPrompt
                              }
                          } else {
                              item.image_url = normalizedUrl
                              updates.image_url = normalizedUrl
                              if (finalGenerationPrompt) {
                                item.generation_prompt = finalGenerationPrompt
                                updates.generation_prompt = finalGenerationPrompt
                              }
                          }
                          if (item.id && Object.keys(updates).length > 0) {
                            handleUpdateItem(item.id, updates)
                          }
                          
                          let mediaName = `${type}-${index}`
                          if (item.action) mediaName = item.action
                          else if (item.name) mediaName = item.name
                          else if (item.location_name) mediaName = item.location_name

                          emit('generate-media', {
                              type: type,
                              src: normalizedUrl,
                              name: mediaName,
                              duration: 5,
                              refData: item
                          })
                      }
                  } 
                  
                  if (msg.type === 'message' && type === 'text') {
                       item.visual_prompt = stripThinkTags(String(msg.payload ?? ''))
                  }
                  if (msg.type === 'finish' && type === 'text' && typeof msg.payload === 'string') {
                       item.visual_prompt = stripThinkTags(msg.payload)
                  }

                  message.success(t('workbench.scriptEditor.messages.generateSuccess'))
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
                  refinedPrompt = stripThinkTags(refinedPrompt)

                  if (refinedPrompt) {
                      item.visual_prompt = refinedPrompt
                      handleUpdateItem(item.id, { visual_prompt: refinedPrompt })
                      message.success(t('workbench.scriptEditor.messages.promptRefined'))
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
                  
                  message.error(t('workbench.scriptEditor.messages.generateError', { error: errorText }))
                  delete generatingItems[itemId]
              }
           },
           onError: (err) => {
              debugLogger.addLog('backend', `[Stream Connect Error] ${err.message}`, 'error', err.stack)
              message.error(t('workbench.scriptEditor.messages.requestFailed'))
              delete generatingItems[itemId]
           }
      })
    } catch (e) {

      console.error(e)
      message.error(t('workbench.scriptEditor.messages.generateFailed'))
      delete generatingItems[itemId]
  }
}

const handleUploadReference = async (item: any, file: File, category: 'character' | 'scene') => {
    if (!file) return
    try {
        const res: any = await aiApi.uploadReference(file, category)
        const url = res?.url
        if (!url) {
            throw new Error('Upload failed: no url returned')
        }
        item.reference_image = url
        let persisted = true
        if (item.id) {
            persisted = await handleUpdateItem(
                item.id,
                { reference_image: url },
                { silent: true }
            )
        }
        if (persisted) {
            message.success(t('workbench.scriptEditor.messages.referenceUploaded'))
        } else {
            message.warning(t('workbench.scriptEditor.messages.referenceUploadedButSaveFailed'))
        }
    } catch (e) {
        console.error(e)
        message.error(t('workbench.scriptEditor.messages.uploadFailed'))
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
         <h3 class="font-bold text-gray-600 text-s tracking-wider">{{ t('workbench.scriptEditor.title') }}</h3>
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
           <span class="text-sm">{{ t('workbench.scriptEditor.emptyWaiting') }}</span>
           <NeuButton size="sm" @click="handleAddItem('chars')">{{ t('workbench.scriptEditor.manualCreate') }}</NeuButton>
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
              @upload-reference="(item, _idx, file) => handleUploadReference(item, file, 'character')"
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
              @upload-reference="(item, _idx, file) => handleUploadReference(item, file, 'scene')"
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
