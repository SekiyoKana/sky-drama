<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft, Download, RotateCcw, Settings2, Loader2, TerminalSquare, Sparkles, Film, ChevronDown, Package, X, FileText, Languages, Copy, Image
} from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { save } from '@tauri-apps/plugin-dialog';
import { writeFile } from '@tauri-apps/plugin-fs';
import NeuButton from '@/components/base/NeuButton.vue'
import NeuConfirm from '@/components/base/NeuConfirm.vue'
import LanguageSwitcher from '@/components/base/LanguageSwitcher.vue'
import { projectApi, episodeApi, aiApi, styleApi } from '@/api'
import { useMessage } from '@/utils/useMessage'
import { useConfirm } from '@/utils/useConfirm'
import { startOnboardingTour } from '@/utils/tour'
import { debugLogger } from '@/utils/debugLogger'
import { sanitizeThinkPayload, stripThinkTags } from '@/utils/thinkFilter'
import { resolveImageUrl } from '@/utils/assets'

import PreviewModule from './components/PreviewModule.vue'
import AiDirectorModule from './components/AiDirectorModule.vue'
import ModelConfigCard from './components/ModelConfigCard.vue'
import ScriptEditor from './components/ScriptEditor.vue'
import ExecutionConsole from './components/ExecutionConsole.vue'
import VideoPreviewModal from './components/VideoPreviewModal.vue'
import TimelineModule from './components/TimelineModule.vue'

import directorImg from '@/assets/director.png'
import editorImg from '@/assets/editor.png'
import previewImg from '@/assets/preview.png'
import timelineImg from '@/assets/timeline.png'
import answerImg from '@/assets/answer.png'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const isTauri = !!window.__TAURI__;
const { show: showConfirm } = useConfirm()
const { t } = useI18n()

const projectId = Number(route.params.projectId)
const episodeId = Number(route.params.episodeId)

// --- Basic Data ---
const project = ref<any>(null)
const episode = ref<any>(null)
const loading = ref(true)
const showModelConfig = ref(false)

const isAiGenerating = ref(false)
const scriptData = ref<any>(null)
const scriptReadyHighlight = ref(false)
const abortController = ref<AbortController | null>(null)

// --- Console State ---
const streamLogs = ref<any[]>([])
const currentStatus = ref('')
const showConsole = ref(false)
const showAiDirector = ref(false) // Default visible
const activeTraceId = ref('')
const lastProgressLogged = ref(0)
const activeThoughtLogIndex = ref<number | null>(null)

// --- Layout State ---
type ModuleType = 'script' | 'preview'
const layoutOrder = ref<ModuleType[]>(['preview', 'script']) // Preview left, Script right
const moduleWidths = reactive({ script: window.innerWidth / 2 }) // Default to half screen width for 1:1 ratio
const draggableModuleIndex = ref<number | null>(null)
const isResizing = ref(false)
const resizeIndex = ref(-1)

// --- Video Library Window State (Draggable) ---
const showVideoLibrary = ref(false)
const videoLibrary = ref<any[]>([])
const libWindow = reactive({
  x: 24,
  y: window.innerHeight - 640, // Above the footer icon (Footer 224 + Height 400 + Gap)
  w: 300,
  h: 400
})

// Draggable Logic
let isLibDragging = false
let libDragOffset = { x: 0, y: 0 }

const startLibDrag = (e: MouseEvent) => {
  isLibDragging = true
  libDragOffset.x = e.clientX - libWindow.x
  libDragOffset.y = e.clientY - libWindow.y
  document.addEventListener('mousemove', onLibDrag)
  document.addEventListener('mouseup', stopLibDrag)
}
const onLibDrag = (e: MouseEvent) => {
  if (!isLibDragging) return
  libWindow.x = e.clientX - libDragOffset.x
  libWindow.y = e.clientY - libDragOffset.y
}
const stopLibDrag = () => {
  isLibDragging = false
  document.removeEventListener('mousemove', onLibDrag)
  document.removeEventListener('mouseup', stopLibDrag)
}

// Resizable Logic
let isLibResizing = false
const startLibResize = (e: MouseEvent) => {
  e.stopPropagation()
  isLibResizing = true
  document.addEventListener('mousemove', onLibResize)
  document.addEventListener('mouseup', stopLibResize)
}
const onLibResize = (e: MouseEvent) => {
  if (!isLibResizing) return
  libWindow.w = Math.max(200, e.clientX - libWindow.x)
  libWindow.h = Math.max(200, e.clientY - libWindow.y)
}
const stopLibResize = () => {
  isLibResizing = false
  document.removeEventListener('mousemove', onLibResize)
  document.removeEventListener('mouseup', stopLibResize)
}

// --- Timeline State ---
const timelineTracks = ref<any[]>([
  { id: 1, name: 'Main Track', type: 'video', items: [] },
  // { id: 2, name: 'Audio Track', type: 'audio', items: [] },
])

// --- Video Preview ---
const videoPreviewVisible = ref(false)
const currentVideoUrl = ref('')
const currentVideoPoster = ref('')

// --- Playback Control & State ---
const previewModuleRef = ref<any>(null)
const currentTimestamp = ref(0)
const totalDuration = ref(0)
const isPlaying = ref(false)
const volume = ref(1)
const isMuted = ref(false)

const handleTimeUpdate = (time: number) => {
  // time is the global current time emitted by PreviewModule
  currentTimestamp.value = time
}

const handleDurationUpdate = (duration: number) => {
  totalDuration.value = duration
}

const handlePlayStateChange = (playing: boolean) => {
  isPlaying.value = playing
}

const togglePlay = () => {
  // previewModuleRef is array because it's in a v-for loop
  if (Array.isArray(previewModuleRef.value) && previewModuleRef.value.length > 0) {
    previewModuleRef.value[0].togglePlay()
  } else if (previewModuleRef.value) {
    // fallback if somehow not array
    previewModuleRef.value.togglePlay()
  }
}

// Volume Logic (State stays in parent, controls moved to TimelineModule)
const playbackRate = ref(1.0)

const updatePlaybackRate = (rate: number) => {
  playbackRate.value = rate
  if (Array.isArray(previewModuleRef.value) && previewModuleRef.value.length > 0) {
    previewModuleRef.value[0].setPlaybackRate(rate)
  }
}

const updateVolume = (val: number) => {
  volume.value = val
  if (Array.isArray(previewModuleRef.value) && previewModuleRef.value.length > 0) {
    previewModuleRef.value[0].setVolume(val)
  }
}

const openVideoPreview = (item: any) => {
  if (!item.src) return
  currentVideoUrl.value = item.src
  // Poster strategy: try to use refData image if available, else null
  currentVideoPoster.value = item.refData?.image_url || ''
  videoPreviewVisible.value = true
}

// --- Init ---
const initData = async () => {
  try {
    const [pRes, eList] = await Promise.all([
      projectApi.get(projectId),
      episodeApi.list(projectId)
    ])
    project.value = pRes
    const currentEp = (eList as unknown as any[]).find(e => e.id === episodeId)

    if (!currentEp) throw new Error('Episode not found')
    episode.value = currentEp

      if (currentEp.ai_config) {
      if (currentEp.ai_config.generated_script) {
        scriptData.value = sanitizeThinkPayload(currentEp.ai_config.generated_script)
      }
      // Load Video Library
      if (currentEp.ai_config.video_library) {
        videoLibrary.value = currentEp.ai_config.video_library
      }
      // Load Timeline
      if (currentEp.ai_config.timeline_data) {
        timelineTracks.value = currentEp.ai_config.timeline_data
      }
    }
  } catch (e) {
    message.error(t('workbench.messages.loadFailed'))
    goBack()
  } finally {
    loading.value = false
  }
}

