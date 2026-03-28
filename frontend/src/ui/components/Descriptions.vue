<script setup>
import { computed, provide } from 'vue'

const props = defineProps({
  column: {
    type: Number,
    default: 3,
  },
  border: {
    type: Boolean,
    default: false,
  },
  size: {
    type: String,
    default: 'default',
  },
  direction: {
    type: String,
    default: 'horizontal',
  },
})

const normalizedColumn = computed(() => {
  const candidate = Number(props.column || 3)
  if (!Number.isFinite(candidate) || candidate <= 0) {
    return 3
  }
  return Math.max(1, Math.floor(candidate))
})

const normalizedSize = computed(() => {
  const candidate = String(props.size || 'default').trim()
  if (['large', 'default', 'small'].includes(candidate)) {
    return candidate
  }
  return 'default'
})

const normalizedDirection = computed(() => {
  const candidate = String(props.direction || 'horizontal').trim()
  return candidate === 'vertical' ? 'vertical' : 'horizontal'
})

const descriptionClasses = computed(() => [
  'ui-descriptions',
  'el-descriptions',
  props.border ? 'is-bordered' : '',
  normalizedSize.value === 'small' ? 'el-descriptions--small' : '',
  normalizedSize.value === 'large' ? 'el-descriptions--large' : '',
  normalizedDirection.value === 'vertical' ? 'is-vertical' : '',
])

const descriptionStyle = computed(() => ({
  '--ui-descriptions-columns': String(normalizedColumn.value),
}))

provide('uiDescriptionsContext', computed(() => ({
  column: normalizedColumn.value,
  border: props.border,
  size: normalizedSize.value,
  direction: normalizedDirection.value,
})))
</script>

<template>
  <section class="el-descriptions__wrapper">
    <div :class="descriptionClasses" :style="descriptionStyle">
      <div class="el-descriptions__body">
        <div class="ui-descriptions__grid">
          <slot />
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.ui-descriptions {
  width: 100%;
}

.ui-descriptions__grid {
  display: grid;
  grid-template-columns: repeat(var(--ui-descriptions-columns), minmax(0, 1fr));
  gap: 12px;
}

.ui-descriptions.is-bordered .ui-descriptions__grid {
  gap: 0;
  border: 1px solid color-mix(in srgb, var(--qb-border-subtle) 82%, white 18%);
  border-radius: var(--qb-radius-base);
  overflow: hidden;
}

.ui-descriptions.el-descriptions--small .ui-descriptions__grid {
  gap: 10px;
}
</style>
