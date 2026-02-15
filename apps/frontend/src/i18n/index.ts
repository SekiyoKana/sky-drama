import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN'
import enUS from './locales/en-US'
import jaJP from './locales/ja-JP'

export const SUPPORTED_LOCALES = ['zh-CN', 'en-US', 'ja-JP'] as const
export type AppLocale = (typeof SUPPORTED_LOCALES)[number]

const LOCALE_STORAGE_KEY = 'sky_drama_locale'
const FALLBACK_LOCALE: AppLocale = 'zh-CN'

const messages = {
  'zh-CN': zhCN,
  'en-US': enUS,
  'ja-JP': jaJP
}

const normalizeLocale = (locale?: string | null): AppLocale => {
  if (!locale) return FALLBACK_LOCALE

  if (SUPPORTED_LOCALES.includes(locale as AppLocale)) {
    return locale as AppLocale
  }

  if (locale.startsWith('zh')) return 'zh-CN'
  if (locale.startsWith('en')) return 'en-US'
  if (locale.startsWith('ja')) return 'ja-JP'

  return FALLBACK_LOCALE
}

export const getStoredLocale = (): AppLocale => {
  if (typeof window === 'undefined') return FALLBACK_LOCALE

  const fromStorage = localStorage.getItem(LOCALE_STORAGE_KEY)
  if (fromStorage) return normalizeLocale(fromStorage)

  return normalizeLocale(navigator.language)
}

const updateHtmlLang = (locale: AppLocale) => {
  if (typeof document !== 'undefined') {
    document.documentElement.lang = locale
  }
}

const initialLocale = getStoredLocale()
updateHtmlLang(initialLocale)

export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: initialLocale,
  fallbackLocale: FALLBACK_LOCALE,
  messages
})

export const setLocale = (locale: AppLocale) => {
  i18n.global.locale.value = locale
  if (typeof window !== 'undefined') {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  }
  updateHtmlLang(locale)
}