const goBack = () => { router.push({ path: '/projects', query: { id: projectId } }) }

// --- Unified Persistence Logic ---
const persistState = async (silent = true) => {
  if (!episode.value) return
  try {
    const newConfig = {
      ...(episode.value.ai_config || {}),
      generated_script: sanitizeThinkPayload(scriptData.value),
      video_library: videoLibrary.value,
      timeline_data: timelineTracks.value
    }

    episode.value.ai_config = newConfig

    await episodeApi.update(projectId, episodeId, {
      title: episode.value.title,
      ai_config: newConfig
    } as any)

    if (!silent) message.success(t('workbench.messages.saveSuccess'))
  } catch (e) {
    console.error('Auto-save failed', e)
    if (!silent) message.error(t('workbench.messages.saveFailed'))
  }
}

const saveModelConfig = async (newConfig: any) => {
  // This is for the manual settings modal, we merge it
  if (!episode.value) return; // Guard clause

  try {
    const mergedConfig = { ...(episode.value.ai_config || {}), ...newConfig }
    await episodeApi.update(projectId, episodeId, {
      title: episode.value.title,
      ai_config: mergedConfig
    } as any)
    episode.value.ai_config = mergedConfig
    message.success(t('workbench.messages.configSaved'))
  } catch (e) { message.error(t('workbench.messages.saveFailed')) }
}

// --- Prompt Auto-Fill Logic ---
const fillPrompts = async (script: any) => {
  // Collect items needing prompts
  const tasks: { category: string, item: any, index: number }[] = []

  script.characters?.forEach((item: any, i: number) => {
    if (!item.visual_prompt && !item.reference_image) tasks.push({ category: 'character', item, index: i })
  })
  script.scenes?.forEach((item: any, i: number) => {
    if (!item.visual_prompt && !item.reference_image) tasks.push({ category: 'scene', item, index: i })
  })
  script.storyboard?.forEach((item: any, i: number) => {
    if (!item.visual_prompt) tasks.push({ category: 'storyboard', item, index: i })
  })

  if (tasks.length === 0) return

  currentStatus.value = t('workbench.status.refiningPrompts', { count: tasks.length })

  // Push start of prompt refinement log
  const refinementLog = reactive({
    type: 'thought',
    content: `\n<|PROMPT_REFINEMENT|>\n${t('workbench.logs.generatingVisualPrompts', { count: tasks.length })}\n`
  })
  streamLogs.value.push(refinementLog)

  // Execute sequentially to avoid rate limits (or parallel if API allows)
  // Using simple loop for stability
  for (const [idx, task] of tasks.entries()) {
    // Check for manual abort before each step
    if (abortController.value?.signal.aborted) {
      break;
    }

    try {
      let rawText = ''
      if (task.category === 'character') rawText = `[Name]: ${stripThinkTags(String(task.item.name || ''))}, [Desc]: ${stripThinkTags(String(task.item.description || ''))}`
      else if (task.category === 'scene') rawText = `[Location]: ${stripThinkTags(String(task.item.location_name || ''))}, [Mood]: ${stripThinkTags(String(task.item.mood || ''))}`
      else if (task.category === 'storyboard') rawText = `[Action]: ${stripThinkTags(String(task.item.action || ''))}, [Shot]: ${stripThinkTags(String(task.item.shot_type || ''))}`

      // Push progress update to the SAME log entry
      refinementLog.content += t('workbench.logs.refiningItem', {
        current: idx + 1,
        total: tasks.length,
        category: task.category,
        preview: rawText.substring(0, 20)
      }) + '\n'

      await new Promise<void>((resolve, reject) => {
        const signal = abortController.value?.signal
        if (signal?.aborted) {
          reject(new Error('User Terminated'))
          return
        }

        aiApi.skillsStream({
          projectId,
          episodeId,
          prompt: rawText,
          type: 'text',
          skill: 'short-video-prompt-engineer',
          data: { category: task.category }
        }, {
          onMessage: (msg) => {
            if (signal?.aborted) return

            if (msg.type === 'thought' || msg.type === 'token') {
              if (!task.item._tempPrompt) task.item._tempPrompt = ''
              task.item._tempPrompt += msg.payload
            }
            if (msg.type === 'finish' || msg.type === 'text_finish' || msg.type === 'message') {
              if (task.item._tempPrompt) {
                // 如果有累积的流式内容，优先使用
                if (msg.payload && typeof msg.payload === 'string') {
                  // 如果 finish 包里还有残留文本，追加上去
                  task.item._tempPrompt += msg.payload
                }
                task.item.visual_prompt = stripThinkTags(task.item._tempPrompt)
                delete task.item._tempPrompt
              } else if (msg.payload && typeof msg.payload === 'string') {
                // 如果没有流式内容，说明是一次性返回的
                task.item.visual_prompt = stripThinkTags(msg.payload)
              }

              // Save progress incrementally
              if (idx % 3 === 0) persistState(true)
            }
          },
          onFinish: () => resolve(),
          onError: (_err) => {
            if (signal?.aborted) reject(new Error('User Terminated'))
            else resolve() // Continue on individual error
          }
        }, signal) // Pass signal here too if supported, or manual check
      }).catch(e => {
        if (e.message === 'User Terminated') throw e
        console.error('Prompt fill failed for', task, e)
      })
    } catch (e: any) {
      if (e.message === 'User Terminated') {
        message.info(t('workbench.messages.promptGenerationStopped'))
        break
      }
    }
  }

  // Push end of prompt refinement log to the SAME log entry
  refinementLog.content += '<|PROMPT_REFINEMENT_END|>\n'

  if (!abortController.value?.signal.aborted) {
    currentStatus.value = t('workbench.status.refinementComplete')
    // Push finish log manually after everything is done
    streamLogs.value.push({ type: 'finish' })
    message.success(t('workbench.messages.creationDone'))
    await persistState(true)
  }
}

