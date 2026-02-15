<script setup lang="ts">
defineProps<{
  title?: string
  padding?: string // 允许自定义内边距
  clickable?: boolean // 是否可点击（用于列表项）
}>()
</script>

<template>
  <div 
    class="rounded-[2rem] neu-flat bg-[#E0E5EC] transition-all duration-300"
    :class="[
      padding || 'p-8',
      clickable ? 'cursor-pointer hover:-translate-y-1 hover:shadow-lg' : '' // 可点击时的悬浮动效
    ]"
  >
    <div v-if="title" class="mb-6 flex items-center justify-between">
      <h3 class="text-xl font-bold text-gray-700">{{ title }}</h3>
      <slot name="action" /> </div>

    <slot />
  </div>
</template>