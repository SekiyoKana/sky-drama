<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ArrowLeft, UserRound, MapPin, Save, BookOpen, Plus, X, Languages, Settings2 } from 'lucide-vue-next'
import NeuButton from '@/components/base/NeuButton.vue'
import NeuSelect from '@/components/base/NeuSelect.vue'
import NeuMentionSelector from '@/components/base/NeuMentionSelector.vue'
import LanguageSwitcher from '@/components/base/LanguageSwitcher.vue'
import { apiKeyApi, aiApi, episodeApi, projectApi } from '@/api'
import { normalizePlatform } from '@/platforms'
import { useMessage } from '@/utils/useMessage'
import { resolveImageUrl } from '@/utils/assets'
import { useMention } from '@/utils/useMention'
import { safeRandomUUID } from '@/utils/id'

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
  image_url?: string
  reference_image?: string
}

type ReferenceCard = {
  id: string
  type: 'character' | 'scene'
  source: 'novel' | 'script' | 'asset'
  title: string
  subtitle: string
  imageUrl: string
  raw: any
}

type ModelType = 'text' | 'image' | 'video' | 'audio'
type ModelCatalog = {
  all: string[]
  byType: Record<ModelType, string[]>
}

const route = useRoute()
const router = useRouter()
const message = useMessage()
const { t } = useI18n()

const projectId = Number(route.params.projectId)
const episodeId = Number(route.params.episodeId)

const loading = ref(true)
const project = ref<any>(null)
const episode = ref<any>(null)
const draftText = ref('')
const novelCharacters = ref<NovelCharacter[]>([])
const novelScenes = ref<NovelScene[]>([])
const detailCard = ref<ReferenceCard | null>(null)
const isDragOverEditor = ref(false)

const novelConfig = reactive({
  key_id: '' as string | number,
  model: '',
  perspective: 'third',
  tone: 'cinematic',
  length: 'medium',
  temperature: 0.7
})

const creatorVisible = ref(false)
const creatorType = ref<'character' | 'scene'>('character')
const creatorForm = reactive({
  name: '',
  roleOrMood: '',
  description: ''
})

const loadingKeys = ref(false)
const fetchingModels = ref(false)
const availableKeys = ref<any[]>([])
const modelOptions = ref<string[]>([])
const modelCache = ref<Record<string, ModelCatalog>>({})

const showLanguageMenu = ref(false)
const showModelConfig = ref(false)
const languageMenuRef = ref<HTMLElement | null>(null)

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

const draftPlaceholder = computed(() => {
  return [
    t('novelWorkbench.journalTitle'),
    t('novelWorkbench.journalHint'),
    t('novelWorkbench.mentionHint'),
    '',
    t('novelWorkbench.journalPlaceholder')
  ].join('\n')
})

const showManualModelInput = computed(() => {
  return !!novelConfig.key_id && !fetchingModels.value && modelOptions.value.length === 0
})

const scriptCharacters = computed(() => {
  const script = (episode.value?.ai_config?.generated_script || {}) as any
  return Array.isArray(script.characters) ? script.characters : []
})

const scriptScenes = computed(() => {
  const script = (episode.value?.ai_config?.generated_script || {}) as any
  return Array.isArray(script.scenes) ? script.scenes : []
})

const mentionItems = computed(() => {
  const picked = new Set<string>()
  const out: Array<{ id: string; name: string; type: 'character' | 'scene'; image_url?: string }> = []

  const pushCharacter = (char: any) => {
    const id = String(char?.id || '')
    if (!id) return
    const key = `character:${id}`
    if (picked.has(key)) return
    picked.add(key)
    out.push({
      id,
      name: String(char?.name || t('novelWorkbench.unknownCharacter')),
      type: 'character',
      image_url: resolveImageUrl(String(char?.image_url || char?.reference_image || ''))
    })
  }

  const pushScene = (scene: any) => {
    const id = String(scene?.id || '')
    if (!id) return
    const key = `scene:${id}`
    if (picked.has(key)) return
    picked.add(key)
    out.push({
      id,
      name: String(scene?.location_name || t('novelWorkbench.unknownScene')),
      type: 'scene',
      image_url: resolveImageUrl(String(scene?.image_url || scene?.reference_image || ''))
    })
  }

  novelCharacters.value.forEach(pushCharacter)
  novelScenes.value.forEach(pushScene)
  scriptCharacters.value.forEach(pushCharacter)
  scriptScenes.value.forEach(pushScene)
  return out
})

