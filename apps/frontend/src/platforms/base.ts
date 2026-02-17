export type PlatformType = 'openai' | 'ollama' | 'volcengine'

export type EndpointField =
  | 'text_endpoint'
  | 'image_endpoint'
  | 'video_endpoint'
  | 'video_fetch_endpoint'
  | 'audio_endpoint'

export type PlatformDefaults = {
  base_url: string
  text_endpoint: string
  image_endpoint: string
  video_endpoint: string
  video_fetch_endpoint: string
  audio_endpoint: string
}

export class BasePlatformProvider {
  key: PlatformType
  aliases: string[]
  requiresApiKey: boolean
  defaults: PlatformDefaults

  constructor(options: {
    key: PlatformType
    aliases?: string[]
    requiresApiKey?: boolean
    defaults: PlatformDefaults
  }) {
    this.key = options.key
    this.aliases = options.aliases || []
    this.requiresApiKey = options.requiresApiKey ?? true
    this.defaults = options.defaults
  }

  normalizeBaseUrl(baseUrl?: string): string {
    const candidate = (baseUrl || '').trim()
    if (candidate) {
      return candidate.replace(/\/+$/, '')
    }
    return this.defaults.base_url
  }

  resolveEndpoint(endpointName: EndpointField, endpointValue?: string): string {
    const candidate = (endpointValue || '').trim()
    if (!candidate) {
      return this.defaults[endpointName]
    }
    if (!candidate.startsWith('/')) {
      return `/${candidate}`
    }
    return candidate
  }
}
