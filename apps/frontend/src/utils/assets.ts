export const getBaseUrl = (): string => {
  const apiUrl = import.meta.env.VITE_API_URL || '/v1'
  if (apiUrl.startsWith('http')) {
    try {
      const url = new URL(apiUrl)
      return url.origin
    } catch (e) {
      console.error('Invalid VITE_API_URL:', apiUrl)
      return ''
    }
  }
  if (typeof window !== 'undefined') {
    return window.location.origin
  }
  return ''
}

export const resolveImageUrl = (path: string | undefined | null): string => {
  if (!path) return ''
  let normalizedPath = path

  // Tauri: always serve assets from local backend
  // @ts-ignore
  const isTauri = typeof window !== 'undefined' && (window as any).__TAURI_INTERNALS__ !== undefined
  if (isTauri) {
    if (
      normalizedPath.startsWith('http') ||
      normalizedPath.startsWith('https') ||
      normalizedPath.startsWith('data:') ||
      normalizedPath.startsWith('blob:')
    ) {
      return normalizedPath
    }
    const cleanPath = normalizedPath.startsWith('/') ? normalizedPath : `/${normalizedPath}`
    return `http://127.0.0.1:11451${cleanPath}`
  }
  
  // 1. Check for legacy absolute localhost URLs (from migrated database)
  // If the URL contains localhost/127.0.0.1 but we are NOT on localhost,
  // we must rewrite it to be relative or point to current origin.
  if (normalizedPath.includes('localhost:11451') || normalizedPath.includes('127.0.0.1:11451')) {
    // Extract the path part: http://localhost:11451/assets/foo.png -> /assets/foo.png
    try {
        const url = new URL(normalizedPath)
        normalizedPath = url.pathname + url.search
    } catch(e) {
        // Fallback for malformed URLs
        normalizedPath = normalizedPath.replace(/https?:\/\/(localhost|127\.0\.0\.1):11451/, '')
    }
  }

  if (
    normalizedPath.startsWith('http') ||
    normalizedPath.startsWith('https') ||
    normalizedPath.startsWith('data:') ||
    normalizedPath.startsWith('blob:')
  ) {
    return normalizedPath
  }
  
  const baseUrl = getBaseUrl()
  if (!baseUrl) return normalizedPath

  const cleanPath = normalizedPath.startsWith('/') ? normalizedPath : `/${normalizedPath}`
  return `${baseUrl}${cleanPath}`
}