const referenceCards = computed<ReferenceCard[]>(() => {
  const cards: ReferenceCard[] = []
  const picked = new Set<string>()

  const pushCard = (card: ReferenceCard) => {
    const key = `${card.type}:${card.id}`
    if (picked.has(key)) return
    picked.add(key)
    cards.push(card)
  }

  novelCharacters.value.forEach((c) => {
    pushCard({
      id: String(c.id),
      type: 'character',
      source: 'novel',
      title: c.name || t('novelWorkbench.unknownCharacter'),
      subtitle: c.role || c.description || '',
      imageUrl: resolveImageUrl(String(c.image_url || c.reference_image || '')),
      raw: c
    })
  })

  novelScenes.value.forEach((s) => {
    pushCard({
      id: String(s.id),
      type: 'scene',
      source: 'novel',
      title: s.location_name || t('novelWorkbench.unknownScene'),
      subtitle: s.mood || s.description || '',
      imageUrl: resolveImageUrl(String(s.image_url || s.reference_image || '')),
      raw: s
    })
  })

  scriptCharacters.value.forEach((c: any) => {
    pushCard({
      id: String(c.id || c.name || safeRandomUUID()),
      type: 'character',
      source: 'script',
      title: c.name || t('novelWorkbench.unknownCharacter'),
      subtitle: c.role || c.description || '',
      imageUrl: resolveImageUrl(String(c.image_url || c.reference_image || '')),
      raw: c
    })
  })

  scriptScenes.value.forEach((s: any) => {
    pushCard({
      id: String(s.id || s.location_name || safeRandomUUID()),
      type: 'scene',
      source: 'script',
      title: s.location_name || t('novelWorkbench.unknownScene'),
      subtitle: s.mood || s.description || '',
      imageUrl: resolveImageUrl(String(s.image_url || s.reference_image || '')),
      raw: s
    })
  })

  const assets = project.value?.assets || {}
  const fallbackChars = Array.isArray(assets.characters) ? assets.characters : []
  const fallbackScenes = Array.isArray(assets.scenes) ? assets.scenes : []

  fallbackChars.forEach((c: any) => {
    pushCard({
      id: String(c.id || c.name || safeRandomUUID()),
      type: 'character',
      source: 'asset',
      title: c.name || t('novelWorkbench.unknownCharacter'),
      subtitle: c.role || c.description || '',
      imageUrl: resolveImageUrl(String(c.image_url || c.reference_image || '')),
      raw: c
    })
  })

  fallbackScenes.forEach((s: any) => {
    pushCard({
      id: String(s.id || s.location_name || safeRandomUUID()),
      type: 'scene',
      source: 'asset',
      title: s.location_name || t('novelWorkbench.unknownScene'),
      subtitle: s.mood || s.description || '',
      imageUrl: resolveImageUrl(String(s.image_url || s.reference_image || '')),
      raw: s
    })
  })

  return cards.slice(0, 24)
})

const characterCards = computed(() => referenceCards.value.filter((card) => card.type === 'character'))
const sceneCards = computed(() => referenceCards.value.filter((card) => card.type === 'scene'))

const creatorTitle = computed(() =>
  creatorType.value === 'character'
    ? t('novelWorkbench.creator.characterTitle')
    : t('novelWorkbench.creator.sceneTitle')
)