// --- Streaming Logic ---
const handleGenerateStream = async (data: { prompt: string, tags: any }) => {
  if (!data.prompt) return message.warning(t('workbench.messages.enterPrompt'))
  const cleanPrompt = stripThinkTags(data.prompt)
  if (!cleanPrompt) return message.warning(t('workbench.messages.enterPrompt'))

  // Confirm overwrite if data exists
  const hasContent = scriptData.value && (
    (scriptData.value.characters && scriptData.value.characters.length > 0) ||
    (scriptData.value.scenes && scriptData.value.scenes.length > 0) ||
    (scriptData.value.storyboard && scriptData.value.storyboard.length > 0)
  )

  if (hasContent && data.tags?.mode !== 'split') {
    const confirmed = await showConfirm(
      t('workbench.messages.overwriteConfirmText'),
      t('workbench.messages.overwriteConfirmTitle')
    )
    if (!confirmed) return
  }

  isAiGenerating.value = true; streamLogs.value = []; currentStatus.value = t('workbench.status.thinking'); scriptReadyHighlight.value = false;
  activeTraceId.value = ''
  lastProgressLogged.value = 0
  activeThoughtLogIndex.value = null
  // showConsole.value = true;

  // Create new AbortController
  abortController.value = new AbortController()

  try {
    let skill: string | undefined = undefined
    let type: string | undefined = undefined

    if (data.tags?.mode === 'split') {
      skill = 'short-video-storyboard-maker'
      type = 'text'
    }

    const traceId = `wb_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
    debugLogger.addLog('frontend', `[DirectorTrace] Starting run ${traceId}`, 'info', undefined, {
      projectId,
      episodeId,
      mode: data.tags?.mode || 'script',
      promptPreview: cleanPrompt.slice(0, 160)
    })

    await aiApi.skillsStream({
      projectId: projectId, episodeId: episodeId,
      prompt: cleanPrompt,
      skill: skill,
      type: type,
      data: { trace_id: traceId }
    }, {
      onMessage: (msg) => { handleStreamMessage(msg) },
      onError: (err) => {
        let errorMsg = err.message
        const isInterrupted = err.message === 'User Terminated'
        if (err.message === 'User Terminated') {
          errorMsg = t('workbench.messages.userTerminatedRequest')
        }
        debugLogger.addLog('frontend', `[DirectorTrace] Run failed ${activeTraceId.value || traceId}`, 'error', undefined, {
          error: errorMsg
        })
        streamLogs.value.push({
          type: 'status',
          content: isInterrupted ? '[INTERRUPTED] Request terminated by user' : '[ERROR] Request failed'
        })
        message.error(t('workbench.messages.generateError', { error: errorMsg }));
        streamLogs.value.push({ type: 'error', content: errorMsg });
        isAiGenerating.value = false;
        abortController.value = null
        activeThoughtLogIndex.value = null
      },
      onFinish: async () => {
        debugLogger.addLog('frontend', `[DirectorTrace] Run finished ${activeTraceId.value || traceId}`, 'info')
        // Check for empty prompts and fill them
        if (scriptData.value && !abortController.value?.signal.aborted) {
          await fillPrompts(scriptData.value)
        }
        isAiGenerating.value = false;
        currentStatus.value = '';
        abortController.value = null
        activeThoughtLogIndex.value = null
        await refreshEpisodeData();
      }
    }, abortController.value.signal); // Pass signal
  } catch (e: any) {
    // Logic handled in onError mostly
    if (!abortController.value?.signal.aborted) {
      message.error(t('workbench.messages.generateInterrupted', { error: e.message })); streamLogs.value.push({ type: 'error', content: e.message }); isAiGenerating.value = false;
    }
    abortController.value = null
  }
}

const handleStopGenerate = () => {
  if (abortController.value) {
    abortController.value.abort()
    debugLogger.addLog('frontend', `[DirectorTrace] Run aborted ${activeTraceId.value || '-'}`, 'warn')
    isAiGenerating.value = false
    currentStatus.value = t('workbench.status.terminatedByUser')
    streamLogs.value.push({ type: 'status', content: '[INTERRUPTED] Generation aborted' })
    streamLogs.value.push({ type: 'error', content: t('workbench.messages.userTerminatedOperation') })
    message.info(t('workbench.messages.operationCancelled'))
    // onError will be called with AbortError -> 'User Terminated'
    activeThoughtLogIndex.value = null
  }
}

const refreshEpisodeData = async () => {
  // Re-fetch to sync state from backend (since backend already auto-saved)
  await initData()
}

const handleStreamMessage = (msg: any) => {
  switch (msg.type) {
    case 'trace':
      activeTraceId.value = msg.payload?.run_id || activeTraceId.value
      if (activeTraceId.value) {
        streamLogs.value.push({ type: 'status', content: `[Trace] ${activeTraceId.value}` })
        debugLogger.addLog('frontend', `[DirectorTrace] Active run ${activeTraceId.value}`, 'info', undefined, msg.payload)
      }
      break;
    case 'status': currentStatus.value = msg.payload; break;
    case 'progress':
      {
        const progress = Number(msg.payload || 0)
        if (!Number.isNaN(progress) && (progress === 1 || progress === 100 || progress - lastProgressLogged.value >= 10)) {
          lastProgressLogged.value = progress
          streamLogs.value.push({ type: 'status', content: `Progress: ${progress}%` })
        }
      }
      break;
    case 'backend_log':
      streamLogs.value.push({ type: 'backend_log', content: msg.payload })
      break;
    case 'thought':
      if (activeThoughtLogIndex.value === null || streamLogs.value[activeThoughtLogIndex.value]?.type !== 'thought') {
        streamLogs.value.push({ type: 'thought', content: '' })
        activeThoughtLogIndex.value = streamLogs.value.length - 1
      }
      streamLogs.value[activeThoughtLogIndex.value].content += msg.payload
      break;
    case 'tool_start': streamLogs.value.push({ type: 'tool', name: msg.payload.name, input: msg.payload.input, status: 'running', output: null }); break;
    case 'tool_end':
      for (let i = streamLogs.value.length - 1; i >= 0; i--) {
        const log = streamLogs.value[i]
        if (log.type === 'tool' && log.name === msg.payload.name && log.status === 'running') { log.status = 'done'; log.output = msg.payload.output; log.duration = msg.payload.duration; break; }
      }
      break;
    case 'finish':
      try {
        const scriptJson = JSON.parse(msg.payload.json)
        scriptData.value = sanitizeThinkPayload(scriptJson)
        scriptReadyHighlight.value = true
        // Backend already saved, no need to persistState again
      } catch (e) {
        // Suppress
      }
      activeThoughtLogIndex.value = null
      break;
    case 'error':
      streamLogs.value.push({ type: 'status', content: '[ERROR] Server stream error' })
      streamLogs.value.push({ type: 'error', content: msg.payload })
      activeThoughtLogIndex.value = null
      break;
    case 'text_finish':
      if (msg.payload?.text) {
        streamLogs.value.push({ type: 'thought', content: msg.payload.text })
      }
      activeThoughtLogIndex.value = null
      break;
    case 'message':
      if (activeThoughtLogIndex.value === null || streamLogs.value[activeThoughtLogIndex.value]?.type !== 'thought') {
        streamLogs.value.push({ type: 'thought', content: '' })
        activeThoughtLogIndex.value = streamLogs.value.length - 1
      }
      streamLogs.value[activeThoughtLogIndex.value].content += String(msg.payload ?? '')
      break;
  }
}

// --- Layout & Resizing ---
const onHandleMouseDown = (index: number) => { draggableModuleIndex.value = index }
const handleModuleDragStart = (e: DragEvent, index: number) => {
  if (draggableModuleIndex.value !== index) { e.preventDefault(); return }
  if (e.dataTransfer) { e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('index', index.toString()) }
}
const handleModuleDrop = (e: DragEvent, targetIndex: number) => {
  draggableModuleIndex.value = null
  const sourceIndex = parseInt(e.dataTransfer?.getData('index') || '-1')
  if (sourceIndex !== -1 && sourceIndex !== targetIndex) {
    const temp = layoutOrder.value[sourceIndex]; layoutOrder.value[sourceIndex] = layoutOrder.value[targetIndex] as ModuleType; layoutOrder.value[targetIndex] = temp as ModuleType;
  }
}
const startResize = (index: number) => { isResizing.value = true; resizeIndex.value = index; document.body.style.cursor = 'col-resize'; document.addEventListener('mousemove', handleResizeMove); document.addEventListener('mouseup', stopResize); }
const handleResizeMove = (e: MouseEvent) => {
  if (!isResizing.value) return
  const sensitivity = 1.0;
  const leftModule = layoutOrder.value[resizeIndex.value];
  const rightModule = layoutOrder.value[resizeIndex.value + 1];

  const totalW = window.innerWidth
  const minW = totalW * 0.2
  const maxW = totalW * 0.8

  // We only have 'script' in moduleWidths now. 'preview' is flex.
  if (leftModule !== 'preview') {
    // Left is script. Drag right -> width increases.
    const key = leftModule as 'script';
    const newW = moduleWidths[key] + e.movementX * sensitivity;
    moduleWidths[key] = Math.max(minW, Math.min(maxW, newW));
  }
  else if (rightModule !== 'preview') {
    // Right is script. Drag right -> width decreases (resizer moves right).
    const key = rightModule as 'script';
    const newW = moduleWidths[key] - e.movementX * sensitivity;
    moduleWidths[key] = Math.max(minW, Math.min(maxW, newW));
  }
}
const stopResize = () => { isResizing.value = false; document.body.style.cursor = ''; document.removeEventListener('mousemove', handleResizeMove); document.removeEventListener('mouseup', stopResize); }
const resetLayout = () => {
  moduleWidths.script = window.innerWidth / 2;
  layoutOrder.value = ['preview', 'script'];
  libWindow.x = 24;
  libWindow.y = window.innerHeight - 640;
}

// --- Video Generation & Library ---
const handleGenerateMedia = async (mediaItem: any) => {
  // Only allow video content from storyboard generation
  if (mediaItem.type !== 'video') return

  videoLibrary.value.unshift({ id: Date.now(), ...mediaItem })
  // Save state
  await persistState(true)
}

const handleUpdateTimelineItem = async (payload: any) => {
  const { trackId, itemId, updates } = payload
  const track = timelineTracks.value.find(t => t.id === trackId) || timelineTracks.value.find(t => t.type === 'video')
  if (track) {
    const item = track.items.find((i: any) => i.id === itemId)
    if (item) {
      Object.assign(item, updates)
      // No need to persistState immediately for duration updates to avoid spam
    }
  }
}

// --- Export Logic ---
const showExportMenu = ref(false)
const exportMenuRef = ref<HTMLElement | null>(null)
const showLanguageMenu = ref(false)
const languageMenuRef = ref<HTMLElement | null>(null)
const showStoryboardExportPreview = ref(false)
const storyboardPromptRecords = ref<
  Record<string, { videoPrompt: string; styleImageUrl: string; imageUrl: string; videoUrl: string }>
>({})
const storyboardStyleFallbackImage = ref('')
const storyboardPromptLoading = ref(false)
const isExporting = ref(false)
const exportProgress = ref(0)
const exportStatusText = ref('')

const normalizeAssetPath = (path: string | null | undefined): string => {
  if (!path) return ''
  const text = String(path).trim()
  if (!text) return ''
  if (text.startsWith('http://') || text.startsWith('https://')) {
    try {
      return new URL(text).pathname || ''
    } catch (_error) {
      return text
    }
  }
  return text
}

const resolveStoryboardImageUrl = (path: string | null | undefined): string => {
  if (!path) return ''
  if (
    path.startsWith('http://') ||
    path.startsWith('https://') ||
    path.startsWith('data:') ||
    path.startsWith('blob:')
  ) {
    return path
  }
  return resolveImageUrl(path)
}

const storyboardExportItems = computed(() => {
  const list = scriptData.value?.storyboard
  if (!Array.isArray(list)) return []
  return list.map((item: any, index: number) => {
    const assetPath = normalizeAssetPath(item?.image_url)
    const itemId = String(item?.id || `storyboard_${index}`)
    const record = storyboardPromptRecords.value[itemId]
    const prompt = stripThinkTags(
      String(record?.videoPrompt || item?.video_generation_prompt || '')
    )
    const styleRefImageUrl = resolveStoryboardImageUrl(record?.styleImageUrl || '')
    const finalStyleRefImageUrl = styleRefImageUrl || storyboardStyleFallbackImage.value
    const videoUrl = resolveStoryboardImageUrl(record?.videoUrl || item?.video_url)
    return {
      assetPath,
      itemId,
      index,
      shotId: String(item?.shot_id ?? index + 1),
      shotType: stripThinkTags(String(item?.shot_type ?? '')),
      action: stripThinkTags(String(item?.action ?? '')),
      prompt,
      styleRefImageUrl: finalStyleRefImageUrl,
      showStyleRefImage: Boolean(finalStyleRefImageUrl),
      imageUrl: resolveStoryboardImageUrl(record?.imageUrl || item?.image_url),
      videoUrl,
    }
  })
})

const handleClickOutside = (event: MouseEvent) => {
  if (showExportMenu.value && exportMenuRef.value && !exportMenuRef.value.contains(event.target as Node)) {
    showExportMenu.value = false
  }
  if (showLanguageMenu.value && languageMenuRef.value && !languageMenuRef.value.contains(event.target as Node)) {
    showLanguageMenu.value = false
  }
}

const copyTextWithFallback = async (text: string) => {
  if (!text) return false
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch (_error) {
    // fallback below
  }

  try {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.left = '-9999px'
    document.body.appendChild(textarea)
    textarea.focus()
    textarea.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(textarea)
    return ok
  } catch (_error) {
    return false
  }
}

const copyStoryboardPrompt = async (item: { prompt: string }) => {
  const content = item.prompt || t('workbench.export.emptyPrompt')
  const ok = await copyTextWithFallback(content)
  if (ok) message.success(t('workbench.export.copyPromptSuccess'))
  else message.error(t('workbench.export.copyFailed'))
}

const copyAllStoryboardPrompts = async () => {
  if (!storyboardExportItems.value.length) {
    message.warning(t('workbench.export.noStoryboardData'))
    return
  }
  const payload = storyboardExportItems.value
    .map((item) => {
      const videoLine = `${t('workbench.export.videoLinkLabel')}: ${item.videoUrl || t('workbench.export.noVideoYet')}`
      return `#${item.shotId}\n${item.prompt || t('workbench.export.emptyPrompt')}\n${videoLine}`
    })
    .join('\n\n---\n\n')
  const ok = await copyTextWithFallback(payload)
  if (ok) message.success(t('workbench.export.copyAllPromptsSuccess'))
  else message.error(t('workbench.export.copyFailed'))
}

