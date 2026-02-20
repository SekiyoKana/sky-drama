<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  ArrowLeft,
  Save,
  BookOpen,
  X,
  Languages,
  Settings2,
  WandSparkles,
  UserRound,
  MapPin
} from 'lucide-vue-next'
import NeuButton from '@/components/base/NeuButton.vue'
import NeuSelect from '@/components/base/NeuSelect.vue'
import NeuMentionSelector from '@/components/base/NeuMentionSelector.vue'
import NeuConfirm from '@/components/base/NeuConfirm.vue'
import LanguageSwitcher from '@/components/base/LanguageSwitcher.vue'
import ScriptCharacters from '@/views/workbench/components/ScriptCharacters.vue'
import ScriptScenes from '@/views/workbench/components/ScriptScenes.vue'
import BookPreview from '@/views/workbench/components/BookPreview.vue'
import CharacterCreateModal from '@/views/workbench/components/CharacterCreateModal.vue'
import { aiApi, apiKeyApi, episodeApi, projectApi } from '@/api'
import { normalizePlatform } from '@/platforms'
import { resolveImageUrl } from '@/utils/assets'
import { safeRandomUUID } from '@/utils/id'
import { useMention } from '@/utils/useMention'
import { useMessage } from '@/utils/useMessage'
import { useConfirm } from '@/utils/useConfirm'

type NovelCharacter = {
  id: string
  name: string
  role?: string
  description?: string
  image_url?: string
  reference_image?: string
}

type NovelScene = {
  id: string
  location_name: string
  mood?: string
  description?: string
  visual_prompt?: string
  image_url?: string
  reference_image?: string
}

type ModelType = 'text' | 'image' | 'video' | 'audio'
type ModelCatalog = {
  all: string[]
  byType: Record<ModelType, string[]>
}

type PlanOption = {
  id: string
  name: string
  subtitle: string
}

type SnowflakeSuggestion = {
  id: string
  name: string
  reason: string
}

type SnowflakePlan = {
  oneSentence: string
  chapterSummary: string
  majorBeats: string[]
  characterSuggestions: SnowflakeSuggestion[]
  sceneSuggestions: SnowflakeSuggestion[]
}

type RewriteMode = 'expand' | 'rewrite'
type MentionItem = {
  id: string
  name: string
  type: 'character' | 'scene'
  image_url?: string
  role?: string
  mood?: string
  description?: string
}

const route = useRoute()
const router = useRouter()
const message = useMessage()
const { show: showConfirm } = useConfirm()
const { t, locale } = useI18n()

const projectId = Number(route.params.projectId)
const episodeId = Number(route.params.episodeId)

const loading = ref(true)
const project = ref<any>(null)
const episode = ref<any>(null)
const draftText = ref('')
const novelCharacters = ref<NovelCharacter[]>([])
const novelScenes = ref<NovelScene[]>([])
const referenceEntityTab = ref<'characters' | 'scenes'>('characters')
const previewVisible = ref(false)
const previewIndex = ref(0)
const previewList = ref<any[]>([])

const novelConfig = reactive({
  key_id: '' as string | number,
  model: '',
  image_key_id: '' as string | number,
  image_model: '',
  perspective: 'third',
  tone: 'cinematic',
  length: 'medium',
  temperature: 0.7
})

const showCharModal = ref(false)

const loadingKeys = ref(false)
const fetchingModels = ref(false)
const availableKeys = ref<any[]>([])
const textModelOptions = ref<string[]>([])
const imageModelOptions = ref<string[]>([])
const modelCache = ref<Record<string, ModelCatalog>>({})
const configTag = ref<'text' | 'image'>('text')
const generatingItems = reactive<Record<string, number>>({})

const showLanguageMenu = ref(false)
const showModelConfig = ref(false)
const showSnowflakeAssistant = ref(false)
const languageMenuRef = ref<HTMLElement | null>(null)
const snowflakeWindowState = reactive({
  x: Math.max(24, window.innerWidth - 680),
  y: 84,
  w: 640,
  h: 580
})
let isSnowflakeDragging = false
let isSnowflakeResizing = false
const snowflakeDragOffset = reactive({ x: 0, y: 0 })

const chapterBrief = ref('')
const targetWordCount = ref(1000)
const planLoading = ref(false)
const chapterWriting = ref(false)
const snowflakePlan = ref<SnowflakePlan | null>(null)
const selectedPlanCharacterIds = ref<string[]>([])
const selectedPlanSceneIds = ref<string[]>([])
const snowflakeStatus = ref<'idle' | 'planned' | 'confirmed' | 'cancelled'>('idle')

const showRewriteAssistant = ref(false)
const rewriteLoading = ref(false)
const rewriteMode = ref<RewriteMode>('expand')
const rewriteInstruction = ref('')
const rewriteTargetWords = ref(200)
const rewriteSelection = reactive({
  start: 0,
  end: 0,
  text: ''
})
const rewriteTooltipRef = ref<HTMLElement | null>(null)
const rewriteTooltipPos = reactive({ x: 0, y: 0 })
const rewriteTooltipPlacement = ref<'top' | 'bottom'>('top')
const mentionInfoVisible = ref(false)
const mentionInfoData = ref<MentionItem | null>(null)
const mentionInfoPos = reactive({ x: 0, y: 0 })
const pendingRewrite = ref<null | {
  previousText: string
  currentText: string
  start: number
  end: number
  scrollTop: number
}>(null)

const draftInputRef = ref<HTMLTextAreaElement | null>(null)
const {
  isMentionVisible,
  mentionX,
  mentionY,
  mentionQuery,
  mentionStartIndex,
  handleInput: handleMentionInput,
  closeMention: hideMention
} = useMention(draftInputRef)

const normalizeMentionId = (type: 'character' | 'scene', rawId: string) => {
  const idText = String(rawId || '').trim()
  const targetPrefix = type === 'character' ? 'char_' : 'scene_'
  return idText.startsWith(targetPrefix) ? idText : `${targetPrefix}${idText}`
}

const buildMentionToken = (item: MentionItem) => `@${String(item?.name || '').trim()}`

const findMentionByTypeAndId = (type: 'character' | 'scene', rawId: string) => {
  const id = normalizeMentionId(type, rawId)
  const hit = mentionById.value.get(id)
  if (hit && hit.type === type) return hit
  return mentionItems.value.find((item) => item.type === type && item.id === id) || null
}

const convertPlaceholdersToMentions = (rawText: string) => {
  const text = String(rawText || '')
  const regex = /\{\{\s*((?:char|scene)_[a-zA-Z0-9_]+)\s*\}\}/g
  return text.replace(regex, (_all, rawId: string) => {
    const id = String(rawId || '').trim()
    if (!id) return _all
    const type = id.startsWith('char_') ? 'character' : 'scene'
    const match = findMentionByTypeAndId(type, id)
    return match ? buildMentionToken(match) : _all
  })
}

const asciiWordRe = /[A-Za-z0-9_]/

const isNameWordLike = (name: string) => asciiWordRe.test(name)

