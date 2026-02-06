export const getBaseUrl = (): string => {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:11451/v1'
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
  if (path.startsWith('http') || path.startsWith('https') || path.startsWith('data:') || path.startsWith('blob:')) {
    return path
  }
  
  const baseUrl = getBaseUrl()
  if (!baseUrl) return path

  const cleanPath = path.startsWith('/') ? path : `/${path}`
  return `${baseUrl}${cleanPath}`
}