const copyStoryboardImage = async (item: { imageUrl: string }) => {
  if (!item.imageUrl) {
    message.warning(t('workbench.export.noImageToCopy'))
    return
  }

  const ClipboardItemCtor = (window as any).ClipboardItem
  if (ClipboardItemCtor && navigator.clipboard?.write) {
    try {
      const resp = await fetch(item.imageUrl)
      const blob = await resp.blob()
      const mimeType = blob.type || 'image/png'
      await navigator.clipboard.write([new ClipboardItemCtor({ [mimeType]: blob })])
      message.success(t('workbench.export.copyImageSuccess'))
      return
    } catch (_error) {
      // fallback to URL copy
    }
  }

  const copiedUrl = await copyTextWithFallback(item.imageUrl)
  if (copiedUrl) message.info(t('workbench.export.copyImageUrlFallback'))
  else message.error(t('workbench.export.copyFailed'))
}

const loadStoryboardPrompts = async () => {
  if (!episode.value) return
  storyboardPromptLoading.value = true
  try {
    const res: any = await aiApi.getStoryboardPrompts(episodeId)
    const rawRecords = (res?.records || {}) as Record<string, any>
    const normalizedRecords: Record<
      string,
      { videoPrompt: string; styleImageUrl: string; imageUrl: string; videoUrl: string }
    > = {}
    Object.entries(rawRecords).forEach(([itemId, record]) => {
      const key = String(itemId || '').trim()
      if (!key) return
      normalizedRecords[key] = {
        videoPrompt: stripThinkTags(String(record?.video_prompt || '')),
        styleImageUrl: String(record?.style_image_url || ''),
        imageUrl: String(record?.image_url || ''),
        videoUrl: String(record?.video_url || ''),
      }
    })
    storyboardPromptRecords.value = normalizedRecords
    storyboardStyleFallbackImage.value = ''

    const styleId = Number(episode.value?.ai_config?.style?.id || 0)
    if (styleId > 0) {
      const styles = await styleApi.list()
      const matched = Array.isArray(styles)
        ? styles.find((s: any) => Number(s?.id) === styleId)
        : null
      if (matched?.image_url) {
        storyboardStyleFallbackImage.value = resolveStoryboardImageUrl(matched.image_url)
      }
    }
  } catch (error) {
    console.warn('[storyboard prompts] failed to load prompt records', error)
    storyboardPromptRecords.value = {}
    storyboardStyleFallbackImage.value = ''
  } finally {
    storyboardPromptLoading.value = false
  }
}

