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
  return ''
}

export const resolveImageUrl = (path: string | undefined | null): string => {
  if (!path) return ''
  
  // 1. Check for legacy absolute localhost URLs (from migrated database)
  // If the URL contains localhost/127.0.0.1 but we are NOT on localhost,
  // we must rewrite it to be relative or point to current origin.
  if (path.includes('localhost:11451') || path.includes('127.0.0.1:11451')) {
    // Extract the path part: http://localhost:11451/assets/foo.png -> /assets/foo.png
    try {
        const url = new URL(path)
        return url.pathname + url.search
    } catch(e) {
        // Fallback for malformed URLs
        return path.replace(/https?:\/\/(localhost|127\.0\.0\.1):11451/, '')
    }
  }

  if (path.startsWith('http') || path.startsWith('https') || path.startsWith('data:') || path.startsWith('blob:')) {
    return path
  }
  
  const baseUrl = getBaseUrl()
  if (!baseUrl) return path

  const cleanPath = path.startsWith('/') ? path : `/${path}`
  return `${baseUrl}${cleanPath}`
}
