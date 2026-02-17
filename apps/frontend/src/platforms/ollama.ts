import { BasePlatformProvider } from '@/platforms/base'

export class OllamaPlatformProvider extends BasePlatformProvider {
  constructor() {
    super({
      key: 'ollama',
      aliases: ['ollama'],
      requiresApiKey: false,
      defaults: {
        base_url: 'http://127.0.0.1:11434/api',
        text_endpoint: '/chat',
        image_endpoint: '',
        video_endpoint: '',
        video_fetch_endpoint: '',
        audio_endpoint: ''
      }
    })
  }

  override normalizeBaseUrl(baseUrl?: string): string {
    const normalized = super.normalizeBaseUrl(baseUrl)
    try {
      const parsed = new URL(normalized)
      const path = (parsed.pathname || '').replace(/\/+$/, '')
      if (!path) {
        return `${normalized}/api`
      }
      return normalized
    } catch {
      return normalized
    }
  }
}
