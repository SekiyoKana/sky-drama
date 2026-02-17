const THINK_BLOCK_RE = /<think\b[^>]*>[\s\S]*?<\/think>/gi
const THINK_OPEN_RE = /<think\b[^>]*>[\s\S]*$/gi
const THINK_TAG_RE = /<\/?think\b[^>]*>/gi

export const stripThinkTags = (input: string): string => {
  if (!input) return input

  let cleaned = String(input)
  cleaned = cleaned.replace(THINK_BLOCK_RE, '')
  cleaned = cleaned.replace(THINK_OPEN_RE, '')
  cleaned = cleaned.replace(THINK_TAG_RE, '')
  cleaned = cleaned.replace(/\n{3,}/g, '\n\n')
  return cleaned.trim()
}

export const sanitizeThinkPayload = <T>(value: T): T => {
  if (typeof value === 'string') {
    return stripThinkTags(value) as T
  }
  if (Array.isArray(value)) {
    return value.map((item) => sanitizeThinkPayload(item)) as T
  }
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      out[k] = sanitizeThinkPayload(v)
    }
    return out as T
  }
  return value
}
