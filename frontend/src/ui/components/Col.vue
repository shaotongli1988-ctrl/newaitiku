<script setup>
import { computed, inject } from 'vue'

const props = defineProps({
  span: {
    type: Number,
    default: undefined,
  },
  offset: {
    type: Number,
    default: 0,
  },
  tag: {
    type: String,
    default: 'div',
  },
})

const rowContext = inject('uiRowContext', computed(() => ({
  gutter: 0,
})))

function normalizeGridNumber(value, fallback) {
  const candidate = Number(value)
  if (!Number.isFinite(candidate)) {
    return fallback
  }
  return Math.max(0, Math.min(24, Math.floor(candidate)))
}

const normalizedSpan = computed(() => {
  if (props.span === undefined || props.span === null || props.span === '') {
    return null
  }
  const candidate = normalizeGridNumber(props.span, 24)
  return candidate === 0 ? null : candidate
})

const normalizedOffset = computed(() => normalizeGridNumber(props.offset, 0))

const colClasses = computed(() => [
  'ui-col',
  'el-col',
  normalizedSpan.value ? `el-col-${normalizedSpan.value}` : '',
  normalizedOffset.value ? `el-col-offset-${normalizedOffset.value}` : '',
])

const colStyle = computed(() => {
  const gutter = Number(rowContext?.value?.gutter || 0)
  const halfGutter = `${gutter / 2}px`
  const style = {
    paddingLeft: gutter > 0 ? halfGutter : undefined,
    paddingRight: gutter > 0 ? halfGutter : undefined,
  }

  if (normalizedSpan.value) {
    const width = `${(normalizedSpan.value / 24) * 100}%`
    style.flex = `0 0 ${width}`
    style.maxWidth = width
  } else {
    style.flex = '1 1 0%'
    style.maxWidth = '100%'
  }

  if (normalizedOffset.value) {
    style.marginLeft = `${(normalizedOffset.value / 24) * 100}%`
  }

  return style
})
</script>

<template>
  <component :is="tag" :class="colClasses" :style="colStyle">
    <slot />
  </component>
</template>

<style scoped>
.ui-col {
  min-width: 0;
  box-sizing: border-box;
}
</style>