const convertKnownNamesToMentions = (rawText: string) => {
  let text = String(rawText || '')
  if (!text) return text

  mentionCandidates.value.forEach((item) => {
    const name = item.name.trim()
    if (!name) return
    const nameRegex = new RegExp(name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')
    text = text.replace(nameRegex, (matched: string, offset: number, source: string) => {
      const prevChar = offset > 0 ? (source[offset - 1] ?? '') : ''
      const nextChar = offset + matched.length < source.length ? (source[offset + matched.length] ?? '') : ''
      if (prevChar === '@') return matched
      if (isNameWordLike(name) && (asciiWordRe.test(prevChar) || asciiWordRe.test(nextChar))) return matched
      return item.token
    })
  })

  return text
}

const normalizeGeneratedMentionText = (rawText: string) => {
  const withPlaceholders = convertPlaceholdersToMentions(rawText)
  return convertKnownNamesToMentions(withPlaceholders)
}

const clampWordCount = (raw: unknown) => {
  const parsed = Number(raw)
  if (Number.isNaN(parsed)) return 1000
  return Math.max(200, Math.min(12000, Math.round(parsed)))
}

const draftPlaceholder = computed(() => {
  return [
    t('novelWorkbench.journalTitle'),
    t('novelWorkbench.journalHint'),
    t('novelWorkbench.mentionHint'),
    '',
    t('novelWorkbench.journalPlaceholder')
  ].join('\n')
})

const rewriteActionLabel = computed(() => (
  rewriteMode.value === 'expand'
    ? t('novelWorkbench.rewrite.applyExpand')
    : t('novelWorkbench.rewrite.applyRewrite')
))

const showManualTextModelInput = computed(() => {
  return !!novelConfig.key_id && !fetchingModels.value && textModelOptions.value.length === 0
})

const showManualImageModelInput = computed(() => {
  return !!novelConfig.image_key_id && !fetchingModels.value && imageModelOptions.value.length === 0
})

const activeConfigKey = computed<string | number>({
  get: () => (configTag.value === 'text' ? novelConfig.key_id : novelConfig.image_key_id),
  set: (value) => {
    if (configTag.value === 'text') novelConfig.key_id = value
    else novelConfig.image_key_id = value
  }
})

const activeConfigModel = computed<string>({
  get: () => (configTag.value === 'text' ? novelConfig.model : novelConfig.image_model),
  set: (value) => {
    if (configTag.value === 'text') novelConfig.model = value
    else novelConfig.image_model = value
  }
})

const activeModelOptions = computed(() => (
  configTag.value === 'text' ? textModelOptions.value : imageModelOptions.value
))

const showActiveManualModelInput = computed(() => (
  configTag.value === 'text' ? showManualTextModelInput.value : showManualImageModelInput.value
))

const scriptCharacters = computed(() => {
  const script = (episode.value?.ai_config?.generated_script || {}) as any
  return Array.isArray(script.characters) ? script.characters : []
})

const scriptScenes = computed(() => {
  const script = (episode.value?.ai_config?.generated_script || {}) as any
  return Array.isArray(script.scenes) ? script.scenes : []
})

const mentionItems = computed<MentionItem[]>(() => {
  const picked = new Set<string>()
  const out: MentionItem[] = []

  const pushCharacter = (char: any) => {
    const rawId = String(char?.id || '').trim()
    if (!rawId) return
    const id = normalizeMentionId('character', rawId)
    const key = `character:${id}`
    if (picked.has(key)) return
    picked.add(key)
    out.push({
      id,
      name: String(char?.name || t('novelWorkbench.unknownCharacter')),
      type: 'character',
      image_url: resolveImageUrl(String(char?.image_url || char?.reference_image || '')),
      role: String(char?.role || '').trim(),
      description: String(char?.description || '').trim()
    })
  }

  const pushScene = (scene: any) => {
    const rawId = String(scene?.id || '').trim()
    if (!rawId) return
    const id = normalizeMentionId('scene', rawId)
    const key = `scene:${id}`
    if (picked.has(key)) return
    picked.add(key)
    out.push({
      id,
      name: String(scene?.location_name || t('novelWorkbench.unknownScene')),
      type: 'scene',
      image_url: resolveImageUrl(String(scene?.image_url || scene?.reference_image || '')),
      mood: String(scene?.mood || '').trim(),
      description: String(scene?.description || '').trim()
    })
  }

  novelCharacters.value.forEach(pushCharacter)
  novelScenes.value.forEach(pushScene)
  scriptCharacters.value.forEach(pushCharacter)
  scriptScenes.value.forEach(pushScene)
  return out
})

const mentionById = computed(() => {
  const out = new Map<string, MentionItem>()
  mentionItems.value.forEach((item) => out.set(item.id, item))
  return out
})

const mentionCandidates = computed(() => (
  mentionItems.value
    .map((item) => ({ ...item, token: buildMentionToken(item) }))
    .filter((item) => item.name.trim().length > 0)
    .sort((a, b) => b.name.length - a.name.length)
))

const referenceEntityTabs = computed(() => [
  { id: 'characters' as const, label: t('workbench.scriptEditor.tabs.characters'), icon: UserRound },
  { id: 'scenes' as const, label: t('workbench.scriptEditor.tabs.scenes'), icon: MapPin }
])

const characterPlanOptions = computed<PlanOption[]>(() => (
  novelCharacters.value.map((char) => ({
    id: normalizeMentionId('character', String(char.id)),
    name: String(char.name || t('novelWorkbench.unknownCharacter')),
    subtitle: String(char.role || char.description || '')
  }))
))

const scenePlanOptions = computed<PlanOption[]>(() => (
  novelScenes.value.map((scene) => ({
    id: normalizeMentionId('scene', String(scene.id)),
    name: String(scene.location_name || t('novelWorkbench.unknownScene')),
    subtitle: String(scene.mood || scene.description || '')
  }))
))

const characterPlanMap = computed(() => {
  const map = new Map<string, PlanOption>()
  for (const item of characterPlanOptions.value) map.set(item.id, item)
  return map
})

const scenePlanMap = computed(() => {
  const map = new Map<string, PlanOption>()
  for (const item of scenePlanOptions.value) map.set(item.id, item)
  return map
})

const inferModelTypesById = (modelId: string): Set<ModelType> => {
  const v = String(modelId || '').toLowerCase()
  const out = new Set<ModelType>()
  if (['chat', 'gpt', 'claude', 'deepseek', 'qwen', 'llama', 'gemini', 'doubao', 'text', 'instruct', 'reasoner'].some((kw) => v.includes(kw))) out.add('text')
  if (['image', 'vision', 'flux', 'sd', 'stable-diffusion', 'dall', 'seedream', 'recraft', 'pixart', 'cogview'].some((kw) => v.includes(kw))) out.add('image')
  if (['video', 'sora', 'seedance', 'runway', 'pika', 'veo', 'kling', 'wanx', 'hunyuan-video', 'i2v', 't2v'].some((kw) => v.includes(kw))) out.add('video')
  if (['audio', 'speech', 'tts', 'voice', 'whisper', 'asr', 'transcribe'].some((kw) => v.includes(kw))) out.add('audio')
  if (out.size === 0) out.add('text')
  return out
}

const buildFallbackCatalog = (models: string[]): ModelCatalog => {
  const byType: Record<ModelType, string[]> = { text: [], image: [], video: [], audio: [] }
  for (const model of models) {
    inferModelTypesById(model).forEach((type) => {
      if (!byType[type].includes(model)) byType[type].push(model)
    })
  }
  return { all: models, byType }
}

const toModelCatalog = (res: any): ModelCatalog => {
  const all = Array.isArray(res?.models) ? res.models.map((m: any) => String(m)) : []
  const byTypeFromApi = res?.models_by_type
  const hasStructuredGroups =
    byTypeFromApi &&
    typeof byTypeFromApi === 'object' &&
    ['text', 'image', 'video', 'audio'].every((k) => Array.isArray(byTypeFromApi[k]))

  if (!hasStructuredGroups) return buildFallbackCatalog(all)

  return {
    all,
    byType: {
      text: byTypeFromApi.text.map((m: any) => String(m)),
      image: byTypeFromApi.image.map((m: any) => String(m)),
      video: byTypeFromApi.video.map((m: any) => String(m)),
      audio: byTypeFromApi.audio.map((m: any) => String(m))
    }
  }
}

const applyModelOptions = (keyId: string | number | null | undefined, modelType: 'text' | 'image') => {
  if (!keyId) {
    if (modelType === 'text') textModelOptions.value = []
    else imageModelOptions.value = []
    return
  }
  const cacheKey = String(keyId)
  const catalog = modelCache.value[cacheKey]
  if (!catalog) return
  if (modelType === 'text') {
    textModelOptions.value = catalog.byType.text.length > 0 ? catalog.byType.text : []
  } else {
    imageModelOptions.value = catalog.byType.image.length > 0 ? catalog.byType.image : []
  }
}

const fetchModelsForKey = async (keyId: string | number | null | undefined, modelType: 'text' | 'image') => {
  applyModelOptions(keyId, modelType)
  if (!keyId) return
  const cacheKey = String(keyId)
  if (modelCache.value[cacheKey]) return

  fetchingModels.value = true
  try {
    const res: any = await aiApi.testConnection(Number(keyId))
    const catalog = toModelCatalog(res)
    modelCache.value[cacheKey] = catalog
    applyModelOptions(keyId, modelType)
  } catch (error) {
    console.error('[NovelWorkbench] fetch models failed', error)
  } finally {
    fetchingModels.value = false
  }
}

const loadApiKeys = async () => {
  loadingKeys.value = true
  try {
    const raw: any = await apiKeyApi.list()
    const keys: any[] = Array.isArray(raw) ? raw : Array.isArray(raw?.data) ? raw.data : []
    availableKeys.value = keys.map((k: any) => ({
      label: `${k.name} (${t(`projects.api.platforms.${normalizePlatform(k.platform)}`)})`,
      value: k.id
    }))
  } catch (error) {
    console.error('[NovelWorkbench] load keys failed', error)
  } finally {
    loadingKeys.value = false
  }
}

watch(
  () => novelConfig.key_id,
  (newKey, oldKey) => {
    if (newKey !== oldKey) fetchModelsForKey(newKey, 'text')
  }
)

watch(
  () => novelConfig.image_key_id,
  (newKey, oldKey) => {
    if (newKey !== oldKey) fetchModelsForKey(newKey, 'image')
  }
)

watch(
  () => targetWordCount.value,
  (val) => {
    const next = clampWordCount(val)
    if (next !== val) targetWordCount.value = next
  }
)

watch(
  () => characterPlanOptions.value.map((item) => item.id).join('|'),
  () => {
    selectedPlanCharacterIds.value = selectedPlanCharacterIds.value.filter((id) => characterPlanMap.value.has(id))
  }
)

watch(
  () => scenePlanOptions.value.map((item) => item.id).join('|'),
  () => {
    selectedPlanSceneIds.value = selectedPlanSceneIds.value.filter((id) => scenePlanMap.value.has(id))
  }
)

const makeCharacterId = (index: number) => {
  const ts = Math.floor(Date.now() / 1000)
  const suffix = safeRandomUUID().slice(0, 4)
  return `char_${ts}_${index}_${suffix}`
}

const makeSceneId = (index: number) => {
  const ts = Math.floor(Date.now() / 1000)
  const suffix = safeRandomUUID().slice(0, 4)
  return `scene_${ts}_${index}_${suffix}`
}

const handleAddCharacter = () => {
  showCharModal.value = true
}

const handleCharConfirm = async (charData: { name: string; role: string; description: string }) => {
  novelCharacters.value.unshift({
    id: makeCharacterId(novelCharacters.value.length),
    name: String(charData?.name || '').trim(),
    role: String(charData?.role || '').trim(),
    description: String(charData?.description || '').trim(),
    image_url: '',
    reference_image: ''
  })
  showCharModal.value = false
  await saveNovelConfig(true)
  message.success(t('novelWorkbench.messages.characterCreated'))
}

const handleAddScene = async () => {
  novelScenes.value.unshift({
    id: makeSceneId(novelScenes.value.length),
    location_name: t('workbench.scriptEditor.defaults.newScene'),
    mood: t('workbench.scriptEditor.defaults.neutralMood'),
    description: '',
    visual_prompt: t('workbench.scriptEditor.defaults.newScenePrompt'),
    image_url: '',
    reference_image: ''
  })
  await saveNovelConfig(true)
  openPreview(novelScenes.value, 0)
}

const buildCharacterImagePrompt = (item: NovelCharacter) => {
  const parts = [
    `角色立绘，单人，${item.name || t('novelWorkbench.unknownCharacter')}`,
    item.role ? `角色定位：${item.role}` : '',
    item.description ? `外观与设定：${item.description}` : '',
    '画面干净，主体清晰，风格统一，不要文字水印。'
  ]
  return parts.filter(Boolean).join('，')
}

const buildSceneImagePrompt = (item: NovelScene) => {
  const parts = [
    `场景概念图，地点：${item.location_name || t('novelWorkbench.unknownScene')}`,
    item.mood ? `氛围：${item.mood}` : '',
    item.description ? `场景细节：${item.description}` : '',
    '画面完整，构图清晰，风格统一，不要文字水印。'
  ]
  return parts.filter(Boolean).join('，')
}

const parseMediaFinishPayload = (payload: any): { url: string; finalPrompt: string } => {
  let url = ''
  let finalPrompt = ''
  if (typeof payload === 'string') {
    try {
      const json = JSON.parse(payload)
      url = String(json?.url || '').trim()
      finalPrompt = String(json?.provider_prompt || json?.final_prompt || json?.prompt || '').trim()
    } catch (_error) {
      if (payload.startsWith('http')) {
        url = payload
      }
    }
  } else if (payload && typeof payload === 'object') {
    url = String(payload.url || '').trim()
    finalPrompt = String(payload.provider_prompt || payload.final_prompt || payload.prompt || '').trim()
  }
  return { url, finalPrompt }
}

const getGenerateKey = (kind: 'character' | 'scene', index: number) => (
  kind === 'character' ? `chars-${index}` : `scenes-${index}`
)

const openPreview = (items: any[], index: number) => {
  if (index < 0 || index >= items.length) return
  previewList.value = items
  previewIndex.value = index
  previewVisible.value = true
}

const handleSceneEdit = (item: any) => {
  const idx = novelScenes.value.findIndex((row) => String(row.id) === String(item?.id || ''))
  if (idx >= 0) openPreview(novelScenes.value, idx)
}

const updateNovelEntity = (id: string, updates: Record<string, any>) => {
  if (!id) return false
  const char = novelCharacters.value.find((item) => String(item.id) === String(id))
  if (char) {
    Object.assign(char, updates)
    return true
  }
  const scene = novelScenes.value.find((item) => String(item.id) === String(id))
  if (scene) {
    Object.assign(scene, updates)
    return true
  }
  return false
}

const handlePreviewUpdate = async (payload: any) => {
  const { id, ...updates } = payload || {}
  if (!id || !updates || typeof updates !== 'object') return
  if (!updateNovelEntity(String(id), updates)) return
  await saveNovelConfig(true)
}

const ensureVisualPrompt = (item: any) => {
  if (!item) return
  if (!item.visual_prompt || typeof item.visual_prompt !== 'string') {
    item.visual_prompt = ''
  }
}

const buildRefinePrompt = (
  kind: 'character' | 'scene',
  item: NovelCharacter | NovelScene,
  extraPrompt?: string
) => {
  const parts: string[] = []
  if (kind === 'character') {
    parts.push(
      `[Character Info]\nName: ${String((item as NovelCharacter).name || '')}\nDescription: ${String((item as NovelCharacter).description || '')}`
    )
  } else {
    parts.push(
      `[Scene Info]\nLocation: ${String((item as NovelScene).location_name || '')}\nMood: ${String((item as NovelScene).mood || '')}`
    )
  }
  if ((item as any).visual_prompt) {
    parts.push(`[Current Visual Prompt]\n${String((item as any).visual_prompt || '')}`)
  }
  if (extraPrompt) {
    parts.push(`[Refinement Instruction]\n${extraPrompt}`)
  } else {
    parts.push('[Instruction]\nOptimize the visual prompt for better image generation consistency and detail.')
  }
  return parts.join('\n\n')
}

const ensureImageConfigReady = async () => {
  if (!novelConfig.image_key_id) {
    message.warning(t('novelWorkbench.messages.selectImageConnection'))
    throw new Error('missing image key')
  }
  if (!novelConfig.image_model) {
    message.warning(t('novelWorkbench.messages.selectImageModel'))
    throw new Error('missing image model')
  }
  const saved = await saveNovelConfig(true)
  if (!saved) {
    throw new Error('save failed')
  }
}

const handleGenerateEntity = async (
  kind: 'character' | 'scene',
  type: 'image' | 'text' | 'video',
  item: NovelCharacter | NovelScene,
  index: number,
  extraPrompt?: string,
  updates?: Record<string, any>
) => {
  const key = getGenerateKey(kind, index)
  if (generatingItems[key] !== undefined) return

  if (updates && Object.keys(updates).length > 0) {
    Object.assign(item as any, updates)
    await saveNovelConfig(true)
  }

  if (type === 'video') return

  if (type === 'image' && (item as any).reference_image) {
    const confirmed = await showConfirm(t('workbench.scriptEditor.messages.referenceConfirm'))
    if (!confirmed) return
  }

  generatingItems[key] = 0
  try {
    if (type === 'image') {
      await ensureImageConfigReady()
      const prompt = kind === 'character'
        ? buildCharacterImagePrompt(item as NovelCharacter)
        : buildSceneImagePrompt(item as NovelScene)
      const finalPrompt = extraPrompt ? `${prompt}。补充要求：${extraPrompt}` : prompt
      message.info(t('novelWorkbench.messages.imageGenerating'))

      const mediaResult = await new Promise<{ url: string; finalPrompt: string }>((resolve, reject) => {
        let finishedResult: { url: string; finalPrompt: string } | null = null
        aiApi.skillsStream(
          {
            projectId,
            episodeId,
            prompt: finalPrompt,
            type: 'image',
            data: {
              category: kind,
              reference_image: String((item as any).reference_image || '').trim() || undefined
            }
          } as any,
          {
            onMessage: (msg: any) => {
              if (msg?.type === 'progress') {
                generatingItems[key] = Number(msg.payload || 0)
                return
              }
              if (msg?.type === 'finish') {
                finishedResult = parseMediaFinishPayload(msg.payload)
                return
              }
              if (msg?.type === 'error') {
                reject(new Error(String(msg.payload || 'image generation failed')))
              }
            },
            onError: (error: any) => reject(error),
            onFinish: () => {
              if (!finishedResult?.url) {
                reject(new Error(t('novelWorkbench.messages.imageGenerateFailed')))
                return
              }
              resolve(finishedResult)
            }
          }
        ).catch((error: unknown) => reject(error))
      })

      ;(item as any).image_url = resolveImageUrl(mediaResult.url)
      if (mediaResult.finalPrompt) {
        ;(item as any).generation_prompt = mediaResult.finalPrompt
      }
      await saveNovelConfig(true)
      message.success(t('novelWorkbench.messages.imageGenerated'))
      return
    }

    ensureVisualPrompt(item)
    const refinePrompt = buildRefinePrompt(kind, item, extraPrompt)
    let textResult = ''
    await aiApi.skillsStream(
      {
        projectId,
        episodeId,
        prompt: refinePrompt,
        type: 'text',
        skill: 'short-video-prompt-engineer',
        data: { category: kind }
      } as any,
      {
        onMessage: (msg: any) => {
          if (msg?.type === 'progress') {
            generatingItems[key] = Number(msg.payload || 0)
            return
          }
          if (msg?.type === 'text_finish') {
            textResult = String(msg?.payload?.text || msg?.payload || '')
            return
          }
          if (msg?.type === 'finish' && typeof msg?.payload === 'string' && !textResult) {
            textResult = msg.payload
          }
        }
      }
    )
    ;(item as any).visual_prompt = String(textResult || '').trim()
    await saveNovelConfig(true)
    message.success(t('workbench.scriptEditor.messages.promptRefined'))
  } catch (error) {
    console.error('[NovelWorkbench] generate entity failed', error)
    if (type === 'image') message.error(t('novelWorkbench.messages.imageGenerateFailed'))
    else message.error(t('workbench.scriptEditor.messages.generateFailed'))
  } finally {
    delete generatingItems[key]
  }
}

const handleCharacterGenerate = (type: 'image' | 'text' | 'video', item: any, index: number) => {
  void handleGenerateEntity('character', type, item as NovelCharacter, index)
}

const handleSceneGenerate = (type: 'image' | 'text' | 'video', item: any, index: number) => {
  void handleGenerateEntity('scene', type, item as NovelScene, index)
}

const handlePreviewRegenerate = (payload: any) => {
  const row = payload?.item
  if (!row) return
  const kind: 'character' | 'scene' = row.role !== undefined ? 'character' : 'scene'
  const index = Number(payload?.index ?? 0)
  void handleGenerateEntity(
    kind,
    payload?.type || 'image',
    row,
    index,
    payload?.extraPrompt,
    payload?.updates
  )
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

const summarizeUsageText = (value: unknown, maxLen = 28) => {
  const raw = String(value || '').replace(/\s+/g, ' ').trim()
  if (!raw) return t('novelWorkbench.detail.empty')
  return raw.length > maxLen ? `${raw.slice(0, maxLen)}...` : raw
}

const containsEntityReference = (node: any, entityId: string): boolean => {
  if (!node) return false
  if (typeof node === 'string') return hasEntityReference(node, entityId)
  if (Array.isArray(node)) return node.some((item) => containsEntityReference(item, entityId))
  if (typeof node === 'object') {
    return Object.values(node).some((value) => containsEntityReference(value, entityId))
  }
  return false
}

const buildScriptUsageLabel = (
  group: 'characters' | 'scenes' | 'storyboard',
  index: number,
  row: any
) => {
  const episodeName = summarizeUsageText(episode.value?.title || t('novelWorkbench.chapterUntitled'), 36)
  if (group === 'storyboard') {
    const shotName = summarizeUsageText(row?.action || row?.shot_type || row?.visual_prompt, 36)
    return `${episodeName} - ${t('workbench.scriptEditor.tabs.storyboard')}${index + 1}: [${shotName}]`
  }
  if (group === 'characters') {
    const characterName = summarizeUsageText(row?.name || row?.description, 36)
    return `${episodeName} - ${t('workbench.scriptEditor.tabs.characters')}${index + 1}: [${characterName}]`
  }
  const sceneName = summarizeUsageText(row?.location_name || row?.description, 36)
  return `${episodeName} - ${t('workbench.scriptEditor.tabs.scenes')}${index + 1}: [${sceneName}]`
}

const collectScriptUsagePaths = (entityId: string) => {
  const scriptRoot = (episode.value?.ai_config?.generated_script || {}) as any
  const out = new Set<string>()
  const pushRowUsages = (group: 'characters' | 'scenes' | 'storyboard', rows: any[], matcher: (row: any) => boolean) => {
    rows.forEach((row, idx) => {
      if (out.size >= 12) return
      if (matcher(row)) out.add(buildScriptUsageLabel(group, idx, row))
    })
  }

  const storyboards = Array.isArray(scriptRoot?.storyboard) ? scriptRoot.storyboard : []
  pushRowUsages('storyboard', storyboards, (row) => containsEntityReference(row, entityId))

  const scenes = Array.isArray(scriptRoot?.scenes) ? scriptRoot.scenes : []
  pushRowUsages('scenes', scenes, (row) => (
    normalizeMentionId('scene', String(row?.id || '')) === entityId || containsEntityReference(row, entityId)
  ))

  const characters = Array.isArray(scriptRoot?.characters) ? scriptRoot.characters : []
  pushRowUsages('characters', characters, (row) => (
    normalizeMentionId('character', String(row?.id || '')) === entityId || containsEntityReference(row, entityId)
  ))

  return Array.from(out).slice(0, 12)
}

const handleDeleteEntity = async (kind: 'character' | 'scene', index: number) => {
  const confirmed = await showConfirm(t('workbench.scriptEditor.messages.confirmDelete'))
  if (!confirmed) return

  const list = kind === 'character' ? novelCharacters.value : novelScenes.value
  if (index < 0 || index >= list.length) return
  const target = list[index] as any
  const entityId = normalizeMentionId(kind, String(target?.id || ''))
  if (!entityId) return

  const scriptUsages = collectScriptUsagePaths(entityId)
  if (scriptUsages.length > 0) {
    const usageLines = scriptUsages.map((item) => `- ${item}`).join('\n')
    const crossConfirmed = await showConfirm(
      t('novelWorkbench.messages.deleteCrossUsageConfirm', {
        target: kind === 'character'
          ? t('workbench.scriptEditor.tabs.characters')
          : t('workbench.scriptEditor.tabs.scenes'),
        usages: usageLines
      })
    )
    if (!crossConfirmed) return
  }

  if (kind === 'character') {
    novelCharacters.value = novelCharacters.value.filter(
      (row) => normalizeMentionId('character', String(row?.id || '')) !== entityId
    )
    selectedPlanCharacterIds.value = selectedPlanCharacterIds.value.filter((id) => id !== entityId)
  } else {
    novelScenes.value = novelScenes.value.filter(
      (row) => normalizeMentionId('scene', String(row?.id || '')) !== entityId
    )
    selectedPlanSceneIds.value = selectedPlanSceneIds.value.filter((id) => id !== entityId)
  }

  const saved = await saveNovelConfig(true)
  if (saved) {
    message.success(t('workbench.scriptEditor.messages.deleted'))
  } else {
    message.error(t('novelWorkbench.messages.deleteSaveFailed'))
  }
}

const handleUploadReference = async (
  kind: 'character' | 'scene',
  item: NovelCharacter | NovelScene,
  file: File
) => {
  if (!file) return
  try {
    const res: any = await aiApi.uploadReference(file, kind)
    const url = String(res?.url || '')
    if (!url) throw new Error('Upload failed: no url returned')
    ;(item as any).reference_image = url
    const saved = await saveNovelConfig(true)
    if (saved) message.success(t('workbench.scriptEditor.messages.referenceUploaded'))
    else message.warning(t('workbench.scriptEditor.messages.referenceUploadedButSaveFailed'))
  } catch (error) {
    console.error('[NovelWorkbench] upload reference failed', error)
    message.error(t('workbench.scriptEditor.messages.uploadFailed'))
  }
}

const clampSnowflakeWindow = () => {
  const minW = 420
  const minH = 360
  snowflakeWindowState.w = Math.max(minW, Math.min(snowflakeWindowState.w, window.innerWidth - 24))
  snowflakeWindowState.h = Math.max(minH, Math.min(snowflakeWindowState.h, window.innerHeight - 24))
  snowflakeWindowState.x = Math.max(12, Math.min(snowflakeWindowState.x, window.innerWidth - snowflakeWindowState.w - 12))
  snowflakeWindowState.y = Math.max(12, Math.min(snowflakeWindowState.y, window.innerHeight - snowflakeWindowState.h - 12))
}

const handleWindowResize = () => {
  clampSnowflakeWindow()
  updateRewriteTooltipPosition()
}

const startSnowflakeDrag = (event: MouseEvent) => {
  isSnowflakeDragging = true
  snowflakeDragOffset.x = event.clientX - snowflakeWindowState.x
  snowflakeDragOffset.y = event.clientY - snowflakeWindowState.y
  document.addEventListener('mousemove', onSnowflakeDrag)
  document.addEventListener('mouseup', stopSnowflakeDrag)
  document.body.style.userSelect = 'none'
}

const onSnowflakeDrag = (event: MouseEvent) => {
  if (!isSnowflakeDragging) return
  snowflakeWindowState.x = event.clientX - snowflakeDragOffset.x
  snowflakeWindowState.y = event.clientY - snowflakeDragOffset.y
  clampSnowflakeWindow()
}

const stopSnowflakeDrag = () => {
  isSnowflakeDragging = false
  document.removeEventListener('mousemove', onSnowflakeDrag)
  document.removeEventListener('mouseup', stopSnowflakeDrag)
  document.body.style.userSelect = ''
}

const startSnowflakeResize = (event: MouseEvent) => {
  isSnowflakeResizing = true
  document.addEventListener('mousemove', onSnowflakeResize)
  document.addEventListener('mouseup', stopSnowflakeResize)
  event.stopPropagation()
}

const onSnowflakeResize = (event: MouseEvent) => {
  if (!isSnowflakeResizing) return
  snowflakeWindowState.w = Math.max(420, event.clientX - snowflakeWindowState.x)
  snowflakeWindowState.h = Math.max(360, event.clientY - snowflakeWindowState.y)
  clampSnowflakeWindow()
}

const stopSnowflakeResize = () => {
  isSnowflakeResizing = false
  document.removeEventListener('mousemove', onSnowflakeResize)
  document.removeEventListener('mouseup', stopSnowflakeResize)
}

const buildSnowflakeState = () => ({
  chapter_brief: chapterBrief.value,
  target_words: clampWordCount(targetWordCount.value),
  status: snowflakeStatus.value,
  plan: snowflakePlan.value,
  selected_character_ids: selectedPlanCharacterIds.value,
  selected_scene_ids: selectedPlanSceneIds.value,
  rewrite_target_words: rewriteTargetWords.value > 0 ? Math.round(rewriteTargetWords.value) : 0,
  window: {
    x: snowflakeWindowState.x,
    y: snowflakeWindowState.y,
    w: snowflakeWindowState.w,
    h: snowflakeWindowState.h
  }
})

const saveNovelConfig = async (silent = false) => {
  if (!episode.value) return false

  try {
    const currentAiConfig = episode.value.ai_config || {}
    const nextTextConfig = {
      ...(currentAiConfig.text || {})
    }
    const nextImageConfig = {
      ...(currentAiConfig.image || {})
    }
    if (novelConfig.key_id) nextTextConfig.key_id = novelConfig.key_id
    if (novelConfig.model) nextTextConfig.model = novelConfig.model
    nextTextConfig.temperature = novelConfig.temperature
    if (novelConfig.image_key_id) nextImageConfig.key_id = novelConfig.image_key_id
    if (novelConfig.image_model) nextImageConfig.model = novelConfig.image_model

    const nextConfig = {
      ...currentAiConfig,
      text: nextTextConfig,
      image: nextImageConfig,
      novel: {
        key_id: novelConfig.key_id,
        model: novelConfig.model,
        image_key_id: novelConfig.image_key_id,
        image_model: novelConfig.image_model,
        perspective: novelConfig.perspective,
        tone: novelConfig.tone,
        length: novelConfig.length,
        temperature: novelConfig.temperature,
        draft_text: draftText.value,
        characters: novelCharacters.value,
        scenes: novelScenes.value,
        snowflake: buildSnowflakeState()
      }
    }

    await episodeApi.update(projectId, episodeId, {
      title: episode.value.title,
      ai_config: nextConfig
    } as any)

    episode.value.ai_config = nextConfig
    if (!silent) message.success(t('novelWorkbench.messages.saved'))
    return true
  } catch (error) {
    console.error('[NovelWorkbench] save failed', error)
    if (!silent) message.error(t('novelWorkbench.messages.saveFailed'))
    return false
  }
}

const clearRewriteSelection = () => {
  rewriteSelection.start = 0
  rewriteSelection.end = 0
  rewriteSelection.text = ''
  showRewriteAssistant.value = false
}

const focusEditorWithViewport = (scrollTop: number, start: number, end: number) => {
  nextTick(() => {
    const textarea = draftInputRef.value
    if (!textarea) return
    textarea.focus()
    textarea.scrollTop = scrollTop
    textarea.setSelectionRange(start, end)
  })
}

const cancelPendingRewritePreview = () => {
  const pending = pendingRewrite.value
  if (!pending) return
  draftText.value = pending.previousText
  pendingRewrite.value = null
  clearRewriteSelection()
  focusEditorWithViewport(pending.scrollTop, pending.start, pending.start)
}

const confirmPendingRewritePreview = async () => {
  const pending = pendingRewrite.value
  if (!pending) return
  pendingRewrite.value = null
  clearRewriteSelection()
  focusEditorWithViewport(pending.scrollTop, pending.end, pending.end)
  await saveNovelConfig(true)
}

const getTextareaCaretPoint = (textarea: HTMLTextAreaElement, caret: number) => {
  const mirror = document.createElement('div')
  const computed = window.getComputedStyle(textarea)
  const props = [
    'boxSizing',
    'width',
    'height',
    'paddingTop',
    'paddingRight',
    'paddingBottom',
    'paddingLeft',
    'borderTopWidth',
    'borderRightWidth',
    'borderBottomWidth',
    'borderLeftWidth',
    'fontFamily',
    'fontSize',
    'fontWeight',
    'fontStyle',
    'letterSpacing',
    'lineHeight',
    'textTransform',
    'textIndent',
    'textDecoration',
    'textAlign',
    'whiteSpace',
    'wordWrap',
    'overflowWrap'
  ]
  mirror.style.position = 'absolute'
  mirror.style.visibility = 'hidden'
  mirror.style.pointerEvents = 'none'
  mirror.style.whiteSpace = 'pre-wrap'
  mirror.style.wordWrap = 'break-word'
  mirror.style.overflow = 'hidden'
  mirror.style.top = '0'
  mirror.style.left = '0'
  props.forEach((prop) => {
    mirror.style.setProperty(prop, computed.getPropertyValue(prop))
  })
  mirror.textContent = textarea.value.slice(0, caret)

  const marker = document.createElement('span')
  marker.textContent = textarea.value.slice(caret, caret + 1) || '\u200b'
  mirror.appendChild(marker)
  document.body.appendChild(mirror)

  const textareaRect = textarea.getBoundingClientRect()
  const fontSize = Number.parseFloat(computed.fontSize || '14') || 14
  const parsedLineHeight = Number.parseFloat(computed.lineHeight || '')
  const lineHeight = Number.isFinite(parsedLineHeight) ? parsedLineHeight : fontSize * 1.45
  const x = textareaRect.left + marker.offsetLeft - textarea.scrollLeft
  const y = textareaRect.top + marker.offsetTop - textarea.scrollTop

  document.body.removeChild(mirror)
  return { x, y, lineHeight }
}

const updateRewriteTooltipPosition = () => {
  if (!showRewriteAssistant.value) return
  if (!rewriteSelection.text.trim()) return
  const textarea = draftInputRef.value
  if (!textarea) return

  const startPoint = getTextareaCaretPoint(textarea, rewriteSelection.start)
  const endPoint = getTextareaCaretPoint(textarea, rewriteSelection.end)
  const tooltipWidth = rewriteTooltipRef.value?.offsetWidth || 340
  const tooltipHeight = rewriteTooltipRef.value?.offsetHeight || 160
  const viewportPadding = 12
  const minX = tooltipWidth / 2 + viewportPadding
  const maxX = window.innerWidth - tooltipWidth / 2 - viewportPadding
  const rawX = (startPoint.x + endPoint.x) / 2
  const selectedTop = Math.min(startPoint.y, endPoint.y)
  const selectedBottom = Math.max(
    startPoint.y + startPoint.lineHeight,
    endPoint.y + endPoint.lineHeight
  )
  const spacing = 12
  let placement: 'top' | 'bottom' = 'top'
  let yTop = selectedTop - tooltipHeight - spacing
  if (yTop < viewportPadding) {
    placement = 'bottom'
    yTop = selectedBottom + spacing
  }
  if (placement === 'bottom' && yTop + tooltipHeight > window.innerHeight - viewportPadding) {
    placement = 'top'
    yTop = selectedTop - tooltipHeight - spacing
  }
  yTop = Math.max(viewportPadding, Math.min(window.innerHeight - tooltipHeight - viewportPadding, yTop))
  rewriteTooltipPos.x = Math.min(maxX, Math.max(minX, rawX))
  rewriteTooltipPos.y = yTop
  rewriteTooltipPlacement.value = placement
}

const updateRewriteSelectionFromEditor = () => {
  const textarea = draftInputRef.value
  if (!textarea) return
  const start = textarea.selectionStart ?? 0
  const end = textarea.selectionEnd ?? start
  const nextText = end > start ? draftText.value.slice(start, end) : ''
  const selectionChanged =
    start !== rewriteSelection.start ||
    end !== rewriteSelection.end ||
    nextText !== rewriteSelection.text

  if (!nextText.trim()) {
    clearRewriteSelection()
    return
  }

  rewriteSelection.start = start
  rewriteSelection.end = end
  rewriteSelection.text = nextText
  if (selectionChanged || !showRewriteAssistant.value) {
    showRewriteAssistant.value = true
    nextTick(() => updateRewriteTooltipPosition())
  } else {
    updateRewriteTooltipPosition()
  }
}

const closeRewriteAssistant = (_dismissed = true) => {
  showRewriteAssistant.value = false
}

const toggleRewriteMode = () => {
  rewriteMode.value = rewriteMode.value === 'expand' ? 'rewrite' : 'expand'
}

const hideMentionInfo = () => {
  mentionInfoVisible.value = false
  mentionInfoData.value = null
}

const mentionBoundaryRe = /[\s，。,.!?！？；;:：、()[\]{}<>《》「」『』"'`]/

const isMentionBoundary = (char: string) => !char || mentionBoundaryRe.test(char)

const resolveMentionAtCursor = () => {
  const textarea = draftInputRef.value
  if (!textarea) return null
  const cursor = textarea.selectionStart ?? 0
  const text = draftText.value
  for (const item of mentionCandidates.value) {
    const token = item.token
    let start = text.lastIndexOf(token, cursor)
    while (start !== -1) {
      const end = start + token.length
      const prevChar = start > 0 ? (text[start - 1] ?? '') : ''
      const nextChar = end < text.length ? (text[end] ?? '') : ''
      if (
        cursor >= start &&
        cursor <= end &&
        isMentionBoundary(prevChar) &&
        isMentionBoundary(nextChar)
      ) {
        return { hit: item as MentionItem, start, end }
      }
      start = text.lastIndexOf(token, start - 1)
    }
  }
  return null
}

const updateMentionInfoByCursor = () => {
  const textarea = draftInputRef.value
  if (!textarea) {
    hideMentionInfo()
    return
  }
  const resolved = resolveMentionAtCursor()
  if (!resolved) {
    hideMentionInfo()
    return
  }
  const point = getTextareaCaretPoint(textarea, resolved.end)
  mentionInfoData.value = resolved.hit
  mentionInfoPos.x = Math.max(18, Math.min(window.innerWidth - 18, point.x))
  mentionInfoPos.y = Math.max(16, point.y - 12)
  mentionInfoVisible.value = true
}

const handleDraftInput = (e: Event) => {
  if (pendingRewrite.value && draftText.value !== pendingRewrite.value.currentText) {
    pendingRewrite.value = null
  }
  handleMentionInput(e)
  hideMentionInfo()
  updateRewriteSelectionFromEditor()
}

const handleDraftBlur = () => {
  hideMentionInfo()
  setTimeout(() => hideMention(), 120)
}

const handleDraftKeyup = () => {
  updateRewriteSelectionFromEditor()
  updateMentionInfoByCursor()
}

const handleDraftMouseup = () => {
  updateRewriteSelectionFromEditor()
  updateMentionInfoByCursor()
}

const handleDraftClick = () => {
  updateRewriteSelectionFromEditor()
  updateMentionInfoByCursor()
}

const handleDraftContextMenu = (event: MouseEvent) => {
  event.preventDefault()
  updateRewriteSelectionFromEditor()
  updateMentionInfoByCursor()
}

const handleDraftScroll = () => {
  updateRewriteTooltipPosition()
  if (mentionInfoVisible.value) updateMentionInfoByCursor()
}

const handleSelectMention = (item: any) => {
  const start = mentionStartIndex.value
  if (start === -1) return
  insertMentionTag(item, { replaceMention: true, mentionStart: start })
  hideMention()
}

const insertMentionTag = (
  item: MentionItem | null,
  options: { replaceMention?: boolean; mentionStart?: number } = {}
) => {
  if (!draftInputRef.value || !item) return
  const textarea = draftInputRef.value
  const text = draftText.value
  const tagCore = buildMentionToken(item)
  const prevScrollTop = textarea.scrollTop
  const prevScrollLeft = textarea.scrollLeft

  let start = textarea.selectionStart ?? text.length
  let end = textarea.selectionEnd ?? start
  if (options.replaceMention && typeof options.mentionStart === 'number') {
    start = options.mentionStart
    end = textarea.selectionStart ?? start
  }
  const rightChar = text.slice(end, end + 1)
  const tag = /\s|$/.test(rightChar) ? tagCore : `${tagCore} `

  draftText.value = text.slice(0, start) + tag + text.slice(end)

  nextTick(() => {
    textarea.focus({ preventScroll: true })
    const newCursorPos = start + tag.length
    textarea.setSelectionRange(newCursorPos, newCursorPos)
    textarea.scrollTop = prevScrollTop
    textarea.scrollLeft = prevScrollLeft
    updateMentionInfoByCursor()
  })
}

const closeMention = () => {
  hideMention()
}

const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as Node
  if (languageMenuRef.value && !languageMenuRef.value.contains(target)) {
    showLanguageMenu.value = false
  }
  if (
    showRewriteAssistant.value &&
    rewriteTooltipRef.value &&
    !rewriteTooltipRef.value.contains(target) &&
    draftInputRef.value &&
    target !== draftInputRef.value
  ) {
    closeRewriteAssistant(true)
  }
  if (mentionInfoVisible.value && draftInputRef.value && target !== draftInputRef.value) {
    hideMentionInfo()
  }
}

const runNovelSkill = async (
  skill: string,
  prompt: string,
  data: Record<string, any> = {}
): Promise<string> => {
  return new Promise((resolve, reject) => {
    let settled = false
    let tokenText = ''
    let finalText = ''

    const fail = (error: unknown) => {
      if (settled) return
      settled = true
      if (error instanceof Error) reject(error)
      else reject(new Error(String(error || t('novelWorkbench.messages.emptyAiResult'))))
    }

    const success = (text: string) => {
      if (settled) return
      settled = true
      resolve(text)
    }

    aiApi.skillsStream(
      {
        projectId,
        episodeId,
        prompt,
        type: 'text',
        skill,
        data
      },
      {
        onMessage: (msg: any) => {
          const msgType = String(msg?.type || '')
          if (msgType === 'thought') {
            tokenText += String(msg?.payload || '')
            return
          }
          if (msgType === 'text_finish') {
            finalText = String(msg?.payload?.text || '')
            return
          }
          if (msgType === 'error') {
            fail(new Error(String(msg?.payload || 'AI error')))
          }
        },
        onError: (error: any) => fail(error),
        onFinish: () => {
          const merged = String(finalText || tokenText || '').trim()
          if (!merged) {
            fail(new Error(t('novelWorkbench.messages.emptyAiResult')))
            return
          }
          success(merged)
        }
      }
    ).catch((error: unknown) => fail(error))
  })
}

const parseJsonObject = (rawText: string): any | null => {
  const trimmed = String(rawText || '').trim()
  if (!trimmed) return null

  const candidates: string[] = [trimmed]
  const fenceMatch = trimmed.match(/```(?:json)?\s*([\s\S]*?)\s*```/i)
  if (fenceMatch?.[1]) candidates.push(fenceMatch[1].trim())

  const firstBrace = trimmed.indexOf('{')
  const lastBrace = trimmed.lastIndexOf('}')
  if (firstBrace !== -1 && lastBrace > firstBrace) {
    candidates.push(trimmed.slice(firstBrace, lastBrace + 1))
  }

  for (const candidate of candidates) {
    try {
      const parsed = JSON.parse(candidate)
      if (parsed && typeof parsed === 'object') return parsed
    } catch (_error) {
      continue
    }
  }
  return null
}

const normalizeSuggestions = (
  rawItems: any,
  type: 'character' | 'scene'
): SnowflakeSuggestion[] => {
  if (!Array.isArray(rawItems)) return []
  const out: SnowflakeSuggestion[] = []
  const optionMap = type === 'character' ? characterPlanMap.value : scenePlanMap.value

  for (const row of rawItems) {
    if (!row || typeof row !== 'object') continue
    const rawId = String((row as any).id || '').trim()
    if (!rawId) continue
    const id = normalizeMentionId(type, rawId)
    if (!optionMap.has(id)) continue
    const option = optionMap.get(id)
    out.push({
      id,
      name: String((row as any).name || option?.name || '').trim() || option?.name || '',
      reason: String((row as any).reason || '').trim()
    })
  }

  return out.slice(0, 12)
}

const normalizeSnowflakePlan = (raw: any): SnowflakePlan | null => {
  if (!raw || typeof raw !== 'object') return null
  const oneSentence = String(raw.one_sentence || raw.oneSentence || '').trim()
  const chapterSummary = String(raw.chapter_summary || raw.chapterSummary || '').trim()
  const majorBeatsSource = Array.isArray(raw.major_beats)
    ? raw.major_beats
    : Array.isArray(raw.majorBeats)
      ? raw.majorBeats
      : []
  const majorBeats = majorBeatsSource
    .map((item: any) => String(item || '').trim())
    .filter((item: string) => !!item)
    .slice(0, 16)

  const characterSuggestions = normalizeSuggestions(raw.character_suggestions || raw.characterSuggestions, 'character')
  const sceneSuggestions = normalizeSuggestions(raw.scene_suggestions || raw.sceneSuggestions, 'scene')

  if (!oneSentence && !chapterSummary && majorBeats.length === 0) return null
  return {
    oneSentence,
    chapterSummary,
    majorBeats,
    characterSuggestions,
    sceneSuggestions
  }
}

const ensureAiConfigReady = async () => {
  if (!novelConfig.key_id) {
    message.warning(t('novelWorkbench.messages.selectConnection'))
    throw new Error('missing key')
  }
  if (!novelConfig.model) {
    message.warning(t('novelWorkbench.messages.selectModel'))
    throw new Error('missing model')
  }
  const saved = await saveNovelConfig(true)
  if (!saved) {
    throw new Error('save failed')
  }
}

const openSnowflakeAssistant = () => {
  showSnowflakeAssistant.value = true
  nextTick(() => clampSnowflakeWindow())
}

const closeSnowflakeAssistant = () => {
  showSnowflakeAssistant.value = false
  stopSnowflakeDrag()
  stopSnowflakeResize()
  void saveNovelConfig(true)
}

const runSnowflakePlan = async () => {
  const brief = chapterBrief.value.trim()
  if (!brief) {
    message.warning(t('novelWorkbench.messages.briefRequired'))
    return
  }

  planLoading.value = true
  try {
    await ensureAiConfigReady()

    const planText = await runNovelSkill('novel-snowflake-planner', brief, {
      chapter_brief: brief,
      characters: novelCharacters.value.map((char) => ({
        id: normalizeMentionId('character', String(char.id)),
        name: char.name || '',
        role: char.role || '',
        description: char.description || ''
      })),
      scenes: novelScenes.value.map((scene) => ({
        id: normalizeMentionId('scene', String(scene.id)),
        location_name: scene.location_name || '',
        mood: scene.mood || '',
        description: scene.description || ''
      })),
      existing_draft: draftText.value,
      language: locale.value
    })

    const parsed = normalizeSnowflakePlan(parseJsonObject(planText))
    if (!parsed) {
      throw new Error(t('novelWorkbench.messages.planParseFailed'))
    }

    snowflakePlan.value = parsed
    selectedPlanCharacterIds.value = parsed.characterSuggestions
      .map((item) => item.id)
      .filter((id) => characterPlanMap.value.has(id))
    selectedPlanSceneIds.value = parsed.sceneSuggestions
      .map((item) => item.id)
      .filter((id) => scenePlanMap.value.has(id))

    if (selectedPlanCharacterIds.value.length === 0 && characterPlanOptions.value.length > 0) {
      selectedPlanCharacterIds.value = characterPlanOptions.value
        .slice(0, Math.min(3, characterPlanOptions.value.length))
        .map((item) => item.id)
    }
    if (selectedPlanSceneIds.value.length === 0 && scenePlanOptions.value.length > 0) {
      selectedPlanSceneIds.value = scenePlanOptions.value
        .slice(0, Math.min(2, scenePlanOptions.value.length))
        .map((item) => item.id)
    }

    snowflakeStatus.value = 'planned'
    await saveNovelConfig(true)
    message.success(t('novelWorkbench.messages.planReady'))
  } catch (error) {
    console.error('[NovelWorkbench] plan failed', error)
    message.error(t('novelWorkbench.messages.planFailed'))
  } finally {
    planLoading.value = false
  }
}

const confirmSnowflakePlan = async () => {
  if (!snowflakePlan.value) return
  chapterWriting.value = true
  try {
    await ensureAiConfigReady()

    const selectedCharacters = selectedPlanCharacterIds.value
      .map((id) => {
        const option = characterPlanMap.value.get(id)
        if (!option) return null
        const char = novelCharacters.value.find((row) => normalizeMentionId('character', String(row.id)) === id)
        return {
          id,
          name: option.name,
          role: char?.role || '',
          description: char?.description || ''
        }
      })
      .filter((item): item is { id: string; name: string; role: string; description: string } => item !== null)

    const selectedScenes = selectedPlanSceneIds.value
      .map((id) => {
        const option = scenePlanMap.value.get(id)
        if (!option) return null
        const scene = novelScenes.value.find((row) => normalizeMentionId('scene', String(row.id)) === id)
        return {
          id,
          location_name: option.name,
          mood: scene?.mood || '',
          description: scene?.description || ''
        }
      })
      .filter((item): item is { id: string; location_name: string; mood: string; description: string } => item !== null)

    const chapterText = await runNovelSkill('novel-chapter-writer', chapterBrief.value, {
      chapter_brief: chapterBrief.value,
      one_sentence: snowflakePlan.value.oneSentence,
      chapter_summary: snowflakePlan.value.chapterSummary,
      major_beats: snowflakePlan.value.majorBeats,
      selected_characters: selectedCharacters,
      selected_scenes: selectedScenes,
      perspective: novelConfig.perspective,
      tone: novelConfig.tone,
      length: novelConfig.length,
      target_words: clampWordCount(targetWordCount.value),
      language: locale.value
    })

    draftText.value = normalizeGeneratedMentionText(chapterText.trim())
    snowflakeStatus.value = 'confirmed'
    showSnowflakeAssistant.value = false
    await saveNovelConfig(true)
    message.success(t('novelWorkbench.messages.chapterGenerated'))
  } catch (error) {
    console.error('[NovelWorkbench] write chapter failed', error)
    message.error(t('novelWorkbench.messages.chapterGenerateFailed'))
  } finally {
    chapterWriting.value = false
  }
}

const cancelSnowflakePlan = async () => {
  snowflakeStatus.value = 'cancelled'
  showSnowflakeAssistant.value = false
  await saveNovelConfig(true)
}

const applyRewriteAssistant = async () => {
  if (!rewriteSelection.text.trim()) {
    message.warning(t('novelWorkbench.messages.noSelection'))
    return
  }

  if (pendingRewrite.value) {
    message.warning(t('novelWorkbench.messages.rewritePendingDecision'))
    return
  }

  rewriteLoading.value = true
  try {
    await ensureAiConfigReady()
    const textarea = draftInputRef.value
    const currentScrollTop = textarea?.scrollTop ?? 0
    const replaceRawText = await runNovelSkill('novel-expansion-assistant', rewriteSelection.text, {
      selected_text: rewriteSelection.text,
      instruction: rewriteInstruction.value.trim(),
      mode: rewriteMode.value,
      before_context: draftText.value.slice(Math.max(0, rewriteSelection.start - 220), rewriteSelection.start),
      after_context: draftText.value.slice(rewriteSelection.end, rewriteSelection.end + 220),
      target_words: rewriteTargetWords.value > 0 ? Math.round(rewriteTargetWords.value) : 0,
      language: locale.value
    })
    const replaceText = normalizeGeneratedMentionText(replaceRawText)

    const before = draftText.value.slice(0, rewriteSelection.start)
    const after = draftText.value.slice(rewriteSelection.end)
    const previousText = draftText.value
    const currentText = `${before}${replaceText}${after}`
    draftText.value = currentText

    const replacedStart = before.length
    const replacedEnd = replacedStart + replaceText.length
    pendingRewrite.value = {
      previousText,
      currentText,
      start: replacedStart,
      end: replacedEnd,
      scrollTop: currentScrollTop
    }

    focusEditorWithViewport(currentScrollTop, replacedStart, replacedEnd)

    closeRewriteAssistant(false)
    clearRewriteSelection()
    message.success(t('novelWorkbench.messages.rewritePreviewReady'))
  } catch (error) {
    console.error('[NovelWorkbench] rewrite failed', error)
    message.error(t('novelWorkbench.messages.rewriteFailed'))
  } finally {
    rewriteLoading.value = false
  }
}

const slugToken = (raw: unknown, fallback: string) => {
  const text = String(raw || '').trim().toLowerCase()
  const slug = text.replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '')
  return slug || fallback
}

const normalizeCharacterEntity = (raw: any, idx: number): NovelCharacter | null => {
  const name = String(raw?.name || '').trim()
  if (!name) return null
  const idText = String(raw?.id || '').trim()
  const id = idText
    ? normalizeMentionId('character', idText)
    : `char_${slugToken(name, 'character')}_${idx}`
  return {
    id,
    name,
    role: String(raw?.role || '').trim(),
    description: String(raw?.description || '').trim(),
    image_url: String(raw?.image_url || '').trim(),
    reference_image: String(raw?.reference_image || '').trim()
  }
}

const normalizeSceneEntity = (raw: any, idx: number): NovelScene | null => {
  const locationName = String(raw?.location_name || raw?.name || '').trim()
  if (!locationName) return null
  const idText = String(raw?.id || '').trim()
  const id = idText
    ? normalizeMentionId('scene', idText)
    : `scene_${slugToken(locationName, 'scene')}_${idx}`
  return {
    id,
    location_name: locationName,
    mood: String(raw?.mood || '').trim(),
    description: String(raw?.description || '').trim(),
    visual_prompt: String(raw?.visual_prompt || '').trim(),
    image_url: String(raw?.image_url || '').trim(),
    reference_image: String(raw?.reference_image || '').trim()
  }
}

const mergeCharacters = (sources: any[][]): NovelCharacter[] => {
  const out: NovelCharacter[] = []
  const picked = new Set<string>()
  for (const rows of sources) {
    if (!Array.isArray(rows)) continue
    for (const row of rows) {
      const normalized = normalizeCharacterEntity(row, out.length)
      if (!normalized) continue
      const key = normalized.id
      if (picked.has(key)) continue
      picked.add(key)
      out.push(normalized)
    }
  }
  return out
}

const mergeScenes = (sources: any[][]): NovelScene[] => {
  const out: NovelScene[] = []
  const picked = new Set<string>()
  for (const rows of sources) {
    if (!Array.isArray(rows)) continue
    for (const row of rows) {
      const normalized = normalizeSceneEntity(row, out.length)
      if (!normalized) continue
      const key = normalized.id
      if (picked.has(key)) continue
      picked.add(key)
      out.push(normalized)
    }
  }
  return out
}

const initData = async () => {
  loading.value = true
  try {
    const [pRes, eList, assets] = await Promise.all([
      projectApi.get(projectId),
      episodeApi.list(projectId),
      projectApi.getAssets(projectId).catch(() => ({ characters: [], scenes: [] }))
    ])

    const normalizedAssets = (assets as any)?.data || assets || { characters: [], scenes: [] }
    project.value = { ...pRes, assets: normalizedAssets }
    const episodeRows = Array.isArray(eList) ? (eList as any[]) : (((eList as any)?.data || []) as any[])
    const currentEp = episodeRows.find((e: any) => e.id === episodeId)
    if (!currentEp) throw new Error('Episode not found')
    episode.value = currentEp

    const saved = (currentEp.ai_config?.novel || {}) as any
    const generatedScript = (currentEp.ai_config?.generated_script || {}) as any
    const scriptCharRows = Array.isArray(generatedScript.characters) ? generatedScript.characters : []
    const scriptSceneRows = Array.isArray(generatedScript.scenes) ? generatedScript.scenes : []
    const assetCharRows = Array.isArray((normalizedAssets as any)?.characters) ? (normalizedAssets as any).characters : []
    const assetSceneRows = Array.isArray((normalizedAssets as any)?.scenes) ? (normalizedAssets as any).scenes : []

    const textConfig = (currentEp.ai_config?.text || {}) as any
    const imageConfig = (currentEp.ai_config?.image || {}) as any
    novelConfig.key_id = saved.key_id ?? textConfig.key_id ?? ''
    novelConfig.model = String(saved.model || textConfig.model || '')
    novelConfig.image_key_id = saved.image_key_id ?? imageConfig.key_id ?? saved.key_id ?? ''
    novelConfig.image_model = String(saved.image_model || imageConfig.model || '')
    if (saved.perspective) novelConfig.perspective = String(saved.perspective)
    if (saved.tone) novelConfig.tone = String(saved.tone)
    if (saved.length) novelConfig.length = String(saved.length)
    if (saved.temperature !== undefined) {
      const parsed = Number(saved.temperature)
      novelConfig.temperature = Number.isNaN(parsed) ? 0.7 : Math.max(0, Math.min(1.5, parsed))
    }

    const savedCharacters = Array.isArray(saved.characters) ? saved.characters : []
    const savedScenes = Array.isArray(saved.scenes) ? saved.scenes : []
    novelCharacters.value = mergeCharacters([savedCharacters, scriptCharRows, assetCharRows])
    novelScenes.value = mergeScenes([savedScenes, scriptSceneRows, assetSceneRows])
    draftText.value = convertPlaceholdersToMentions(String(saved.draft_text || ''))

    const snowflake = saved.snowflake || {}
    chapterBrief.value = String(snowflake.chapter_brief || '')
    targetWordCount.value = clampWordCount(snowflake.target_words ?? 1000)
    rewriteTargetWords.value = Math.max(0, Number(snowflake.rewrite_target_words || 0))
    snowflakeStatus.value = ['idle', 'planned', 'confirmed', 'cancelled'].includes(snowflake.status)
      ? snowflake.status
      : 'idle'

    const restoredPlan = normalizeSnowflakePlan(snowflake.plan)
    snowflakePlan.value = restoredPlan
    selectedPlanCharacterIds.value = Array.isArray(snowflake.selected_character_ids)
      ? snowflake.selected_character_ids.map((id: any) => normalizeMentionId('character', String(id)))
      : []
    selectedPlanSceneIds.value = Array.isArray(snowflake.selected_scene_ids)
      ? snowflake.selected_scene_ids.map((id: any) => normalizeMentionId('scene', String(id)))
      : []

    const snowflakeWindow = snowflake.window || {}
    if (Number.isFinite(Number(snowflakeWindow.x))) snowflakeWindowState.x = Number(snowflakeWindow.x)
    if (Number.isFinite(Number(snowflakeWindow.y))) snowflakeWindowState.y = Number(snowflakeWindow.y)
    if (Number.isFinite(Number(snowflakeWindow.w))) snowflakeWindowState.w = Number(snowflakeWindow.w)
    if (Number.isFinite(Number(snowflakeWindow.h))) snowflakeWindowState.h = Number(snowflakeWindow.h)
    clampSnowflakeWindow()
  } catch (error) {
    console.error('[NovelWorkbench] init failed', error)
    message.error(t('novelWorkbench.messages.loadFailed'))
    goBack()
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push({ path: '/projects', query: { id: projectId } })
}

onMounted(async () => {
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('resize', handleWindowResize)
  await Promise.all([initData(), loadApiKeys()])
  if (novelConfig.key_id) await fetchModelsForKey(novelConfig.key_id, 'text')
  if (novelConfig.image_key_id) await fetchModelsForKey(novelConfig.image_key_id, 'image')
})

onUnmounted(() => {
  window.removeEventListener('resize', handleWindowResize)
  stopSnowflakeDrag()
  stopSnowflakeResize()
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="novel-page">
    <div v-if="loading" class="novel-loading">{{ t('novelWorkbench.loading') }}</div>

    <template v-else>
      <header class="novel-topbar neu-flat">
        <div class="header-left">
          <button @click="goBack" class="icon-btn neu-flat">
            <ArrowLeft class="w-5 h-5" />
          </button>
          <div class="header-title-wrap">
            <div class="header-title">
              <BookOpen class="w-4 h-4" />
              <span>{{ episode?.title || t('novelWorkbench.chapterLabel') }}</span>
            </div>
            <p class="header-subtitle">{{ project?.name || t('novelWorkbench.title') }}</p>
          </div>
        </div>

        <div class="header-right">
          <div class="relative">
            <button
              @click.stop="showModelConfig = !showModelConfig"
              class="top-btn"
              :class="showModelConfig ? 'neu-pressed text-blue-500' : 'neu-flat hover:text-blue-500 text-gray-500'"
              :title="t('novelWorkbench.configTitle')"
            >
              <Settings2 class="w-4 h-4" />
            </button>

            <transition name="pop">
              <div v-if="showModelConfig" class="config-popover" @click.stop>
                <h3>{{ t('novelWorkbench.configTitle') }}</h3>

                <div class="config-tags">
                  <button
                    class="config-tag"
                    :class="configTag === 'text' ? 'neu-pressed text-blue-500' : 'neu-flat text-gray-500'"
                    @click="configTag = 'text'"
                  >
                    {{ t('novelWorkbench.configTags.text') }}
                  </button>
                  <button
                    class="config-tag"
                    :class="configTag === 'image' ? 'neu-pressed text-emerald-600' : 'neu-flat text-gray-500'"
                    @click="configTag = 'image'"
                  >
                    {{ t('novelWorkbench.configTags.image') }}
                  </button>
                </div>

                <label class="config-field">
                  <span class="config-label">
                    {{
                      configTag === 'text'
                        ? t('workbench.modelConfig.apiConnection')
                        : t('novelWorkbench.config.imageSource')
                    }}
                    <span v-if="loadingKeys">{{ t('workbench.modelConfig.loading') }}</span>
                  </span>
                  <NeuSelect
                    v-model="activeConfigKey"
                    :options="availableKeys"
                    :placeholder="t('workbench.modelConfig.selectConnection')"
                    size="mini"
                  />
                </label>

                <label class="config-field">
                  <span class="config-label">
                    {{
                      configTag === 'text'
                        ? t('workbench.modelConfig.targetModel')
                        : t('novelWorkbench.config.imageModel')
                    }}
                    <span v-if="fetchingModels">{{ t('workbench.modelConfig.fetching') }}</span>
                  </span>
                  <NeuSelect
                    v-model="activeConfigModel"
                    :options="activeModelOptions"
                    :disabled="!activeConfigKey || fetchingModels"
                    :placeholder="t('workbench.modelConfig.autoDefault')"
                    size="mini"
                  />
                  <div v-if="showActiveManualModelInput" class="manual-model">
                    <input
                      v-model="activeConfigModel"
                      class="config-input"
                      :placeholder="t('workbench.modelConfig.manualModelPlaceholder')"
                    />
                    <p>{{ t('workbench.modelConfig.manualModelHint') }}</p>
                  </div>
                </label>

                <label v-if="configTag === 'text'" class="config-field">
                  <span>{{ t('novelWorkbench.config.perspective') }}</span>
                  <select v-model="novelConfig.perspective" class="config-input">
                    <option value="first">{{ t('novelWorkbench.perspectives.first') }}</option>
                    <option value="third">{{ t('novelWorkbench.perspectives.third') }}</option>
                    <option value="omniscient">{{ t('novelWorkbench.perspectives.omniscient') }}</option>
                  </select>
                </label>

                <label v-if="configTag === 'text'" class="config-field">
                  <span>{{ t('novelWorkbench.config.tone') }}</span>
                  <select v-model="novelConfig.tone" class="config-input">
                    <option value="cinematic">{{ t('novelWorkbench.tones.cinematic') }}</option>
                    <option value="lyrical">{{ t('novelWorkbench.tones.lyrical') }}</option>
                    <option value="realistic">{{ t('novelWorkbench.tones.realistic') }}</option>
                  </select>
                </label>

                <label v-if="configTag === 'text'" class="config-field">
                  <span>{{ t('novelWorkbench.config.length') }}</span>
                  <select v-model="novelConfig.length" class="config-input">
                    <option value="short">{{ t('novelWorkbench.lengths.short') }}</option>
                    <option value="medium">{{ t('novelWorkbench.lengths.medium') }}</option>
                    <option value="long">{{ t('novelWorkbench.lengths.long') }}</option>
                  </select>
                </label>

                <label v-if="configTag === 'text'" class="config-field">
                  <span>{{ t('novelWorkbench.assistant.wordCountLabel') }}</span>
                  <input
                    v-model.number="targetWordCount"
                    type="number"
                    min="200"
                    max="12000"
                    step="50"
                    class="config-input"
                  />
                </label>

                <label v-if="configTag === 'text'" class="config-field">
                  <span>{{ t('novelWorkbench.config.temperature') }}</span>
                  <input
                    v-model.number="novelConfig.temperature"
                    type="number"
                    step="0.1"
                    min="0"
                    max="1.5"
                    class="config-input"
                  />
                </label>

                <NeuButton
                  size="sm"
                  class="w-full mt-2 text-xs px-3 py-1.5 rounded-xl"
                  @click="saveNovelConfig(false)"
                >
                  <Save class="w-4 h-4 mr-1" />
                  {{ t('novelWorkbench.save') }}
                </NeuButton>
              </div>
            </transition>
          </div>

          <button
            @click.stop="openSnowflakeAssistant"
            class="top-btn"
            :class="showSnowflakeAssistant ? 'neu-pressed text-amber-600' : 'neu-flat hover:text-amber-500 text-gray-500'"
            :title="t('novelWorkbench.assistant.title')"
          >
            <WandSparkles class="w-4 h-4" />
          </button>

          <div class="relative" ref="languageMenuRef">
            <button
              @click.stop="showLanguageMenu = !showLanguageMenu"
              class="top-btn"
              :class="showLanguageMenu ? 'neu-pressed text-emerald-600' : 'neu-flat hover:text-emerald-500 text-gray-500'"
            >
              <Languages class="w-4 h-4" />
            </button>
            <transition name="pop">
              <div v-if="showLanguageMenu" class="absolute top-full right-0 mt-2 z-50 rounded-xl" @click.stop>
                <LanguageSwitcher />
              </div>
            </transition>
          </div>
        </div>
      </header>

      <main class="novel-main">
        <section class="journal-shell neu-flat-sm">
          <transition name="pop">
            <div v-if="pendingRewrite" class="rewrite-preview-bar neu-flat-sm" @click.stop>
              <span>{{ t('novelWorkbench.rewrite.previewReady') }}</span>
              <div class="rewrite-preview-actions">
                <NeuButton
                  size="xs"
                  class="text-xs px-3 py-1.5 rounded-xl"
                  @click="cancelPendingRewritePreview"
                >
                  {{ t('novelWorkbench.rewrite.undoAction') }}
                </NeuButton>
                <NeuButton
                  size="xs"
                  class="text-xs px-3 py-1.5 rounded-xl"
                  variant="primary"
                  @click="confirmPendingRewritePreview"
                >
                  {{ t('novelWorkbench.rewrite.confirmAction') }}
                </NeuButton>
              </div>
            </div>
          </transition>
          <div class="journal-paper">
            <textarea
              ref="draftInputRef"
              v-model="draftText"
              class="journal-textarea"
              :class="{ 'is-rewrite-preview': !!pendingRewrite }"
              :placeholder="draftPlaceholder"
              @input="handleDraftInput"
              @blur="handleDraftBlur"
              @keyup="handleDraftKeyup"
              @mouseup="handleDraftMouseup"
              @click="handleDraftClick"
              @contextmenu="handleDraftContextMenu"
              @scroll="handleDraftScroll"
            />
          </div>
        </section>
        <aside
          class="reference-shell neu-flat reference-list-shell reference-pane"
          :class="referenceEntityTab === 'characters' ? 'character-pane' : 'scene-pane'"
        >
          <div class="reference-tabs-wrap">
            <button
              v-for="tab in referenceEntityTabs"
              :key="tab.id"
              class="reference-tab-btn"
              :class="referenceEntityTab === tab.id ? 'neu-pressed-sm text-blue-500' : 'neu-flat-sm text-gray-500 hover:text-gray-600'"
              @click="referenceEntityTab = tab.id"
            >
              <component :is="tab.icon" class="w-3.5 h-3.5" />
              {{ tab.label }}
            </button>
          </div>

          <div class="reference-content custom-scroll">
            <ScriptCharacters
              v-if="referenceEntityTab === 'characters'"
              :characters="novelCharacters"
              :generating-items="generatingItems"
              :enable-mention-drag="false"
              @delete="(idx) => handleDeleteEntity('character', idx)"
              @preview="(idx) => openPreview(novelCharacters, idx)"
              @add="handleAddCharacter"
              @generate="handleCharacterGenerate"
              @upload-reference="(item, _idx, file) => handleUploadReference('character', item, file)"
            />
            <ScriptScenes
              v-else
              :scenes="novelScenes"
              :generating-items="generatingItems"
              :enable-mention-drag="false"
              @delete="(idx) => handleDeleteEntity('scene', idx)"
              @edit="handleSceneEdit"
              @preview="(idx) => openPreview(novelScenes, idx)"
              @add="handleAddScene"
              @generate="handleSceneGenerate"
              @upload-reference="(item, _idx, file) => handleUploadReference('scene', item, file)"
            />
          </div>
        </aside>
      </main>
    </template>

    <NeuMentionSelector
      :visible="isMentionVisible"
      :x="mentionX"
      :y="mentionY + 20"
      :filter-text="mentionQuery"
      :items="mentionItems"
      @select="handleSelectMention"
      @close="closeMention"
    />

    <Teleport to="body">
      <transition name="pop">
        <div
          v-if="mentionInfoVisible && mentionInfoData"
          class="mention-inline-tooltip fixed z-[99] rounded-xl p-3 pointer-events-none"
          :style="{ left: `${mentionInfoPos.x}px`, top: `${mentionInfoPos.y}px`, transform: 'translate(-50%, -100%)' }"
        >
          <div class="mention-inline-head">
            <div class="mention-inline-avatar" :class="mentionInfoData.type === 'character' ? 'is-character' : 'is-scene'">
              <img v-if="mentionInfoData.image_url" :src="mentionInfoData.image_url" class="w-full h-full object-cover" />
              <UserRound v-else-if="mentionInfoData.type === 'character'" class="w-4 h-4" />
              <MapPin v-else class="w-4 h-4" />
            </div>
            <div class="min-w-0">
              <div class="mention-inline-name">@{{ mentionInfoData.name }}</div>
              <div class="mention-inline-sub">
                {{ mentionInfoData.type === 'character'
                  ? (mentionInfoData.role || t('workbench.scriptEditor.tabs.characters'))
                  : (mentionInfoData.mood || t('workbench.scriptEditor.tabs.scenes')) }}
              </div>
            </div>
          </div>
          <p class="mention-inline-desc">
            {{ mentionInfoData.description || t('novelWorkbench.detail.empty') }}
          </p>
        </div>
      </transition>
    </Teleport>

    <NeuConfirm />

    <BookPreview
      :visible="previewVisible"
      :items="previewList"
      :initial-index="previewIndex"
      :generating-items="generatingItems"
      :all-characters="novelCharacters"
      :all-scenes="novelScenes"
      @close="previewVisible = false"
      @regenerate="handlePreviewRegenerate"
      @update-item="handlePreviewUpdate"
    />

    <Teleport to="body">
      <CharacterCreateModal
        :visible="showCharModal"
        @close="showCharModal = false"
        @confirm="handleCharConfirm"
      />

      <transition name="pop">
        <div
          v-if="showSnowflakeAssistant"
          class="assistant-panel fixed z-[96] bg-[#E0E5EC] rounded-[1.2rem] border border-white/40 shadow-2xl overflow-hidden flex flex-col"
          :style="{
            left: `${snowflakeWindowState.x}px`,
            top: `${snowflakeWindowState.y}px`,
            width: `${snowflakeWindowState.w}px`,
            height: `${snowflakeWindowState.h}px`
          }"
        >
          <div class="assistant-panel-head" @mousedown="startSnowflakeDrag">
            <div class="assistant-panel-title">
              <WandSparkles class="w-3.5 h-3.5 text-amber-500" />
              <h4>{{ t('novelWorkbench.assistant.title') }}</h4>
            </div>
            <button class="modal-close neu-flat" @click.stop="closeSnowflakeAssistant">
              <X class="w-4 h-4" />
            </button>
          </div>

          <div class="assistant-panel-body custom-scroll">
            <div class="assistant-setup">
              <label class="modal-field assistant-field">
                <span>{{ t('novelWorkbench.assistant.briefLabel') }}</span>
                <textarea
                  v-model="chapterBrief"
                  class="config-input assistant-textarea"
                  :placeholder="t('novelWorkbench.assistant.briefPlaceholder')"
                />
              </label>

              <label class="modal-field assistant-field">
                <span>{{ t('novelWorkbench.assistant.wordCountLabel') }}</span>
                <input
                  v-model.number="targetWordCount"
                  type="number"
                  min="200"
                  max="12000"
                  step="50"
                  class="config-input"
                />
              </label>

              <div v-if="!snowflakePlan" class="assistant-actions">
                <NeuButton
                  size="xs"
                  class="text-xs px-3 py-1.5 rounded-xl"
                  :disabled="planLoading || chapterWriting"
                  @click="runSnowflakePlan"
                >
                  {{ planLoading ? t('novelWorkbench.assistant.planning') : t('novelWorkbench.assistant.planAction') }}
                </NeuButton>
              </div>
            </div>

            <div v-if="snowflakePlan" class="assistant-plan">
              <div class="assistant-plan-head">
                <strong>{{ t('novelWorkbench.assistant.planAction') }}</strong>
                <span>{{ t('novelWorkbench.assistant.beatsLabel') }}: {{ snowflakePlan.majorBeats.length }}</span>
              </div>
              <div class="assistant-section">
                <p class="assistant-label">{{ t('novelWorkbench.assistant.oneSentenceLabel') }}</p>
                <p class="assistant-value">{{ snowflakePlan.oneSentence || t('novelWorkbench.detail.empty') }}</p>
              </div>
              <div class="assistant-section">
                <p class="assistant-label">{{ t('novelWorkbench.assistant.summaryLabel') }}</p>
                <p class="assistant-value">{{ snowflakePlan.chapterSummary || t('novelWorkbench.detail.empty') }}</p>
              </div>
              <div class="assistant-section" v-if="snowflakePlan.majorBeats.length > 0">
                <p class="assistant-label">{{ t('novelWorkbench.assistant.beatsLabel') }}</p>
                <ol class="assistant-beats">
                  <li v-for="(beat, idx) in snowflakePlan.majorBeats" :key="`beat-${idx}`">{{ beat }}</li>
                </ol>
              </div>
              <div class="assistant-grid">
                <div class="assistant-column">
                  <p class="assistant-label">{{ t('novelWorkbench.assistant.charactersLabel') }}</p>
                  <p v-if="snowflakePlan.characterSuggestions.length > 0" class="assistant-tip">
                    {{ t('novelWorkbench.assistant.suggestedCharacters', { names: snowflakePlan.characterSuggestions.map((item) => item.name).join('、') }) }}
                  </p>
                  <div v-if="characterPlanOptions.length === 0" class="assistant-empty">{{ t('projects.archive.noCharacters') }}</div>
                  <label
                    v-for="item in characterPlanOptions"
                    :key="`plan-char-${item.id}`"
                    class="assistant-option"
                  >
                    <input v-model="selectedPlanCharacterIds" type="checkbox" :value="item.id" />
                    <span>{{ item.name }}</span>
                    <small v-if="item.subtitle">{{ item.subtitle }}</small>
                  </label>
                </div>
                <div class="assistant-column">
                  <p class="assistant-label">{{ t('novelWorkbench.assistant.scenesLabel') }}</p>
                  <p v-if="snowflakePlan.sceneSuggestions.length > 0" class="assistant-tip">
                    {{ t('novelWorkbench.assistant.suggestedScenes', { names: snowflakePlan.sceneSuggestions.map((item) => item.name).join('、') }) }}
                  </p>
                  <div v-if="scenePlanOptions.length === 0" class="assistant-empty">{{ t('projects.archive.noScenes') }}</div>
                  <label
                    v-for="item in scenePlanOptions"
                    :key="`plan-scene-${item.id}`"
                    class="assistant-option"
                  >
                    <input v-model="selectedPlanSceneIds" type="checkbox" :value="item.id" />
                    <span>{{ item.name }}</span>
                    <small v-if="item.subtitle">{{ item.subtitle }}</small>
                  </label>
                </div>
              </div>
            </div>

            <div v-if="snowflakePlan && !planLoading && !chapterWriting" class="modal-foot assistant-foot">
              <NeuButton
                size="xs"
                class="text-xs px-3 py-1.5 rounded-xl"
                :disabled="planLoading || chapterWriting"
                @click="cancelSnowflakePlan"
              >
                {{ t('novelWorkbench.assistant.cancelAction') }}
              </NeuButton>
              <NeuButton
                size="xs"
                class="text-xs px-3 py-1.5 rounded-xl"
                :disabled="planLoading || chapterWriting"
                @click="runSnowflakePlan"
              >
                {{ t('novelWorkbench.assistant.replanAction') }}
              </NeuButton>
              <NeuButton
                size="xs"
                class="text-xs px-3 py-1.5 rounded-xl"
                variant="primary"
                :disabled="!snowflakePlan || planLoading || chapterWriting"
                @click="confirmSnowflakePlan"
              >
                {{ chapterWriting ? t('novelWorkbench.assistant.writing') : t('novelWorkbench.assistant.confirmAction') }}
              </NeuButton>
            </div>
          </div>

          <div class="assistant-resize-handle" @mousedown="startSnowflakeResize"></div>

          <div v-if="planLoading || chapterWriting" class="assistant-loading-overlay">
            <div class="assistant-loading-card neu-pressed">
              <p class="assistant-loading-text">
                {{ planLoading ? t('novelWorkbench.assistant.planning') : t('novelWorkbench.assistant.writing') }}
              </p>
              <div class="assistant-loading-track">
                <div class="assistant-loading-bar"></div>
              </div>
            </div>
          </div>
        </div>
      </transition>
      <transition name="pop">
        <div
          v-if="showRewriteAssistant && rewriteSelection.text.trim()"
          ref="rewriteTooltipRef"
          class="rewrite-tooltip neu-flat"
          :class="rewriteTooltipPlacement === 'bottom' ? 'is-bottom' : 'is-top'"
          :style="{ left: `${rewriteTooltipPos.x}px`, top: `${rewriteTooltipPos.y}px` }"
          @mousedown.stop
          @click.stop
        >
          <div class="rewrite-toolbar">
            <div class="rewrite-top-row">
              <button
                class="rewrite-mode-toggle"
                :class="rewriteMode === 'expand' ? 'neu-flat text-blue-600' : 'neu-flat text-emerald-600'"
                @click="toggleRewriteMode"
              >
                {{ rewriteMode === 'expand' ? t('novelWorkbench.rewrite.modeExpand') : t('novelWorkbench.rewrite.modeRewrite') }}
              </button>

              <label class="rewrite-words-box">
                <span class="rewrite-words-hint">{{ t('novelWorkbench.rewrite.targetWordsHint') }}</span>
                <input
                  v-model.number="rewriteTargetWords"
                  type="number"
                  min="0"
                  max="6000"
                  step="50"
                  class="config-input rewrite-toolbar-words"
                  :placeholder="t('novelWorkbench.rewrite.targetWordsPlaceholder')"
                  @keydown.enter.prevent="applyRewriteAssistant"
                  @keydown.esc.stop.prevent="closeRewriteAssistant(true)"
                />
              </label>
            </div>

            <textarea
              v-model="rewriteInstruction"
              class="config-input rewrite-toolbar-textarea"
              :placeholder="t('novelWorkbench.rewrite.instructionPlaceholder')"
              @keydown.ctrl.enter.prevent="applyRewriteAssistant"
              @keydown.meta.enter.prevent="applyRewriteAssistant"
              @keydown.esc.stop.prevent="closeRewriteAssistant(true)"
            />

            <div class="rewrite-actions-row">
              <NeuButton
                size="xs"
                class="text-xs px-3 py-1.5 rounded-xl rewrite-run-btn"
                variant="primary"
                :disabled="rewriteLoading"
                :title="rewriteActionLabel"
                @click="applyRewriteAssistant"
              >
                {{ rewriteLoading ? t('novelWorkbench.rewrite.processing') : rewriteActionLabel }}
              </NeuButton>
            </div>
          </div>
        </div>
      </transition>

    </Teleport>
  </div>
</template>

<style scoped>
.novel-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  background: #e0e5ec;
  color: #4a5568;
  overflow: hidden;
}

.novel-loading {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #64748b;
}

.novel-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-radius: 1.5rem;
  background: #e0e5ec;
  position: relative;
  z-index: 20;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.875rem;
}

.icon-btn {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  transition: all 0.2s ease;
}

.icon-btn:hover {
  color: #3b82f6;
}

.header-title-wrap {
  display: flex;
  flex-direction: column;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 14px;
  font-weight: 700;
  color: #4b5563;
}

.header-subtitle {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.top-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.4rem;
  height: 2.4rem;
  border-radius: 0.75rem;
  transition: all 0.2s ease;
}

.config-popover {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  width: 320px;
  padding: 0.9rem;
  border-radius: 1rem;
  background: #e0e5ec;
  box-shadow: 12px 12px 24px rgba(163, 177, 198, 0.65), -12px -12px 24px rgba(255, 255, 255, 0.75);
  z-index: 70;
}

.config-popover h3 {
  font-size: 13px;
  font-weight: 800;
  color: #4b5563;
  margin-bottom: 0.6rem;
}

.config-tags {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
}

.config-tag {
  flex: 1;
  min-height: 32px;
  border: 1px solid transparent;
  border-radius: 0.7rem;
  font-size: 11px;
  line-height: 1;
  font-weight: 700;
  padding: 6px 10px;
  transition: all 0.2s ease;
}

.config-field {
  display: grid;
  gap: 6px;
  margin-bottom: 10px;
}

.config-label,
.config-field span {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #6b7280;
}

.config-input {
  width: 100%;
  border: none;
  border-radius: 0.85rem;
  padding: 8px 10px;
  font-size: 12px;
  color: #4b5563;
  background: #e0e5ec;
  box-shadow: inset 3px 3px 6px rgba(163, 177, 198, 0.65), inset -3px -3px 6px rgba(255, 255, 255, 0.9);
  outline: none;
}

.manual-model {
  display: grid;
  gap: 4px;
}

.manual-model p {
  margin: 0;
  font-size: 10px;
  color: #6b7280;
}

.novel-main {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  grid-template-areas: "editor sidebar";
  gap: 1rem;
}

.journal-shell {
  grid-area: editor;
  position: relative;
  flex: 1;
  min-width: 0;
  border-radius: 2rem;
  /* padding: 1rem; */
  display: flex;
  flex-direction: column;
  gap: 0;
  background: #e0e5ec;
}

.journal-paper {
  --paper-line: 30px;
  flex: 1;
  min-height: 0;
  border-radius: 1.4rem;
  padding: 1rem 0;
  background: #f9fafb;
  display: flex;
  flex-direction: column;
}

.journal-textarea {
  flex: 1;
  min-height: 0;
  width: 100%;
  resize: vertical;
  border: none;
  outline: none;
  border-radius: 0.9rem;
  padding: 0 12px 0 44px;
  background:
    linear-gradient(90deg, transparent 34px, rgba(248, 113, 113, 0.28) 35px, transparent 36px),
    repeating-linear-gradient(
      transparent,
      transparent calc(var(--paper-line) - 1px),
      rgba(122, 163, 220, 0.35) calc(var(--paper-line) - 1px),
      rgba(122, 163, 220, 0.35) var(--paper-line)
    ),
    #f9fafb;
  background-attachment: local;
  color: #334155;
  font-size: 14px;
  line-height: var(--paper-line);
  white-space: pre-wrap;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.journal-textarea::-webkit-scrollbar {
  display: none;
}

.journal-textarea::placeholder {
  color: #94a3b8;
  white-space: pre-line;
}

.journal-textarea.is-rewrite-preview::selection {
  background: rgba(34, 197, 94, 0.35);
  color: #14532d;
}

.rewrite-preview-bar {
  position: absolute;
  top: 0.85rem;
  right: 0.95rem;
  z-index: 14;
  border-radius: 0.9rem;
  padding: 8px 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(224, 229, 236, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 6px 6px 14px rgba(148, 163, 184, 0.26), -4px -4px 10px rgba(255, 255, 255, 0.62);
}

.rewrite-preview-bar > span {
  font-size: 11px;
  font-weight: 700;
  color: #166534;
  white-space: nowrap;
}

.rewrite-preview-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.reference-shell {
  grid-area: sidebar;
  width: 100%;
  min-width: 0;
  min-height: 0;
  border-radius: 2rem;
  background: #e0e5ec;
  display: flex;
  flex-direction: column;
  padding: 0.95rem;
}

.reference-list-shell {
  padding: 16px 0;
}

.reference-pane {
  gap: 0.5rem;
}

.reference-tabs-wrap {
  display: flex;
  gap: 6px;
  padding: 4px 24px;
  border-radius: 0.9rem;
}

.reference-tab-btn {
  flex: 1;
  min-height: 32px;
  border-radius: 0.72rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 800;
  transition: all 0.2s ease;
}

.reference-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px 24px;
}

.character-pane :deep(.grid),
.scene-pane :deep(.grid) {
  grid-template-columns: minmax(0, 1fr) !important;
  gap: 0.75rem;
}

.character-pane :deep(.grid > div),
.scene-pane :deep(.grid > div) {
  min-height: 0;
  width: 100%;
}

.character-pane :deep(.grid > button[class*='border-dashed']),
.scene-pane :deep(.grid > button[class*='border-dashed']) {
  min-height: 132px !important;
}

.character-pane :deep(.mt-auto .flex.gap-2 > *),
.scene-pane :deep(.mt-auto .flex.gap-2 > *) {
  flex: 1 1 0;
  min-height: 30px;
  padding: 0.35rem 0.4rem !important;
}

.character-pane :deep(.mt-auto .flex.gap-2 > * svg),
.scene-pane :deep(.mt-auto .flex.gap-2 > * svg) {
  width: 0.85rem;
  height: 0.85rem;
}

.reference-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.reference-tag-wrap {
  min-width: 0;
}

.reference-tag {
  height: 1.95rem;
  border-radius: 0.7rem;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 0.6rem;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.01em;
}

.reference-tag small {
  font-size: 10px;
  color: #64748b;
}

.mini-icon-btn {
  width: 1.9rem;
  height: 1.9rem;
  border-radius: 0.65rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  transition: all 0.2s ease;
}

.mini-icon-btn:hover {
  color: #2563eb;
}

.sticky-grid {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-auto-rows: 170px;
  align-content: start;
  gap: 10px;
  padding-top: 4px;
  padding-right: 4px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.sticky-grid::-webkit-scrollbar {
  display: none;
}

.photo-empty {
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 12px;
}

.section-empty {
  min-height: 70px;
}

.sticky-note {
  height: 100%;
  position: relative;
  border-radius: 0.95rem;
  background: var(--note-bg, #fef08a);
  box-shadow: 0 8px 14px rgba(30, 41, 59, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.62);
  overflow: hidden;
  cursor: grab;
  transform: rotate(var(--note-rot, 0deg)) translateY(var(--note-offset, 0px));
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.sticky-note:hover {
  transform: rotate(var(--note-rot, 0deg)) translateY(calc(var(--note-offset, 0px) - 2px)) scale(1.01);
  box-shadow: 0 12px 18px rgba(30, 41, 59, 0.22);
}

.sticky-pin {
  position: absolute;
  width: 11px;
  height: 11px;
  left: calc(50% - 6px);
  top: 6px;
  border-radius: 999px;
  background: #475569;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  z-index: 1;
}

.photo-image-wrap {
  height: 78px;
}

.sticky-image {
  margin: 12px 8px 0;
  border-radius: 0.7rem;
  background: rgba(255, 255, 255, 0.55);
}

.photo-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
}

.photo-meta {
  padding: 8px;
  display: grid;
  gap: 4px;
}

.photo-tags {
  display: flex;
  align-items: center;
  gap: 4px;
}

.photo-tag,
.photo-source {
  font-size: 9px;
  border-radius: 999px;
  padding: 0 7px;
  color: rgba(15, 23, 42, 0.7);
  background: rgba(255, 255, 255, 0.55);
}

.photo-title {
  margin-top: 4px;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}

.photo-subtitle {
  font-size: 11px;
  color: #475569;
  line-height: 1.25;
  min-height: 0;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.photo-actions {
  margin-top: 2px;
  display: grid;
  gap: 4px;
}

.photo-action-btn {
  width: 100%;
  height: 24px;
  border-radius: 0.55rem;
  font-size: 10px;
  font-weight: 700;
  color: #475569;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.photo-action-btn:disabled {
  opacity: 0.9;
  cursor: default;
}

.custom-scroll::-webkit-scrollbar {
  display: none;
}

.custom-scroll::-webkit-scrollbar-thumb {
  display: none;
}

.custom-scroll {
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(4px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-card,
.detail-card {
  width: min(540px, 92vw);
  border-radius: 1.25rem;
  background: #e0e5ec;
  padding: 14px;
}

.assistant-panel {
  min-width: 420px;
  min-height: 360px;
  background: linear-gradient(160deg, #e8edf4 0%, #dde4ee 55%, #d5deea 100%);
  box-shadow: 18px 18px 36px rgba(148, 163, 184, 0.35), -12px -12px 28px rgba(255, 255, 255, 0.75);
}

.assistant-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 11px 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.24);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0.35));
  cursor: move;
  user-select: none;
}

.assistant-panel-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.assistant-panel-title h4 {
  font-size: 12px;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: #334155;
  font-weight: 800;
}

.assistant-panel-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 14px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.assistant-panel-body::-webkit-scrollbar {
  display: none;
}

.assistant-resize-handle {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 20px;
  height: 20px;
  cursor: nwse-resize;
  z-index: 2;
}

.rewrite-card {
  width: min(680px, 92vw);
  border-radius: 1.25rem;
  background: #e0e5ec;
  padding: 14px;
}

.detail-card {
  width: min(620px, 92vw);
}

.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.modal-head h4 {
  font-size: 16px;
  font-weight: 800;
  color: #475569;
}

.modal-close {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
}

.modal-field {
  display: grid;
  gap: 6px;
  margin-top: 8px;
}

.modal-field span {
  font-size: 12px;
  color: #6b7280;
}

.modal-textarea {
  min-height: 88px;
  resize: vertical;
}

.assistant-textarea {
  min-height: 112px;
  resize: vertical;
}

.assistant-setup {
  border-radius: 14px;
  padding: 0 12px;
}

.assistant-field {
  margin-top: 0;
  margin-bottom: 12px;
}

.assistant-actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

.assistant-actions :deep(button) {
  min-width: 120px;
  min-height: 32px;
}

.assistant-loading-overlay {
  position: absolute;
  inset: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(224, 229, 236, 0.8);
  backdrop-filter: blur(2px);
}

.assistant-loading-card {
  width: min(340px, calc(100% - 36px));
  border-radius: 12px;
  padding: 12px 14px;
  display: grid;
  gap: 10px;
}

.assistant-loading-text {
  margin: 0;
  color: #475569;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.01em;
}

.assistant-loading-track {
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(148, 163, 184, 0.25);
  box-shadow: inset 2px 2px 6px rgba(148, 163, 184, 0.22), inset -2px -2px 6px rgba(255, 255, 255, 0.68);
}

.assistant-loading-bar {
  width: 42%;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #60a5fa, #38bdf8, #60a5fa);
  animation: assistant-progress-indeterminate 1.15s ease-in-out infinite;
}

@keyframes assistant-progress-indeterminate {
  0% {
    transform: translateX(-120%);
  }
  100% {
    transform: translateX(240%);
  }
}

.assistant-plan {
  margin-top: 12px;
  padding: 12px;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.38);
  border: 1px solid rgba(255, 255, 255, 0.58);
}

.assistant-plan-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  color: #475569;
}

.assistant-plan-head strong {
  font-size: 12px;
  font-weight: 800;
}

.assistant-plan-head span {
  font-size: 11px;
  color: #64748b;
}

.assistant-section {
  margin-top: 8px;
  border-radius: 12px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.34);
}

.assistant-label {
  margin: 0;
  font-size: 11px;
  color: #64748b;
  font-weight: 700;
}

.assistant-value {
  margin: 4px 0 0;
  font-size: 13px;
  color: #334155;
  line-height: 1.55;
}

.assistant-beats {
  margin: 6px 0 0;
  padding-left: 18px;
  display: grid;
  gap: 4px;
  color: #334155;
  font-size: 12px;
}

.assistant-grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.assistant-column {
  border-radius: 0.9rem;
  padding: 9px;
  background: rgba(255, 255, 255, 0.52);
  box-shadow: inset 2px 2px 6px rgba(148, 163, 184, 0.18), inset -2px -2px 8px rgba(255, 255, 255, 0.6);
}

.assistant-option {
  margin-top: 6px;
  display: grid;
  grid-template-columns: 14px minmax(0, 1fr);
  align-items: start;
  column-gap: 8px;
  font-size: 12px;
  color: #334155;
  border-radius: 10px;
  padding: 6px 8px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.16);
  transition: all 0.2s ease;
}

