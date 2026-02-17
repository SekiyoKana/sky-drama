import { BasePlatformProvider } from '@/platforms/base'

export class OpenAIPlatformProvider extends BasePlatformProvider {
  constructor() {
    super({
      key: 'openai',
      aliases: ['openai'],
      defaults: {
        base_url: 'https://api.openai.com/v1',
        text_endpoint: '/chat/completions',
        image_endpoint: '/images/generations',
        video_endpoint: '/videos',
        video_fetch_endpoint: '/videos/{task_id}',
        audio_endpoint: ''
      }
    })
  }
}
