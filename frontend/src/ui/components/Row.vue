<script setup>
import { computed, provide } from 'vue'

const props = defineProps({
  gutter: {
    type: Number,
    default: 0,
  },
  justify: {
    type: String,
    default: 'start',
  },
  align: {
    type: String,
    default: 'top',
  },
  tag: {
    type: String,
    default: 'div',
  },
})

const normalizedGutter = computed(() => {
  const candidate = Number(props.gutter || 0)
  if (!Number.isFinite(candidate) || candidate < 0) {
    return 0
  }
  return candidate
})

const justifyMap = {
  start: 'flex-start',
  end: 'flex-end',
  center: 'center',
  'space-around': 'space-around',
  'space-between': 'space-between',
  'space-evenly': 'space-evenly',
}

const alignMap = {
  top: 'flex-start',
  middle: 'center',
  bottom: 'flex-end',
}

const rowClasses = computed(() => [
  'ui-row',
  'el-row',
  props.justify && justifyMap[props.justify] ? `is-justify-${props.justify}` : '',
  props.align && alignMap[props.align] ? `is-align-${props.align}` : '',
])

const rowStyle = computed(() => {
  const halfGutter = `${normalizedGutter.value / 2}px`
  return {
    '--ui-row-gutter': `${normalizedGutter.value}px`,
    marginLeft: normalizedGutter.value > 0 ? `-${halfGutter}` : undefined,
    marginRight: normalizedGutter.value > 0 ? `-${halfGutter}` : undefined,
    justifyContent: justifyMap[props.justify] || justifyMap.start,
    alignItems: alignMap[props.align] || alignMap.top,
  }
})

provide('uiRowContext', computed(() => ({
  gutter: normalizedGutter.value,
})))
</script>

<template>
  <component :is="tag" :class="rowClasses" :style="rowStyle">
    <slot />
  </component>
</template>

<style scoped>
.ui-row {
  display: flex;
  flex-wrap: wrap;
  min-width: 0;
  box-sizing: border-box;
}
</style>
