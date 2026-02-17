export type { EndpointField, PlatformDefaults, PlatformType } from '@/platforms/base'
export {
  PLATFORM_TYPES,
  createPlatformConfig,
  getPlatformDefaults,
  getPlatformProvider,
  mergePlatformConfig,
  normalizePlatform,
  platformRequiresApiKey,
  resolvePlatformBaseUrl,
  resolvePlatformEndpoint
} from '@/platforms/registry'
