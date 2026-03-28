<script setup>
import { computed, useSlots } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: '',
  },
  effect: {
    type: String,
    default: 'light',
  },
  size: {
    type: String,
    default: 'default',
  },
  round: {
    type: Boolean,
    default: false,
  },
})

const slots = useSlots()

const normalizedType = computed(() => {
  const candidate = String(props.type || '').trim()
  if (['success', 'warning', 'danger', 'info', 'primary'].includes(candidate)) {
    return candidate
  }
  return ''
})

const normalizedEffect = computed(() => {
  const candidate = String(props.effect || 'light').trim()
  if (['dark', 'light', 'plain'].includes(candidate)) {
    return candidate
  }
  return 'light'
})

const normalizedSize = computed(() => {
  const candidate = String(props.size || 'default').trim()
  if (['large', 'default', 'small'].includes(candidate)) {
    return candidate
  }
  return 'default'
})

const tagClasses = computed(() => [
  'ui-tag',
  'el-tag',
  normalizedType.value ? `el-tag--${normalizedType.value}` : '',
  normalizedEffect.value ? `el-tag--${normalizedEffect.value}` : '',
  normalizedSize.value === 'small' ? 'el-tag--small' : '',
  normalizedSize.value === 'large' ? 'el-tag--large' : '',
  props.round ? 'is-round' : '',
])

const paletteMap = {
  default: {
    light: {
      bg: 'rgba(148, 163, 184, 0.14)',
      border: 'rgba(148, 163, 184, 0.26)',
      text: 'var(--qb-text-secondary-strong)',
    },
    plain: {
      bg: 'transparent',
      border: 'rgba(148, 163, 184, 0.34)',
      text: 'var(--qb-text-secondary-strong)',
    },
    dark: {
      bg: 'var(--qb-text-secondary-strong)',
      border: 'var(--qb-text-secondary-strong)',
      text: 'var(--qb-text-inverse)',
    },
  },
  primary: {
    light: {
      bg: 'var(--qb-primary-soft-bg)',
      border: 'var(--qb-primary-soft-border)',
      text: 'var(--qb-primary-student)',
    },
    plain: {
      bg: 'transparent',
      border: 'color-mix(in srgb, var(--qb-primary-student) 34%, white 66%)',
      text: 'var(--qb-primary-student)',
    },
    dark: {
      bg: 'var(--qb-primary-student)',
      border: 'var(--qb-primary-student)',
      text: 'var(--qb-text-inverse)',
    },
  },
  success: {
    light: {
      bg: 'color-mix(in srgb, var(--qb-success) 12%, white 88%)',
      border: 'color-mix(in srgb, var(--qb-success) 26%, white 74%)',
      text: 'color-mix(in srgb, var(--qb-success) 88%, black 12%)',
    },
    plain: {
      bg: 'transparent',
      border: 'color-mix(in srgb, var(--qb-success) 40%, white 60%)',
      text: 'color-mix(in srgb, var(--qb-success) 88%, black 12%)',
    },
    dark: {
      bg: 'var(--qb-success)',
      border: 'var(--qb-success)',
      text: 'var(--qb-text-inverse)',
    },
  },
  warning: {
    light: {
      bg: 'color-mix(in srgb, var(--qb-warning) 14%, white 86%)',
      border: 'color-mix(in srgb, var(--qb-warning) 28%, white 72%)',
      text: 'color-mix(in srgb, var(--qb-warning) 86%, black 14%)',
    },
    plain: {
      bg: 'transparent',
      border: 'color-mix(in srgb, var(--qb-warning) 42%, white 58%)',
      text: 'color-mix(in srgb, var(--qb-warning) 86%, black 14%)',
    },
    dark: {
      bg: 'var(--qb-warning)',
      border: 'var(--qb-warning)',
      text: 'var(--qb-text-inverse)',
    },
  },
  danger: {
    light: {
      bg: 'color-mix(in srgb, var(--qb-danger) 12%, white 88%)',
      border: 'color-mix(in srgb, var(--qb-danger) 24%, white 76%)',
      text: 'color-mix(in srgb, var(--qb-danger) 86%, black 14%)',
    },
    plain: {
      bg: 'transparent',
      border: 'color-mix(in srgb, var(--qb-danger) 38%, white 62%)',
      text: 'color-mix(in srgb, var(--qb-danger) 86%, black 14%)',
    },
    dark: {
      bg: 'var(--qb-danger)',
      border: 'var(--qb-danger)',
      text: 'var(--qb-text-inverse)',
    },
  },
  info: {
    light: {
      bg: 'color-mix(in srgb, var(--qb-info) 14%, white 86%)',
      border: 'color-mix(in srgb, var(--qb-info) 24%, white 76%)',
      text: 'color-mix(in srgb, var(--qb-info) 84%, black 16%)',
    },
    plain: {
      bg: 'transparent',
      border: 'color-mix(in srgb, var(--qb-info) 38%, white 62%)',
      text: 'color-mix(in srgb, var(--qb-info) 84%, black 16%)',
    },
    dark: {
      bg: 'var(--qb-info)',
      border: 'var(--qb-info)',
      text: 'var(--qb-text-inverse)',
    },
  },
}

const visualStyle = computed(() => {
  const typeKey = normalizedType.value || 'default'
  const palette = paletteMap[typeKey]?.[normalizedEffect.value] || paletteMap.default.light
  return {
    '--ui-tag-bg': palette.bg,
    '--ui-tag-border': palette.border,
    '--ui-tag-text': palette.text,
  }
})

const hasContent = computed(() => Boolean(slots.default))
</script>

<template>
  <span v-if="hasContent" :class="tagClasses" :style="visualStyle">
    <span class="el-tag__content">
      <slot />
    </span>
  </span>
</template>

<style scoped>
.ui-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  max-width: 100%;
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--ui-tag-border);
  border-radius: var(--qb-radius-base);
  background: var(--ui-tag-bg);
  color: var(--ui-tag-text);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
  vertical-align: middle;
  box-sizing: border-box;
}

.ui-tag.is-round {
  border-radius: 999px;
  padding-inline: 12px;
}

.ui-tag.el-tag--small {
  min-height: 22px;
  padding-inline: 8px;
  font-size: 12px;
}

.ui-tag.el-tag--large {
  min-height: 32px;
  padding-inline: 12px;
  font-size: 14px;
}

.el-tag__content {
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
