<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  modelValue: boolean
  label?: string
  disabled?: boolean
  size?: 'sm' | 'md'
}>(), {
  disabled: false,
  size: 'md'
})

const emit = defineEmits(['update:modelValue', 'change'])

const isSm = computed(() => props.size === 'sm')

const trackClass = computed(() => [
  'relative inline-flex items-center rounded-full neu-pressed-sm transition-all',
  isSm.value ? 'w-10 h-5' : 'w-12 h-6',
  props.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
])

const knobClass = computed(() => [
  'absolute rounded-full neu-flat-sm transition-transform duration-200',
  isSm.value ? 'w-4 h-4 top-0.5 left-0.5' : 'w-5 h-5 top-0.5 left-0.5',
  props.modelValue ? (isSm.value ? 'translate-x-5' : 'translate-x-6') : 'translate-x-0'
])

const toggle = () => {
  if (props.disabled) return
  const next = !props.modelValue
  emit('update:modelValue', next)
  emit('change', next)
}
</script>

<template>
  <label class="flex items-center justify-between gap-3 select-none">
    <span v-if="label" class="text-xs text-gray-600">{{ label }}</span>
    <button
      type="button"
      role="switch"
      :aria-checked="modelValue"
      :class="trackClass"
      @click="toggle"
    >
      <span
        class="absolute inset-0 rounded-full transition-colors"
        :class="modelValue ? 'bg-orange-300/80 shadow-[inset_0_0_0_1px_rgba(251,146,60,0.6)]' : 'bg-transparent'"
      ></span>
      <span :class="knobClass"></span>
    </button>
  </label>
</template>
