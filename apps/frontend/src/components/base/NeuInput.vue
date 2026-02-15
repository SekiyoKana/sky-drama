<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  modelValue: string | number
  label?: string
  placeholder?: string
  type?: string
  disabled?: boolean
  error?: string // 错误提示信息
}>()

const emit = defineEmits(['update:modelValue', 'enter']) // 支持回车事件

const inputClass = computed(() => {
  return [
    'w-full px-5 py-3 rounded-2xl outline-none transition-colors duration-200',
    'neu-pressed', // 核心：凹陷效果
    'bg-transparent', // 背景透明，复用父级背景色
    props.disabled ? 'opacity-50 cursor-not-allowed' : 'text-gray-700 focus:text-blue-600',
    props.error ? 'text-red-500 placeholder-red-300' : 'placeholder-gray-400'
  ]
})
</script>

<template>
  <div class="flex flex-col gap-2">
    <label v-if="label" class="ml-2 text-sm font-bold text-gray-500 uppercase tracking-wide">
      {{ label }}
    </label>
    
    <input
      :type="type || 'text'"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :class="inputClass"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      @keyup.enter="emit('enter')"
    />

    <span v-if="error" class="ml-2 text-xs text-red-500 fade-in">
      {{ error }}
    </span>
  </div>
</template>