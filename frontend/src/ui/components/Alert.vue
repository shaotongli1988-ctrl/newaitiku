<script setup>
import { computed, ref, useSlots } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '',
  },
  description: {
    type: String,
    default: '',
  },
  type: {
    type: String,
    default: 'info',
  },
  effect: {
    type: String,
    default: 'light',
  },
  closable: {
    type: Boolean,
    default: true,
  },
  showIcon: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close'])
const slots = useSlots()
const closed = ref(false)

const normalizedType = computed(() => {
  const candidate = String(props.type || 'info').trim()
  if (['success', 'warning', 'info', 'error'].includes(candidate)) {
    return candidate
  }
  return 'info'
})

const normalizedEffect = computed(() => {
  const candidate = String(props.effect || 'light').trim()
  if (['light', 'dark'].includes(candidate)) {
    return candidate
  }
  return 'light'
})

const hasBody = computed(() => Boolean(props.description) || Boolean(slots.default))
const isVisible = computed(() => !closed.value)

const paletteMap = {
  success: {
    light: {
      bg: 'color-mix(in srgb, var(--qb-success) 10%, white 90%)',
      border: 'color-mix(in srgb, var(--qb-success) 24%, white 76%)',
      accent: 'color-mix(in srgb, var(--qb-success) 88%, black 12%)',
      text: 'color-mix(in srgb, var(--qb-success) 84%, black 16%)',
    },
    dark: {
      bg: 'color-mix(in srgb, var(--qb-success) 84%, black 16%)',
      border: 'color-mix(in srgb, var(--qb-success) 84%, black 16%)',
      accent: 'var(--qb-text-inverse)',
      text: 'rgba(255, 255, 255, 0.92)',
    },
    icon: '✓',
  },
  warning: {
    light: {
      bg: 'color-mix(in srgb, var(--qb-warning) 10%, white 90%)',
      border: 'color-mix(in srgb, var(--qb-warning) 24%, white 76%)',
      accent: 'color-mix(in srgb, var(--qb-warning) 86%, black 14%)',
      text: 'color-mix(in srgb, var(--qb-warning) 84%, black 16%)',
    },
    dark: {
      bg: 'color-mix(in srgb, var(--qb-warning) 82%, black 18%)',
      border: 'color-mix(in srgb, var(--qb-warning) 82%, black 18%)',
      accent: 'var(--qb-text-inverse)',
      text: 'rgba(255, 255, 255, 0.92)',
    },
    icon: '!',
  },
  info: {
    light: {
      bg: 'var(--qb-primary-soft-bg)',
      border: 'var(--qb-primary-soft-border)',
      accent: 'var(--qb-primary-student)',
      text: 'var(--qb-text-secondary-strong)',
    },
    dark: {
      bg: 'color-mix(in srgb, var(--qb-primary-student) 84%, black 16%)',
      border: 'color-mix(in srgb, var(--qb-primary-student) 84%, black 16%)',
      accent: 'var(--qb-text-inverse)',
      text: 'rgba(255, 255, 255, 0.92)',
    },
    icon: 'i',
  },
  error: {
    light: {
      bg: 'color-mix(in srgb, var(--qb-danger) 10%, white 90%)',
      border: 'color-mix(in srgb, var(--qb-danger) 24%, white 76%)',
      accent: 'color-mix(in srgb, var(--qb-danger) 88%, black 12%)',
      text: 'color-mix(in srgb, var(--qb-danger) 84%, black 16%)',
    },
    dark: {
      bg: 'color-mix(in srgb, var(--qb-danger) 82%, black 18%)',
      border: 'color-mix(in srgb, var(--qb-danger) 82%, black 18%)',
      accent: 'var(--qb-text-inverse)',
      text: 'rgba(255, 255, 255, 0.92)',
    },
    icon: '!',
  },
}

const visualStyle = computed(() => {
  const palette = paletteMap[normalizedType.value]?.[normalizedEffect.value] || paletteMap.info.light
  return {
    '--ui-alert-bg': palette.bg,
    '--ui-alert-border': palette.border,
    '--ui-alert-accent': palette.accent,
    '--ui-alert-text': palette.text,
  }
})

const iconGlyph = computed(() => paletteMap[normalizedType.value]?.icon || 'i')

function handleClose() {
  closed.value = true
  emit('close')
}
</script>

<template>
  <section
    v-if="isVisible"
    class="ui-alert el-alert"
    :class="[`el-alert--${normalizedType}`, `is-${normalizedEffect}`]"
    :style="visualStyle"
    role="status"
    aria-live="polite"
  >
    <div v-if="showIcon" class="ui-alert__icon el-alert__icon" aria-hidden="true">
      <slot name="icon">
        <span class="ui-alert__icon-glyph">{{ iconGlyph }}</span>
      </slot>
    </div>

    <div class="ui-alert__content el-alert__content">
      <p v-if="title || slots.title" class="ui-alert__title el-alert__title">
        <slot name="title">
          {{ title }}
        </slot>
      </p>

      <div v-if="hasBody" class="ui-alert__description el-alert__description">
        <slot>
          {{ description }}
        </slot>
      </div>
    </div>

    <button v-if="closable" type="button" class="ui-alert__close" aria-label="关闭提示" @click="handleClose">
      ×
    </button>
  </section>
</template>

<style scoped>
.ui-alert {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--ui-alert-border);
  border-radius: var(--qb-radius-base);
  background: var(--ui-alert-bg);
  color: var(--ui-alert-text);
  box-sizing: border-box;
}

.ui-alert__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  flex: 0 0 22px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--ui-alert-accent) 14%, white 86%);
  color: var(--ui-alert-accent);
  font-weight: 700;
  line-height: 1;
}

.ui-alert__icon-glyph {
  transform: translateY(-0.5px);
}

.ui-alert__content {
  flex: 1 1 auto;
  min-width: 0;
}

.ui-alert__title {
  margin: 0;
  color: var(--ui-alert-accent);
  font-size: 14px;
  font-weight: 700;
  line-height: 1.5;
}

.ui-alert__description {
  margin-top: 6px;
  color: var(--ui-alert-text);
  font-size: 13px;
  line-height: 1.7;
}

.ui-alert__close {
  flex: 0 0 auto;
  margin: -2px -2px 0 0;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--ui-alert-accent);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}
</style>