const openStoryboardExportPreview = () => {
  showExportMenu.value = false
  if (!episode.value) return
  if (!storyboardExportItems.value.length) {
    message.warning(t('workbench.export.noStoryboardData'))
    return
  }
  showStoryboardExportPreview.value = true
  loadStoryboardPrompts()
}

const handleExportAssets = async () => {
  showExportMenu.value = false
  if (!episode.value) return
  message.info(t('workbench.messages.packagingAssets'))
  try {
    const blob = await episodeApi.exportAssets(projectId, episodeId)
    if (!blob) throw new Error("Empty response")

    const filename = `${episode.value.title}_${t('workbench.export.assetsFileSuffix')}.zip`

    try {
      if (window.showSaveFilePicker) {
        const handle = await window.showSaveFilePicker({
          suggestedName: filename,
          types: [{
            description: 'ZIP Archive',
            accept: { 'application/zip': ['.zip'] },
          }],
        });
        const writable = await handle.createWritable();
        await writable.write(blob);
        await writable.close();
        message.success(t('workbench.messages.saved'));
        return;
      }
    } catch (err: any) {
      if (err.name === 'AbortError') return;
      console.warn('File System Access API failed, falling back to download:', err);
    }

    if (isTauri) {
      const arrayBuffer = await blob.data();
      const uint8Array = new Uint8Array(arrayBuffer);
      const savePath = await save({
          defaultPath: filename,
          filters: [{
              name: 'Zip Archive',
              extensions: ['zip']
          }, {
              name: 'All Files',
              extensions: ['*']
          }]
      });
      if (!savePath) {
          console.log('[export] save cancelled by user');
          return;
      }
      await writeFile(savePath, uint8Array);
      console.log(`[export] file saved to: ${savePath}`);
    } else {
      const url = window.URL.createObjectURL(new Blob([blob as any]))
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url) 
    }
    message.success(t('workbench.messages.downloadStarted'))
  } catch (e) {
    console.error(e)
    message.error(t('workbench.messages.exportAssetsFailed'))
  }
}

const doExportStoryboard = async () => {
  if (!episode.value) return
  message.info(t('workbench.messages.exportingStoryboard'))

  try {
    const blob = await episodeApi.exportStoryboardData(projectId, episodeId)
    if (!blob) throw new Error("Empty response")

    const filename = `${episode.value.title}_${t('workbench.export.storyboardFileSuffix')}.zip`

    try {
      if (window.showSaveFilePicker) {
        const handle = await window.showSaveFilePicker({
          suggestedName: filename,
          types: [{
            description: 'ZIP Archive',
            accept: { 'application/zip': ['.zip'] },
          }],
        });
        const writable = await handle.createWritable();
        await writable.write(blob);
        await writable.close();
        message.success(t('workbench.messages.saved'));
        return;
      }
    } catch (err: any) {
      if (err.name === 'AbortError') return;
      console.warn('File System Access API failed, falling back to download:', err);
    }

    if (isTauri) {
      const arrayBuffer = await blob.data();
      const uint8Array = new Uint8Array(arrayBuffer);
      const savePath = await save({
          defaultPath: filename,
          filters: [{
              name: 'Zip Archive',
              extensions: ['zip']
          }, {
              name: 'All Files',
              extensions: ['*']
          }]
      });
      if (!savePath) {
          console.log('[export] save cancelled by user');
          return;
      }
      await writeFile(savePath, uint8Array);
      console.log(`[export] file saved to: ${savePath}`);
    } else {
      const url = window.URL.createObjectURL(new Blob([blob as any]))
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url) 
    }
    message.success(t('workbench.messages.downloadStarted'))
  } catch (e) {
    console.error(e)
    message.error(t('workbench.messages.exportStoryboardFailed'))
  }
}

const handleConfirmExportStoryboard = async () => {
  showStoryboardExportPreview.value = false
  await doExportStoryboard()
}

const handleExportVideo = async () => {
  showExportMenu.value = false
  if (!episode.value) return

  await persistState(true)

  isExporting.value = true
  exportProgress.value = 0
  exportStatusText.value = t('workbench.status.renderingVideo')

  // Fake progress for server processing time
  const progressTimer = setInterval(() => {
    if (exportProgress.value < 90) {
      const increment = exportProgress.value > 60 ? 1 : 5
      exportProgress.value += increment
    }
  }, 1000)

  try {
    const blob = await episodeApi.exportVideo(projectId, episodeId, (p) => {
      clearInterval(progressTimer)
      exportStatusText.value = t('workbench.status.downloadingVideo')
      exportProgress.value = p
    })
    if (!blob) throw new Error("Empty response")

    const filename = `${episode.value.title}.mp4`

    // Try File System Access API first
    try {
      // @ts-ignore
      if (window.showSaveFilePicker) {
        // @ts-ignore
        const handle = await window.showSaveFilePicker({
          suggestedName: filename,
          types: [{
            description: 'MP4 Video',
            accept: { 'video/mp4': ['.mp4'] },
          }],
        });
        const writable = await handle.createWritable();
        await writable.write(blob);
        await writable.close();
        message.success(t('workbench.messages.saved'));
        return;
      }
    } catch (err: any) {
      if (err.name === 'AbortError') return;
      console.warn('File System Access API failed, falling back to download:', err);
    }

    const url = window.URL.createObjectURL(new Blob([blob as any]))
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    message.success(t('workbench.messages.downloadStarted'))
  } catch (e: any) {
    console.error(e)
    let errorMsg = t('workbench.messages.exportVideoFailed')

    // Handle Blob error response
    if (e.response?.data instanceof Blob) {
      try {
        const text = await e.response.data.text()
        const json = JSON.parse(text)
        if (json.detail) errorMsg += `: ${json.detail}`
      } catch (err) {
        // If parsing fails, stick to default or status text
        errorMsg += ` (${e.response.status} ${e.response.statusText})`
      }
    } else if (e.message) {
      errorMsg += `: ${e.message}`
    }

    message.error(errorMsg)
  } finally {
    clearInterval(progressTimer)
    setTimeout(() => { isExporting.value = false }, 1000)
  }
}

