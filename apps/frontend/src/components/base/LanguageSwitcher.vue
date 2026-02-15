<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { setLocale, SUPPORTED_LOCALES, type AppLocale } from '@/i18n'

const { locale, t } = useI18n()

const options = computed<Array<{ label: string; value: AppLocale }>>(() => [
  { label: t('language.zhCN'), value: 'zh-CN' },
  { label: t('language.enUS'), value: 'en-US' },
  { label: t('language.jaJP'), value: 'ja-JP' }
])

const current = computed({
  get: () => locale.value as AppLocale,
  set: (value: string) => {
    const next = SUPPORTED_LOCALES.includes(value as AppLocale)
      ? (value as AppLocale)
      : 'zh-CN'
    setLocale(next)
  }
})
</script>

<template>
  <div class="inline-flex items-center gap-2 rounded-xl bg-[#E0E5EC] px-3 py-2 shadow-[3px_3px_10px_#b8b9be,-3px_-3px_10px_#ffffff]">
    <span class="text-xs font-bold text-gray-500 whitespace-nowrap">{{ t('language.label') }}</span>
    <select
      v-model="current"
      class="rounded-lg bg-[#E0E5EC] px-2 py-1 text-xs font-bold text-gray-700 outline-none neu-flat"
    >
      <option v-for="item in options" :key="item.value" :value="item.value">
        {{ item.label }}
      </option>
    </select>
  </div>
</template>