.assistant-option:hover {
  background: rgba(255, 255, 255, 0.9);
  border-color: rgba(59, 130, 246, 0.28);
}

.assistant-option input {
  margin-top: 2px;
  accent-color: #3b82f6;
}

.assistant-option small {
  grid-column: 2;
  color: #64748b;
  line-height: 1.3;
}

.assistant-empty {
  margin-top: 8px;
  color: #94a3b8;
  font-size: 12px;
}

.assistant-tip {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 11px;
  line-height: 1.4;
}

.assistant-foot {
  margin-top: 14px;
}

.rewrite-tooltip {
  position: fixed;
  z-index: 98;
  transform: translateX(-50%);
  width: min(520px, calc(100vw - 24px));
  border-radius: 0.95rem;
  padding: 10px;
  display: block;
  background: #e0e5ec;
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow: 12px 12px 24px rgba(148, 163, 184, 0.32), -8px -8px 16px rgba(255, 255, 255, 0.72);
}

.rewrite-tooltip.is-top::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -8px;
  width: 14px;
  height: 14px;
  transform: translateX(-50%) rotate(45deg);
  background: #e0e5ec;
  border-right: 1px solid rgba(255, 255, 255, 0.42);
  border-bottom: 1px solid rgba(255, 255, 255, 0.42);
}

