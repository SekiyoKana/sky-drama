import { BasePlatformProvider, type EndpointField } from '@/platforms/base'

export class VolcenginePlatformProvider extends BasePlatformProvider {
  constructor() {
    super({
      key: 'volcengine',
      aliases: ['volcengine', 'ark', 'doubao', 'volcano', 'volc', 'huoshan', '火山引擎'],
      defaults: {
        base_url: 'https://ark.cn-beijing.volces.com/api/v3',
        text_endpoint: '/chat/completions',
        image_endpoint: '/images/generations',
        video_endpoint: '/contents/generations/tasks',
        video_fetch_endpoint: '/contents/generations/tasks/{task_id}',
        audio_endpoint: ''
      }
    })
  }

  override resolveEndpoint(endpointName: EndpointField, endpointValue?: string): string {
    let candidate = (endpointValue || '').trim()

    if (endpointName === 'video_endpoint' && ['', 'videos', '/videos'].includes(candidate)) {
      candidate = ''
    }
    if (
      endpointName === 'video_fetch_endpoint' &&
      [
        '',
        'videos/{task_id}',
        '/videos/{task_id}',
        'contents/generations/tasks',
        '/contents/generations/tasks'
      ].includes(candidate)
    ) {
      candidate = ''
    }

    return super.resolveEndpoint(endpointName, candidate)
  }
}