onMounted(() => {
  initData()
  document.addEventListener('click', handleClickOutside)

  startOnboardingTour('workbench_view', [
    {
      element: '#tour-ai-director',
      theme: 'purple',
      image: directorImg,
      popover: { title: t('workbench.tour.aiDirectorTitle'), description: t('workbench.tour.aiDirectorDesc'), side: 'bottom' }
    },
    {
      element: '#tour-model-config',
      theme: 'blue',
      image: answerImg,
      popover: { title: t('workbench.tour.modelConfigTitle'), description: t('workbench.tour.modelConfigDesc'), side: 'bottom' }
    },
    {
      element: '#tour-script-editor',
      theme: 'yellow',
      image: editorImg,
      popover: { title: t('workbench.tour.scriptEditorTitle'), description: t('workbench.tour.scriptEditorDesc'), side: 'right' }
    },
    {
      element: '#tour-preview-module',
      theme: 'green',
      image: previewImg,
      popover: { title: t('workbench.tour.previewTitle'), description: t('workbench.tour.previewDesc'), side: 'left' }
    },
    {
      element: '#tour-timeline',
      theme: 'pink',
      image: timelineImg,
      popover: { title: t('workbench.tour.timelineTitle'), description: t('workbench.tour.timelineDesc'), side: 'top' }
    }
  ])
})
onUnmounted(() => {
  document.removeEventListener('mousemove', onLibDrag)
  document.removeEventListener('mouseup', stopLibDrag)
  document.removeEventListener('mousemove', onLibResize)
  document.removeEventListener('mouseup', stopLibResize)
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="flex flex-col h-screen bg-[#E0E5EC] p-4 gap-4 overflow-hidden select-none text-[#4A5568]">

    <!-- Header -->
    <header
      class="flex items-center justify-between px-4 py-3 rounded-[1.5rem] neu-flat shrink-0 z-30 relative bg-[#E0E5EC]">
      <div class="flex items-center gap-4">
        <button @click="goBack"
          class="p-2.5 rounded-full neu-flat hover:text-blue-500 active:neu-pressed transition-all text-gray-500">
          <ArrowLeft class="w-5 h-5" />
        </button>
        <div class="flex flex-col" v-if="episode">
          <h1 class="text-base font-bold tracking-tight text-gray-700">{{ episode.title }}</h1>
          <span v-if="scriptData?.meta?.core_premise" class="text-xs text-gray-500 line-clamp-1 max-w-[300px]"
            :title="scriptData.meta.core_premise">
            {{ scriptData.meta.core_premise }}
          </span>
          <span v-else class="text-xs text-gray-500">{{ project?.name }}</span>
        </div>
      </div>

      <div class="flex gap-4 items-center">

        <div class="relative group/ai" id="tour-ai-director">
          <button @click="showAiDirector = !showAiDirector"
            class="flex items-center gap-2 px-3 py-2.5 rounded-xl transition-all font-bold text-xs uppercase tracking-wider"
            :class="showAiDirector ? 'neu-pressed text-purple-600' : 'neu-flat hover:text-purple-500 text-gray-500'">
            <Sparkles class="w-4 h-4" />
          </button>
        </div>

        <div class="relative" id="tour-model-config">
          <button @click.stop="showModelConfig = !showModelConfig"
            class="flex items-center gap-2 px-3 py-2.5 rounded-xl transition-all font-bold text-xs uppercase tracking-wider"
            :class="showModelConfig ? 'neu-pressed text-blue-500' : 'neu-flat hover:text-blue-500 text-gray-500'">
            <Settings2 class="w-4 h-4" />
          </button>
          <ModelConfigCard :visible="showModelConfig" :initial-config="episode?.ai_config"
            @close="showModelConfig = false" @save="saveModelConfig" />
        </div>

        <!-- Console Trigger with Tooltip -->
        <div class="relative group/console">
          <button @click="showConsole = !showConsole"
            class="flex items-center gap-2 px-3 py-2.5 rounded-xl transition-all font-bold text-xs uppercase tracking-wider"
            :class="showConsole ? 'neu-pressed text-blue-600' : 'neu-flat hover:text-blue-500 text-gray-500'">
            <TerminalSquare class="w-4 h-4" :class="{ 'animate-pulse': isAiGenerating }" />
          </button>
        </div>

        <div class="relative" ref="languageMenuRef">
          <button @click.stop="showLanguageMenu = !showLanguageMenu"
            class="flex items-center gap-2 px-3 py-2.5 rounded-xl transition-all font-bold text-xs uppercase tracking-wider"
            :class="showLanguageMenu ? 'neu-pressed text-emerald-600' : 'neu-flat hover:text-emerald-500 text-gray-500'">
            <Languages class="w-4 h-4" />
          </button>
          <transition name="pop">
            <div v-if="showLanguageMenu"
              class="absolute top-full right-0 mt-2 z-50 rounded-xl">
              <LanguageSwitcher />
            </div>
          </transition>
        </div>

        <button @click="resetLayout"
          class="p-2.5 rounded-full neu-flat hover:text-blue-500 active:neu-pressed transition-all text-gray-500"
          :title="t('workbench.resetLayout')">
          <RotateCcw class="w-4 h-4" />
        </button>

        <!-- Export Button -->
        <div class="w-px h-6 bg-gray-300 mx-1"></div>

        <div class="relative group/export" ref="exportMenuRef">
          <NeuButton size="sm" variant="primary" @click.stop="showExportMenu = !showExportMenu"
            class="px-5 py-2.5 rounded-xl text-xs font-bold shadow-md active:shadow-inner transition-all flex items-center">
            <Download class="w-4 h-4 mr-2" /> {{ t('workbench.export.title') }}
            <ChevronDown class="w-3 h-3 ml-2 opacity-70" />
          </NeuButton>

          <transition name="pop">
            <div v-if="showExportMenu"
              class="absolute top-full right-0 mt-2 w-40 bg-[#E0E5EC] rounded-xl shadow-xl border border-white/50 z-50 flex flex-col overflow-hidden p-1.5">
              <button @click="handleExportAssets"
                class="flex items-center gap-2 px-3 py-2.5 rounded-lg hover:bg-white/50 hover:shadow-sm transition-all text-xs font-bold text-gray-600 active:scale-95">
                <Package class="w-4 h-4 text-orange-500" /> {{ t('workbench.export.assets') }}
              </button>
              <button @click="openStoryboardExportPreview"
                class="flex items-center gap-2 px-3 py-2.5 rounded-lg hover:bg-white/50 hover:shadow-sm transition-all text-xs font-bold text-gray-600 active:scale-95">
                <FileText class="w-4 h-4 text-purple-500" /> {{ t('workbench.export.storyboard') }}
              </button>
              <div class="h-px bg-gray-200/50 mx-2"></div>
              <button @click="handleExportVideo"
                class="flex items-center gap-2 px-3 py-2.5 rounded-lg hover:bg-white/50 hover:shadow-sm transition-all text-xs font-bold text-gray-600 active:scale-95">
                <Film class="w-4 h-4 text-blue-500" /> {{ t('workbench.export.video') }}
              </button>
            </div>
          </transition>
        </div>
      </div>
    </header>

    <!-- Main Content Area -->
    <div class="flex-1 flex min-h-0 relative gap-0 items-stretch z-10">
      <template v-for="(moduleName, index) in layoutOrder" :key="moduleName">

        <ScriptEditor id="tour-script-editor" v-if="moduleName === 'script'" :width="moduleWidths.script"
          :data="scriptData" @handle-down="onHandleMouseDown(index)" @drag-start="handleModuleDragStart($event, index)"
          @drop="handleModuleDrop($event, index)" @generate-media="handleGenerateMedia"
          @request-save="persistState(true)" @init-data="(newData) => {
            if (newData === 'FETCH') refreshEpisodeData()
            else { scriptData = newData; persistState(true); }
          }"
          @stream-start="(msg) => { isAiGenerating = true; showConsole = true; currentStatus = msg || t('workbench.status.thinking'); streamLogs = [] }"
          @stream-message="handleStreamMessage"
          @stream-end="() => { isAiGenerating = false; currentStatus = ''; refreshEpisodeData() }" />

        <div id="tour-preview-module" v-if="moduleName === 'preview'"
          class="flex-1 min-w-[20%] flex flex-col relative group/preview" draggable="true"
          @dragstart="handleModuleDragStart($event, index)" @drop="handleModuleDrop($event, index)" @dragover.prevent>
          <PreviewModule ref="previewModuleRef" class="flex-1 h-full" :timeline="timelineTracks"
            @handle-down="onHandleMouseDown(index)" @update-item="handleUpdateTimelineItem"
            @time-update="handleTimeUpdate" @duration-update="handleDurationUpdate"
            @play-state-change="handlePlayStateChange" />
        <transition name="fade">
            <div v-if="isAiGenerating"
              class="absolute top-4 left-1/2 -translate-x-1/2 z-50 bg-[#E0E5EC]/90 backdrop-blur-md text-blue-600 px-5 py-2.5 rounded-full shadow-[5px_5px_10px_#b8b9be,-5px_-5px_10px_#ffffff] flex items-center gap-3 border border-white/20 cursor-pointer hover:scale-105 transition-all select-none"
              @click="showConsole = true">
              <Loader2 class="w-4 h-4 animate-spin text-blue-500" />
              <span class="text-xs font-mono font-bold tracking-wide">{{ currentStatus || t('workbench.status.thinking') }}</span>
            </div>
          </transition>
        </div>

        <!-- Resizer -->
        <div v-if="index < layoutOrder.length - 1"
          class="w-4 cursor-col-resize flex items-center justify-center hover:text-blue-500 transition-colors z-20 shrink-0 relative group"
          @mousedown.prevent="startResize(index)">
          <div class="absolute inset-y-0 -left-2 -right-2 z-10"></div>
          <div class="w-1.5 h-8 rounded-full neu-pressed group-hover:bg-blue-400/20 transition-colors"></div>
        </div>

      </template>
    </div>

    <TimelineModule id="tour-timeline" v-model:tracks="timelineTracks" :current-time="currentTimestamp"
      :total-duration="totalDuration" :is-playing="isPlaying" :volume="volume" :is-muted="isMuted"
      :playback-rate="playbackRate"
      @seek="(t) => { if (Array.isArray(previewModuleRef)) previewModuleRef[0].seek(t); else previewModuleRef.seek(t); currentTimestamp = t; }"
      @toggle-play="togglePlay" @update:volume="updateVolume" @update:is-muted="(m) => isMuted = m"
      @update:playback-rate="updatePlaybackRate" @open-library="showVideoLibrary = !showVideoLibrary"
      @persist="persistState(true)" />

    <transition name="pop">
      <div v-if="showVideoLibrary"
        class="fixed z-[90] bg-[#E0E5EC] rounded-2xl flex flex-col shadow-2xl border border-white/40 overflow-hidden"
        :style="{ left: libWindow.x + 'px', top: libWindow.y + 'px', width: libWindow.w + 'px', height: libWindow.h + 'px' }">
        <div
          class="flex items-center justify-between px-4 py-3 bg-[#E0E5EC] border-b border-gray-200/40 cursor-move select-none shrink-0"
          @mousedown="startLibDrag">
          <div class="flex items-center gap-2 overflow-hidden text-gray-500">
            <Film class="w-4 h-4 text-blue-500" />
            <h3 class="font-bold text-gray-600 text-xs tracking-wider uppercase">{{ t('workbench.videoLibrary.title') }}</h3>
          </div>
          <button @click="showVideoLibrary = false"
            class="p-1 rounded-full neu-flat hover:text-red-500 active:neu-pressed transition-all text-gray-400"
            @mousedown.stop>
            <X class="w-3.5 h-3.5" />
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-3 custom-scroll grid gap-3 content-start bg-[#E0E5EC]"
          style="grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));">
          <div v-if="videoLibrary.length === 0"
            class="col-span-full py-10 flex flex-col items-center justify-center text-gray-400 gap-2 opacity-60">
            <div class="w-12 h-12 rounded-full neu-pressed flex items-center justify-center">
              <Film class="w-5 h-5" />
            </div>
            <span class="text-xs font-bold">{{ t('workbench.videoLibrary.empty') }}</span>
          </div>
          <div v-for="item in videoLibrary.filter(i => i.type === 'video')" :key="item.id"
            class="aspect-video neu-flat rounded-xl flex items-center justify-center relative group cursor-grab active:cursor-grabbing hover:scale-[1.02] transition-transform overflow-hidden"
            draggable="true" @click="openVideoPreview(item)"
            @dragstart="(e) => { e.dataTransfer?.setData('type', 'asset'); e.dataTransfer?.setData('payload', JSON.stringify(item)) }">
            <video :src="item.src + '#t=0.1'" class="w-full h-full object-cover pointer-events-none"
              preload="metadata"></video>
            <div
              class="absolute inset-0 bg-gray-200 opacity-0 group-hover:opacity-10 transition-opacity pointer-events-none">
            </div>
            <span
              class="text-[9px] absolute bottom-1 left-1 bg-[#E0E5EC]/80 backdrop-blur text-gray-600 px-1.5 py-0.5 rounded-md font-bold shadow-sm pointer-events-none truncate max-w-[90%]">{{
                item.name || t('workbench.videoLibrary.untitled') }}</span>
          </div>
        </div>
        <div
          class="absolute bottom-0 right-0 w-6 h-6 cursor-nwse-resize flex items-end justify-end p-1 text-gray-400 hover:text-gray-600 z-10"
          @mousedown="startLibResize"></div>
      </div>
    </transition>

    <AiDirectorModule :visible="showAiDirector" :loading="isAiGenerating" @close="showAiDirector = false"
      @generate="handleGenerateStream" @stop="handleStopGenerate" />

    <ExecutionConsole :visible="showConsole" :logs="streamLogs" @close="showConsole = false" />

    <transition name="fade">
      <div
        v-if="showStoryboardExportPreview"
        class="fixed inset-0 z-[95] bg-black/35 backdrop-blur-sm flex items-center justify-center p-4"
        @click.self="showStoryboardExportPreview = false"
      >
        <div class="storyboard-preview-shell w-full max-w-6xl max-h-[92vh] flex flex-col overflow-hidden">
          <div class="storyboard-preview-header px-6 py-4 border-b border-[#d4c8ae] flex items-center justify-between">
            <div>
              <h3 class="text-xl font-black text-[#5f4f39] tracking-wide">{{ t('workbench.export.previewTitle') }}</h3>
              <p class="text-xs text-[#8b7658] mt-1">{{ t('workbench.export.previewSubtitle', { count: storyboardExportItems.length }) }}</p>
              <p v-if="storyboardPromptLoading" class="text-[11px] text-[#9f8867] mt-1">
                {{ t('workbench.export.promptLoading') }}
              </p>
            </div>
            <button
              class="p-2 rounded-full bg-[#efe4d1] text-[#7c6645] hover:bg-[#e6d8c0] transition-colors"
              @click="showStoryboardExportPreview = false"
              :aria-label="t('workbench.export.closePreview')"
              :title="t('workbench.export.closePreview')"
            >
              <X class="w-4 h-4" />
            </button>
          </div>

          <div class="flex-1 overflow-y-auto custom-scroll p-6 storyboard-preview-body">
            <div
              v-if="!storyboardExportItems.length"
              class="h-full min-h-[280px] rounded-2xl border border-dashed border-[#ccbfa7] bg-[#f5ecdc] flex items-center justify-center text-sm text-[#9b8466]"
            >
              {{ t('workbench.export.noStoryboardData') }}
            </div>

            <div v-else class="flex flex-col gap-6">
              <article
                v-for="item in storyboardExportItems"
                :key="`storyboard-export-${item.index}-${item.shotId}`"
                class="storyboard-paper-card relative"
              >
                <div class="storyboard-tape"></div>
                <div class="p-5">
                  <div class="storyboard-note">
                    <div class="flex items-center justify-between gap-3 mb-3">
                      <div class="flex items-center gap-2 text-[#7e6b4e]">
                        <span class="text-[11px] font-bold px-2 py-0.5 rounded bg-[#eadfcf] border border-[#d3c5ac]">
                          {{ t('workbench.export.shotLabel', { number: item.index + 1 }) }}
                        </span>
                        <span class="text-[11px] font-semibold text-[#9b8768]">#{{ item.shotId }}</span>
                        <span v-if="item.shotType" class="text-[11px] text-[#826f52]">{{ item.shotType }}</span>
                      </div>
                    </div>

                    <h4 class="text-sm font-bold text-[#604f3a] mb-2">
                      {{ item.action || t('workbench.export.emptyAction') }}
                    </h4>

                    <div class="rounded-lg border border-[#d7c9b0] bg-[#fcf8ef] p-3 shadow-inner">
                      <div class="flex items-start justify-between gap-2 mb-2">
                        <div class="flex items-center gap-2">
                          <p class="text-[11px] font-semibold text-[#8e795b]">{{ t('workbench.export.promptLabel') }}</p>
                        </div>
                        <div class="flex items-center gap-2 shrink-0">
                          <a
                            v-if="item.imageUrl"
                            :href="item.imageUrl"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="style-ref-thumb"
                            :title="t('workbench.export.openImage')"
                            :aria-label="t('workbench.export.openImage')"
                          >
                            <img :src="item.imageUrl" class="w-full h-full object-cover" />
                          </a>
                          <a
                            v-if="item.showStyleRefImage"
                            :href="item.styleRefImageUrl"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="style-ref-thumb"
                            :title="t('workbench.export.styleReferenceLabel')"
                            :aria-label="t('workbench.export.styleReferenceLabel')"
                          >
                            <img :src="item.styleRefImageUrl" class="w-full h-full object-cover" />
                          </a>
                        </div>
                      </div>
                      <pre class="text-xs leading-relaxed whitespace-pre-wrap break-words text-[#5c4c36] font-mono">{{ item.prompt || t('workbench.export.emptyPrompt') }}</pre>
                      <div class="mt-2 flex items-center gap-2 text-[11px] text-[#77644a]">
                        <span class="font-semibold">{{ t('workbench.export.videoLinkLabel') }}</span>
                        <a
                          v-if="item.videoUrl"
                          :href="item.videoUrl"
                          target="_blank"
                          rel="noopener noreferrer"
                          class="text-[#6b5ce7] hover:underline break-all"
                        >
                          {{ t('workbench.export.openVideo') }}
                        </a>
                        <span v-else class="text-[#9b8666]">{{ t('workbench.export.noVideoYet') }}</span>
                      </div>
                    </div>

                    <div class="mt-3 flex flex-wrap items-center gap-2">
                      <button
                        class="storyboard-action-btn"
                        @click="copyStoryboardPrompt(item)"
                      >
                        <Copy class="w-3.5 h-3.5" />
                        {{ t('workbench.export.copyPrompt') }}
                      </button>
                      <button
                        class="storyboard-action-btn"
                        @click="copyStoryboardImage(item)"
                      >
                        <Image class="w-3.5 h-3.5" />
                        {{ t('workbench.export.copyImage') }}
                      </button>
                    </div>
                  </div>
                </div>
              </article>
            </div>
          </div>

          <div class="storyboard-preview-footer px-6 py-4 border-t border-[#d4c8ae] flex items-center justify-between gap-3">
            <button class="storyboard-footer-btn" @click="copyAllStoryboardPrompts">
              <Copy class="w-4 h-4" />
              {{ t('workbench.export.copyAllPrompts') }}
            </button>

            <div class="flex items-center gap-2">
              <button class="storyboard-footer-btn" @click="showStoryboardExportPreview = false">
                {{ t('workbench.export.closePreview') }}
              </button>
              <NeuButton size="sm" variant="primary" @click="handleConfirmExportStoryboard">
                <FileText class="w-4 h-4 mr-1" />
                {{ t('workbench.export.confirmExport') }}
              </NeuButton>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <NeuConfirm />

    <VideoPreviewModal :visible="videoPreviewVisible" :video-url="currentVideoUrl" :poster-url="currentVideoPoster"
      @close="videoPreviewVisible = false" />

    <!-- Export Progress Overlay -->
    <transition name="fade">
      <div v-if="isExporting"
        class="fixed inset-0 z-[100] bg-black/40 backdrop-blur-sm flex items-center justify-center">
        <div
          class="bg-[#E0E5EC] rounded-2xl shadow-2xl p-8 max-w-sm w-full flex flex-col items-center gap-6 border border-white/60">
          <div class="relative w-20 h-20 flex items-center justify-center">
            <!-- Spinner -->
            <svg class="animate-spin w-full h-full text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none"
              viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
              </path>
            </svg>
            <span class="absolute text-xs font-bold text-blue-600">{{ exportProgress }}%</span>
          </div>

          <div class="text-center space-y-2">
            <h3 class="text-lg font-bold text-gray-700">{{ exportStatusText }}</h3>
            <p class="text-xs text-gray-500">{{ t('workbench.export.keepPageOpen') }}</p>
          </div>

          <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden shadow-inner">
            <div class="bg-blue-500 h-full transition-all duration-300 ease-out"
              :style="{ width: exportProgress + '%' }">
            </div>
          </div>
        </div>
      </div>
    </transition>

  </div>
</template>

<style scoped>
.custom-scroll::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}

.custom-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scroll::-webkit-scrollbar-thumb {
  background-color: #cbd5e0;
  border-radius: 10px;
  border: 1px solid #E0E5EC;
}

.custom-scroll::-webkit-scrollbar-thumb:hover {
  background-color: #a0aec0;
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.pop-enter-active,
.pop-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  transform-origin: top right;
}

.pop-enter-from,
.pop-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.storyboard-preview-shell {
  border-radius: 1.25rem;
  border: 1px solid #e7dbc6;
  background: linear-gradient(180deg, #f7efdf 0%, #efe2cb 100%);
  box-shadow: 0 30px 50px rgba(61, 46, 27, 0.35);
}

.storyboard-preview-header,
.storyboard-preview-footer {
  background: linear-gradient(180deg, #f6eddc 0%, #ecdfc7 100%);
}

.storyboard-preview-body {
  background:
    radial-gradient(circle at 15% 15%, rgba(255, 255, 255, 0.55) 0, transparent 45%),
    repeating-linear-gradient(0deg, rgba(158, 132, 96, 0.05) 0, rgba(158, 132, 96, 0.05) 1px, transparent 1px, transparent 26px),
    #f4ead8;
}

.storyboard-paper-card {
  background: #fff9ef;
  border: 1px solid #d9c8ac;
  border-radius: 1rem;
  box-shadow:
    0 10px 20px rgba(79, 60, 33, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.storyboard-tape {
  position: absolute;
  top: -12px;
  left: 50%;
  width: 96px;
  height: 22px;
  transform: translateX(-50%) rotate(-1.8deg);
  background: rgba(238, 214, 151, 0.75);
  border: 1px solid rgba(172, 145, 87, 0.4);
  box-shadow: 0 3px 6px rgba(61, 46, 27, 0.18);
}

.storyboard-photo-frame {
  border-radius: 0.75rem;
  border: 1px solid #d2c1a6;
  background: #e8dcc8;
  box-shadow:
    inset 0 0 0 6px #f8f1e5,
    inset 0 0 0 7px #d9c8ad;
  aspect-ratio: 16 / 9;
  overflow: hidden;
}

.storyboard-note {
  background: #fdf8ee;
  border: 1px solid #e2d4bc;
  border-radius: 0.75rem;
  padding: 0.85rem;
}

.storyboard-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.6rem;
  font-size: 11px;
  font-weight: 700;
  color: #6f5a3d;
  border-radius: 0.55rem;
  border: 1px solid #d8c7ab;
  background: #f5e9d5;
  transition: all 0.2s ease;
}

.storyboard-action-btn:hover {
  background: #f0e1c9;
  color: #5e4c34;
}

.storyboard-footer-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.45rem 0.75rem;
  border-radius: 0.65rem;
  border: 1px solid #d8c8ac;
  background: #f5ead8;
  color: #6b583d;
  font-size: 12px;
  font-weight: 700;
  transition: all 0.2s ease;
}

.storyboard-footer-btn:hover {
  background: #efdfc6;
}

.style-ref-thumb {
  width: 64px;
  height: 42px;
  flex-shrink: 0;
  border-radius: 0.45rem;
  overflow: hidden;
  border: 1px solid #d8c8ae;
  background: #ece1cf;
  cursor: zoom-in;
  box-shadow: 0 1px 3px rgba(93, 72, 39, 0.18);
}
</style>