.rewrite-tooltip.is-bottom::before {
  content: '';
  position: absolute;
  left: 50%;
  top: -8px;
  width: 14px;
  height: 14px;
  transform: translateX(-50%) rotate(45deg);
  background: #e0e5ec;
  border-left: 1px solid rgba(255, 255, 255, 0.42);
  border-top: 1px solid rgba(255, 255, 255, 0.42);
}

.mention-inline-tooltip {
  width: min(280px, calc(100vw - 24px));
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.65);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.2);
}

.mention-inline-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.mention-inline-avatar {
  width: 26px;
  height: 26px;
  border-radius: 999px;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.65);
}

.mention-inline-avatar.is-character {
  color: #2563eb;
  background: rgba(191, 219, 254, 0.6);
}

.mention-inline-avatar.is-scene {
  color: #ea580c;
  background: rgba(254, 215, 170, 0.65);
}

.mention-inline-name {
  font-size: 12px;
  line-height: 1.2;
  font-weight: 800;
  color: #334155;
}

.mention-inline-sub {
  font-size: 10px;
  line-height: 1.2;
  color: #64748b;
}

.mention-inline-desc {
  margin: 0;
  font-size: 11px;
  line-height: 1.45;
  color: #475569;
}

.rewrite-toolbar {
  display: grid;
  gap: 8px;
}