const creatorTagLabel = computed(() =>
  creatorType.value === 'character'
    ? t('novelWorkbench.creator.roleLabel')
    : t('novelWorkbench.creator.moodLabel')
)

const creatorTagPlaceholder = computed(() =>
  creatorType.value === 'character'
    ? t('novelWorkbench.creator.rolePlaceholder')
    : t('novelWorkbench.creator.moodPlaceholder')
)

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

const applyTextModelOptions = (catalog: ModelCatalog) => {
  modelOptions.value = catalog.byType.text.length > 0 ? catalog.byType.text : []
}

const fetchModels = async (keyId: string | number | null | undefined) => {
  modelOptions.value = []
  if (!keyId) return
  const cacheKey = String(keyId)
  if (modelCache.value[cacheKey]) {
    applyTextModelOptions(modelCache.value[cacheKey])
    return
  }

  fetchingModels.value = true
  try {
    const res: any = await aiApi.testConnection(Number(keyId))
    const catalog = toModelCatalog(res)
    modelCache.value[cacheKey] = catalog
    applyTextModelOptions(catalog)
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
    if (newKey !== oldKey) fetchModels(newKey)
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

const noteStyle = (idx: number, type: 'character' | 'scene') => {
  const rotates = [-3, -1, 1, 2, -2, 3]
  const offsets = [0, -3, 4, -2, 5, -4]
  const hues = type === 'character'
    ? ['#fff6a8', '#fef08a', '#fef3c7']
    : ['#bfdbfe', '#bae6fd', '#a7f3d0']
  return {
    '--note-rot': `${rotates[idx % rotates.length]}deg`,
    '--note-offset': `${offsets[idx % offsets.length]}px`,
    '--note-bg': hues[idx % hues.length]
  } as Record<string, string>
}

const openCardDetail = (card: ReferenceCard) => {
  detailCard.value = card
}

const closeCardDetail = () => {
  detailCard.value = null
}

const openCreator = (type: 'character' | 'scene') => {
  creatorType.value = type
  creatorForm.name = ''
  creatorForm.roleOrMood = ''
  creatorForm.description = ''
  creatorVisible.value = true
}

const closeCreator = () => {
  creatorVisible.value = false
}

const saveNovelConfig = async (silent = false) => {
  if (!episode.value) return

  try {
    const nextConfig = {
      ...(episode.value.ai_config || {}),
      novel: {
        key_id: novelConfig.key_id,
        model: novelConfig.model,
        perspective: novelConfig.perspective,
        tone: novelConfig.tone,
        length: novelConfig.length,
        temperature: novelConfig.temperature,
        draft_text: draftText.value,
        characters: novelCharacters.value,
        scenes: novelScenes.value
      }
    }

    await episodeApi.update(projectId, episodeId, {
      title: episode.value.title,
      ai_config: nextConfig
    } as any)

    episode.value.ai_config = nextConfig
    if (!silent) message.success(t('novelWorkbench.messages.saved'))
  } catch (error) {
    console.error('[NovelWorkbench] save failed', error)
    if (!silent) message.error(t('novelWorkbench.messages.saveFailed'))
  }
}

const confirmCreate = async () => {
  const name = creatorForm.name.trim()
  if (!name) {
    message.warning(t('novelWorkbench.messages.nameRequired'))
    return
  }

  if (creatorType.value === 'character') {
    novelCharacters.value.unshift({
      id: makeCharacterId(novelCharacters.value.length),
      name,
      role: creatorForm.roleOrMood.trim(),
      description: creatorForm.description.trim(),
      image_url: '',
      reference_image: ''
    })
  } else {
    novelScenes.value.unshift({
      id: makeSceneId(novelScenes.value.length),
      location_name: name,
      mood: creatorForm.roleOrMood.trim(),
      description: creatorForm.description.trim(),
      image_url: '',
      reference_image: ''
    })
  }

  creatorVisible.value = false
  await saveNovelConfig(true)
  message.success(
    creatorType.value === 'character'
      ? t('novelWorkbench.messages.characterCreated')
      : t('novelWorkbench.messages.sceneCreated')
  )
}

const handleDraftInput = (e: Event) => {
  handleMentionInput(e)
}

const handleDraftBlur = () => {
  setTimeout(() => hideMention(), 120)
}

const handleSelectMention = (item: any) => {
  const start = mentionStartIndex.value
  if (start === -1) return
  insertMentionTag(item.type, String(item.id), { replaceMention: true, mentionStart: start })
  hideMention()
}

const normalizeMentionId = (type: 'character' | 'scene', rawId: string) => {
  const targetPrefix = type === 'character' ? 'char_' : 'scene_'
  return rawId.startsWith(targetPrefix) ? rawId : `${targetPrefix}${rawId}`
}

const insertMentionTag = (
  type: 'character' | 'scene',
  rawId: string,
  options: { replaceMention?: boolean; mentionStart?: number } = {}
) => {
  if (!draftInputRef.value) return
  const textarea = draftInputRef.value
  const text = draftText.value
  const tag = `{{${normalizeMentionId(type, rawId)}}}`

  let start = textarea.selectionStart ?? text.length
  let end = textarea.selectionEnd ?? start
  if (options.replaceMention && typeof options.mentionStart === 'number') {
    start = options.mentionStart
    end = textarea.selectionStart ?? start
  }

  draftText.value = text.slice(0, start) + tag + text.slice(end)

  nextTick(() => {
    textarea.focus()
    const newCursorPos = start + tag.length
    textarea.setSelectionRange(newCursorPos, newCursorPos)
  })
}

const closeMention = () => {
  hideMention()
}

const handleCardDragStart = (event: DragEvent, card: ReferenceCard) => {
  const payload = JSON.stringify({ type: card.type, id: String(card.id) })
  if (!event.dataTransfer) return
  event.dataTransfer.effectAllowed = 'copy'
  event.dataTransfer.setData('application/x-sky-mention', payload)
  event.dataTransfer.setData('text/plain', `{{${normalizeMentionId(card.type, String(card.id))}}}`)
}

const handleDraftDragOver = (event: DragEvent) => {
  if (!event.dataTransfer) return
  if (event.dataTransfer.types.includes('application/x-sky-mention')) {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'copy'
    isDragOverEditor.value = true
  }
}

const handleDraftDragLeave = () => {
  isDragOverEditor.value = false
}

const handleDraftDrop = (event: DragEvent) => {
  if (!event.dataTransfer) return
  const raw = event.dataTransfer.getData('application/x-sky-mention')
  if (!raw) return
  event.preventDefault()
  isDragOverEditor.value = false
  try {
    const parsed = JSON.parse(raw)
    if (parsed?.type === 'character' || parsed?.type === 'scene') {
      insertMentionTag(parsed.type, String(parsed.id))
    }
  } catch (_error) {
    // ignore invalid drag payload
  }
}

const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as Node
  if (languageMenuRef.value && !languageMenuRef.value.contains(target)) {
    showLanguageMenu.value = false
  }
}

const initData = async () => {
  loading.value = true
  try {
    const [pRes, eList, assets] = await Promise.all([
      projectApi.get(projectId),
      episodeApi.list(projectId),
      projectApi.getAssets(projectId).catch(() => ({ characters: [], scenes: [] }))
    ])

    project.value = { ...pRes, assets }
    const episodeRows = Array.isArray(eList) ? (eList as any[]) : (((eList as any)?.data || []) as any[])
    const currentEp = episodeRows.find((e: any) => e.id === episodeId)
    if (!currentEp) throw new Error('Episode not found')
    episode.value = currentEp

    const saved = (currentEp.ai_config?.novel || {}) as any
    draftText.value = String(saved.draft_text || '')
    novelConfig.key_id = saved.key_id ?? ''
    novelConfig.model = String(saved.model || '')
    if (saved.perspective) novelConfig.perspective = String(saved.perspective)
    if (saved.tone) novelConfig.tone = String(saved.tone)
    if (saved.length) novelConfig.length = String(saved.length)
    if (saved.temperature !== undefined) {
      const parsed = Number(saved.temperature)
      novelConfig.temperature = Number.isNaN(parsed) ? 0.7 : Math.max(0, Math.min(1.5, parsed))
    }

    novelCharacters.value = Array.isArray(saved.characters)
      ? saved.characters.map((c: any, idx: number) => ({
          id: String(c?.id || makeCharacterId(idx)),
          name: String(c?.name || ''),
          role: String(c?.role || ''),
          description: String(c?.description || ''),
          image_url: String(c?.image_url || ''),
          reference_image: String(c?.reference_image || '')
        }))
      : []

    novelScenes.value = Array.isArray(saved.scenes)
      ? saved.scenes.map((s: any, idx: number) => ({
          id: String(s?.id || makeSceneId(idx)),
          location_name: String(s?.location_name || ''),
          mood: String(s?.mood || ''),
          description: String(s?.description || ''),
          image_url: String(s?.image_url || ''),
          reference_image: String(s?.reference_image || '')
        }))
      : []
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
  await Promise.all([initData(), loadApiKeys()])
  if (novelConfig.key_id) await fetchModels(novelConfig.key_id)
})

onUnmounted(() => {
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

                <label class="config-field">
                  <span class="config-label">
                    {{ t('workbench.modelConfig.apiConnection') }}
                    <span v-if="loadingKeys">{{ t('workbench.modelConfig.loading') }}</span>
                  </span>
                  <NeuSelect
                    v-model="novelConfig.key_id"
                    :options="availableKeys"
                    :placeholder="t('workbench.modelConfig.selectConnection')"
                    size="mini"
                  />
                </label>

                <label class="config-field">
                  <span class="config-label">
                    {{ t('workbench.modelConfig.targetModel') }}
                    <span v-if="fetchingModels">{{ t('workbench.modelConfig.fetching') }}</span>
                  </span>
                  <NeuSelect
                    v-model="novelConfig.model"
                    :options="modelOptions"
                    :disabled="!novelConfig.key_id || fetchingModels"
                    :placeholder="t('workbench.modelConfig.autoDefault')"
                    size="mini"
                  />
                  <div v-if="showManualModelInput" class="manual-model">
                    <input
                      v-model="novelConfig.model"
                      class="config-input"
                      :placeholder="t('workbench.modelConfig.manualModelPlaceholder')"
                    />
                    <p>{{ t('workbench.modelConfig.manualModelHint') }}</p>
                  </div>
                </label>

                <label class="config-field">
                  <span>{{ t('novelWorkbench.config.perspective') }}</span>
                  <select v-model="novelConfig.perspective" class="config-input">
                    <option value="first">{{ t('novelWorkbench.perspectives.first') }}</option>
                    <option value="third">{{ t('novelWorkbench.perspectives.third') }}</option>
                    <option value="omniscient">{{ t('novelWorkbench.perspectives.omniscient') }}</option>
                  </select>
                </label>

                <label class="config-field">
                  <span>{{ t('novelWorkbench.config.tone') }}</span>
                  <select v-model="novelConfig.tone" class="config-input">
                    <option value="cinematic">{{ t('novelWorkbench.tones.cinematic') }}</option>
                    <option value="lyrical">{{ t('novelWorkbench.tones.lyrical') }}</option>
                    <option value="realistic">{{ t('novelWorkbench.tones.realistic') }}</option>
                  </select>
                </label>

                <label class="config-field">
                  <span>{{ t('novelWorkbench.config.length') }}</span>
                  <select v-model="novelConfig.length" class="config-input">
                    <option value="short">{{ t('novelWorkbench.lengths.short') }}</option>
                    <option value="medium">{{ t('novelWorkbench.lengths.medium') }}</option>
                    <option value="long">{{ t('novelWorkbench.lengths.long') }}</option>
                  </select>
                </label>

                <label class="config-field">
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

                <NeuButton size="sm" class="w-full mt-2" @click="saveNovelConfig(false)">
                  <Save class="w-4 h-4 mr-1" />
                  {{ t('novelWorkbench.save') }}
                </NeuButton>
              </div>
            </transition>
          </div>

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
        <aside class="reference-shell neu-flat">
          <div class="reference-head">
            <h2>{{ t('novelWorkbench.types.character') }}</h2>
            <button class="mini-icon-btn neu-flat" @click="openCreator('character')" :title="t('novelWorkbench.addCharacter')">
              <Plus class="w-3.5 h-3.5" />
            </button>
          </div>
          <div v-if="characterCards.length === 0" class="photo-empty section-empty">
            {{ t('projects.archive.noCharacters') }}
          </div>
          <div v-else class="sticky-grid custom-scroll">
            <article
              v-for="(card, idx) in characterCards"
              :key="`character-${card.id}`"
              class="sticky-note"
              :style="noteStyle(idx, 'character')"
              draggable="true"
              @dragstart="handleCardDragStart($event, card)"
              @click="openCardDetail(card)"
            >
              <div class="sticky-pin"></div>
              <div class="photo-image-wrap sticky-image neu-pressed">
                <img v-if="card.imageUrl" :src="card.imageUrl" class="photo-image" />
                <div v-else class="photo-image-placeholder">
                  <UserRound class="w-4 h-4" />
                </div>
              </div>
              <div class="photo-meta">
                <p class="photo-title">{{ card.title }}</p>
                <p class="photo-subtitle">{{ card.subtitle }}</p>
              </div>
            </article>
          </div>
        </aside>

        <section class="journal-shell neu-flat">
          <div class="journal-paper neu-pressed">
            <textarea
              ref="draftInputRef"
              v-model="draftText"
              class="journal-textarea"
              :class="{ 'is-drag-over': isDragOverEditor }"
              :placeholder="draftPlaceholder"
              @input="handleDraftInput"
              @blur="handleDraftBlur"
              @dragover="handleDraftDragOver"
              @dragleave="handleDraftDragLeave"
              @drop="handleDraftDrop"
            />
          </div>
        </section>

        <aside class="reference-shell neu-flat">
          <div class="reference-head">
            <h2>{{ t('novelWorkbench.types.scene') }}</h2>
            <button class="mini-icon-btn neu-flat" @click="openCreator('scene')" :title="t('novelWorkbench.addScene')">
              <Plus class="w-3.5 h-3.5" />
            </button>
          </div>
          <div v-if="sceneCards.length === 0" class="photo-empty section-empty">
            {{ t('projects.archive.noScenes') }}
          </div>
          <div v-else class="sticky-grid custom-scroll">
            <article
              v-for="(card, idx) in sceneCards"
              :key="`scene-${card.id}`"
              class="sticky-note"
              :style="noteStyle(idx, 'scene')"
              draggable="true"
              @dragstart="handleCardDragStart($event, card)"
              @click="openCardDetail(card)"
            >
              <div class="sticky-pin"></div>
              <div class="photo-image-wrap sticky-image neu-pressed">
                <img v-if="card.imageUrl" :src="card.imageUrl" class="photo-image" />
                <div v-else class="photo-image-placeholder">
                  <MapPin class="w-4 h-4" />
                </div>
              </div>
              <div class="photo-meta">
                <p class="photo-title">{{ card.title }}</p>
                <p class="photo-subtitle">{{ card.subtitle }}</p>
              </div>
            </article>
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
      <div v-if="creatorVisible" class="modal-mask" @click.self="closeCreator">
        <div class="modal-card neu-flat">
          <div class="modal-head">
            <h4>{{ creatorTitle }}</h4>
            <button class="modal-close neu-flat" @click="closeCreator">
              <X class="w-4 h-4" />
            </button>
          </div>
          <label class="modal-field">
            <span>{{ t('novelWorkbench.creator.nameLabel') }}</span>
            <input v-model="creatorForm.name" class="config-input" :placeholder="t('novelWorkbench.creator.namePlaceholder')" />
          </label>
          <label class="modal-field">
            <span>{{ creatorTagLabel }}</span>
            <input v-model="creatorForm.roleOrMood" class="config-input" :placeholder="creatorTagPlaceholder" />
          </label>
          <label class="modal-field">
            <span>{{ t('novelWorkbench.creator.descriptionLabel') }}</span>
            <textarea
              v-model="creatorForm.description"
              class="config-input modal-textarea"
              :placeholder="t('novelWorkbench.creator.descriptionPlaceholder')"
            />
          </label>
          <div class="modal-foot">
            <NeuButton size="xs" @click="closeCreator">{{ t('novelWorkbench.creator.cancel') }}</NeuButton>
            <NeuButton size="xs" variant="primary" @click="confirmCreate">{{ t('novelWorkbench.creator.confirm') }}</NeuButton>
          </div>
        </div>
      </div>

      <div v-if="detailCard" class="modal-mask" @click.self="closeCardDetail">
        <div class="detail-card neu-flat">
          <div class="modal-head">
            <h4>{{ detailCard.title }}</h4>
            <button class="modal-close neu-flat" @click="closeCardDetail">
              <X class="w-4 h-4" />
            </button>
          </div>
          <div class="detail-image-wrap neu-pressed">
            <img v-if="detailCard.imageUrl" :src="detailCard.imageUrl" class="detail-image" />
            <div v-else class="detail-image-placeholder">
              <UserRound v-if="detailCard.type === 'character'" class="w-5 h-5" />
              <MapPin v-else class="w-5 h-5" />
            </div>
          </div>
          <div class="detail-meta">
            <p>
              <span>{{ t('novelWorkbench.detail.typeLabel') }}:</span>
              {{ t(`novelWorkbench.types.${detailCard.type}`) }}
            </p>
            <p v-if="detailCard.type === 'character'">
              <span>{{ t('novelWorkbench.detail.roleLabel') }}:</span>
              {{ detailCard.raw?.role || t('novelWorkbench.detail.empty') }}
            </p>
            <p v-else>
              <span>{{ t('novelWorkbench.detail.moodLabel') }}:</span>
              {{ detailCard.raw?.mood || t('novelWorkbench.detail.empty') }}
            </p>
            <p class="detail-desc">
              <span>{{ t('novelWorkbench.detail.descriptionLabel') }}:</span>
              {{ detailCard.raw?.description || t('novelWorkbench.detail.empty') }}
            </p>
          </div>
        </div>
      </div>
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
  grid-template-columns: 320px minmax(0, 1fr) 320px;
  gap: 1rem;
}

.journal-shell {
  flex: 1;
  min-width: 0;
  border-radius: 2rem;
  padding: 1rem;
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
  padding: 0.9rem;
  background: #e0e5ec;
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

.journal-textarea.is-drag-over {
  box-shadow: inset 0 0 0 2px rgba(59, 130, 246, 0.4);
}

.reference-shell {
  width: 100%;
  min-width: 0;
  min-height: 0;
  border-radius: 2rem;
  background: #e0e5ec;
  display: flex;
  flex-direction: column;
  padding: 0.95rem;
}

.reference-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.reference-head h2,
.reference-section h2 {
  font-size: 12px;
  font-weight: 800;
  color: #4b5563;
  letter-spacing: 0.04em;
  text-transform: uppercase;
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
  margin-top: 2px;
  font-size: 11px;
  color: #475569;
  line-height: 1.25;
  min-height: 0;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
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
    grid-template-columns: 280px minmax(0, 1fr) 280px;
  }
}

@media (max-width: 1024px) {
  .novel-main {
    grid-template-columns: 1fr;
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
}
</style>
