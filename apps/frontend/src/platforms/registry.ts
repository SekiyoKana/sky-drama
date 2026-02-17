import {
  BasePlatformProvider,
  type EndpointField,
  type PlatformDefaults,
  type PlatformType
} from '@/platforms/base'
import { OllamaPlatformProvider } from '@/platforms/ollama'
import { OpenAIPlatformProvider } from '@/platforms/openai'
import { VolcenginePlatformProvider } from '@/platforms/volcengine'

const providers: Record<PlatformType, BasePlatformProvider> = {
  openai: new OpenAIPlatformProvider(),
  ollama: new OllamaPlatformProvider(),
  volcengine: new VolcenginePlatformProvider()
}

const aliasToPlatform: Record<string, PlatformType> = {}

Object.entries(providers).forEach(([platformKey, provider]) => {
  const aliases = new Set([provider.key, platformKey, ...(provider.aliases || [])])
  aliases.forEach((alias) => {
    aliasToPlatform[String(alias).trim().toLowerCase()] = platformKey as PlatformType
  })
})

export const PLATFORM_TYPES: PlatformType[] = ['openai', 'ollama', 'volcengine']

export type PlatformConfig = PlatformDefaults & {
  platform: PlatformType
}

export const normalizePlatform = (platform?: string): PlatformType => {
  const value = (platform || 'openai').trim().toLowerCase()
  return aliasToPlatform[value] || 'openai'
}

export const getPlatformProvider = (platform?: string): BasePlatformProvider => {
  return providers[normalizePlatform(platform)]
}

export const getPlatformDefaults = (platform?: string): PlatformDefaults => {
  return getPlatformProvider(platform).defaults
}

export const platformRequiresApiKey = (platform?: string): boolean => {
  return getPlatformProvider(platform).requiresApiKey
}

export const resolvePlatformBaseUrl = (platform?: string, baseUrl?: string): string => {
  return getPlatformProvider(platform).normalizeBaseUrl(baseUrl)
}

export const resolvePlatformEndpoint = (
  platform: string | undefined,
  endpointName: EndpointField,
  endpointValue?: string
): string => {
  return getPlatformProvider(platform).resolveEndpoint(endpointName, endpointValue)
}

export const createPlatformConfig = (platform?: string): PlatformConfig => {
  const normalized = normalizePlatform(platform)
  const defaults = getPlatformDefaults(normalized)
  return {
    platform: normalized,
    ...defaults
  }
}

export const mergePlatformConfig = (
  platform: string | undefined,
  incoming: Partial<PlatformDefaults>
): PlatformConfig => {
  const normalized = normalizePlatform(platform)
  const provider = getPlatformProvider(normalized)
  const defaults = provider.defaults

  return {
    platform: normalized,
    base_url: provider.normalizeBaseUrl(incoming.base_url || defaults.base_url),
    text_endpoint: provider.resolveEndpoint('text_endpoint', incoming.text_endpoint),
    image_endpoint: provider.resolveEndpoint('image_endpoint', incoming.image_endpoint),
    video_endpoint: provider.resolveEndpoint('video_endpoint', incoming.video_endpoint),
    video_fetch_endpoint: provider.resolveEndpoint(
      'video_fetch_endpoint',
      incoming.video_fetch_endpoint
    ),
    audio_endpoint: provider.resolveEndpoint('audio_endpoint', incoming.audio_endpoint)
  }
}