.rewrite-top-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.rewrite-mode-toggle {
  min-width: 72px;
  min-height: 32px;
  border-radius: 0.72rem;
  font-size: 11px;
  font-weight: 700;
  padding: 6px 8px;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.rewrite-words-box {
  flex: 1;
  min-width: 0;
  display: grid;
  gap: 4px;
}

.rewrite-words-hint {
  font-size: 10px;
  color: #64748b;
  line-height: 1.2;
}

.rewrite-toolbar-words {
  width: 100%;
  min-height: 32px;
  font-size: 12px;
  padding: 7px 8px;
}

.rewrite-toolbar-textarea {
  width: 100%;
  min-height: 78px;
  font-size: 12px;
  line-height: 1.45;
  padding: 8px 10px;
  resize: vertical;
  white-space: pre-wrap;
}

.rewrite-actions-row {
  display: flex;
  justify-content: flex-end;
}

.rewrite-run-btn {
  min-width: 112px;
  min-height: 32px;
}

.modal-foot {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}

.detail-image-wrap {
  height: 220px;
  border-radius: 12px;
  overflow: hidden;
  background: #e0e5ec;
}

.detail-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.detail-image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
}

.detail-meta {
  margin-top: 12px;
  display: grid;
  gap: 6px;
  font-size: 13px;
  color: #475569;
}

.detail-meta p {
  margin: 0;
}

.detail-meta span {
  font-weight: 700;
}

.detail-meta code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  background: rgba(255, 255, 255, 0.55);
  padding: 1px 6px;
  border-radius: 6px;
}

.detail-desc {
  line-height: 1.55;
}

.pop-enter-active,
.pop-leave-active {
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  transform-origin: top right;
}

.pop-enter-from,
.pop-leave-to {
  opacity: 0;
  transform: scale(0.94);
}

@media (max-width: 1200px) {
  .novel-main {
    grid-template-columns: minmax(0, 1fr) 280px;
  }
}

@media (max-width: 1024px) {
  .novel-main {
    grid-template-columns: 1fr;
    grid-template-areas:
      "editor"
      "sidebar";
  }

  .reference-shell {
    width: 100%;
    min-height: 280px;
  }

  .sticky-grid {
    grid-template-columns: repeat(auto-fill, minmax(148px, 1fr));
    overflow: visible;
    padding-right: 0;
  }

  .config-popover {
    width: min(320px, calc(100vw - 32px));
    right: -6px;
  }

  .assistant-grid {
    grid-template-columns: 1fr;
  }
}
</style>
