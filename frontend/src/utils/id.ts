export const safeRandomUUID = (): string => {
  try {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID()
    }
  } catch {
    // ignore
  }

  const rand = () => Math.random().toString(16).slice(2, 10)
  return `${Date.now().toString(16)}${rand()}${rand()}`
}
