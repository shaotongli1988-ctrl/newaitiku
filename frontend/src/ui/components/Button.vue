<script setup>
import { computed, useSlots } from 'vue'
import {
  normalizeButtonSize,
  normalizeButtonType,
  resolveButtonPalette,
  resolveButtonVariant,
} from './buttonShared'

const props = defineProps({
  type: {
    type: String,
    default: '',
  },
  size: {
    type: String,
    default: '',
  },
  plain: {
    type: Boolean,
    default: false,
  },
  link: {
    type: Boolean,
    default: false,
  },
  text: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  icon: {
    type: [Object, Function],
    default: null,
  },
  nativeType: {
    type: String,
    default: 'button',
  },
  round: {
    type: Boolean,
    default: false,
  },
  circle: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['click'])
const slots = useSlots()

const normalizedType = computed(() => normalizeButtonType(props.type))
const normalizedSize = computed(() => normalizeButtonSize(props.size))
const variant = computed(() =>
  resolveButtonVariant({
    plain: props.plain,
    link: props.link,
    text: props.text,
  }),
)

const paletteStyle = computed(() => {
  const palette = resolveButtonPalette(normalizedType.value, variant.value)
  return {
    '--ui-button-bg': palette.bg,
    '--ui-button-border': palette.border,
    '--ui-button-text': palette.text,
    '--ui-button-hover-bg': palette.hoverBg,
    '--ui-button-hover-border': palette.hoverBorder,
    '--ui-button-hover-text': palette.hoverText,
  }
})

const isDisabled = computed(() => Boolean(props.disabled || props.loading))
const hasDefaultSlot = computed(() => Boolean(slots.default))
const buttonClasses = computed(() => [
  'ui-button',
  'el-button',
  normalizedType.value ? `el-button--${normalizedType.value}` : '',
  normalizedSize.value !== 'default' ? `el-button--${normalizedSize.value}` : '',
  variant.value === 'plain' ? 'is-plain' : '',
  variant.value === 'link' ? 'is-link' : '',
  variant.value === 'text' ? 'is-text' : '',
  props.loading ? 'is-loading' : '',
  isDisabled.value ? 'is-disabled' : '',
  props.round ? 'is-round' : '',
  props.circle ? 'is-circle' : '',
  !hasDefaultSlot.value ? 'is-icon-only' : '',
])

function handleClick(event) {
  if (isDisabled.value) {
    event.preventDefault()
    event.stopPropagation()
    return
  }
  emit('click', event)
}
</script>

<template>
  <button
    :class="buttonClasses"
    :style="paletteStyle"
    :type="nativeType || 'button'"
    :disabled="isDisabled"
    @click="handleClick"
  >
    <span
      v-if="loading || icon"
      class="el-button__icon"
      :class="{ 'is-loading': loading }"
    >
      <span v-if="loading" class="ui-button__spinner" />
      <component :is="icon" v-else />
    </span>

    <span v-if="hasDefaultSlot" class="el-button__text">
      <slot />
    </span>
  </button>
</template>

<style scoped>
.ui-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 36px;
  padding: 0 18px;
  border: 1px solid var(--ui-button-border);
  border-radius: 12px;
  background: var(--ui-button-bg);
  color: var(--ui-button-text);
  font-size: 14px;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background-color 180ms ease,
    border-color 180ms ease,
    color 180ms ease,
    box-shadow 180ms ease,
    transform 180ms ease;
  box-sizing: border-box;
}

.ui-button:hover:not(.is-disabled) {
  background: var(--ui-button-hover-bg);
  border-color: var(--ui-button-hover-border);
  color: var(--ui-button-hover-text);
  box-shadow: 0 12px 24px -20px color-mix(in srgb, var(--qb-primary-student) 34%, transparent 66%);
}

.ui-button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--qb-primary-soft-bg) 70%, white 30%);
}

.ui-button:active:not(.is-disabled) {
  transform: translateY(1px);
}

.ui-button.is-disabled {
  opacity: 0.62;
  cursor: not-allowed;
  box-shadow: none;
}

.ui-button.is-round {
  border-radius: 999px;
}

.ui-button.is-circle {
  width: 36px;
  min-width: 36px;
  padding: 0;
  border-radius: 999px;
}

.ui-button.el-button--small {
  min-height: 30px;
  padding-inline: 12px;
  border-radius: 10px;
  font-size: 13px;
}

.ui-button.el-button--large {
  min-height: 42px;
  padding-inline: 22px;
  border-radius: 14px;
  font-size: 15px;
}

.ui-button.is-link,
.ui-button.is-text {
  min-height: auto;
  padding: 4px 6px;
  box-shadow: none;
}

.ui-button.is-link {
  border-color: transparent;
  text-decoration: none;
}

.ui-button.is-link:hover:not(.is-disabled) {
  text-decoration: underline;
  text-underline-offset: 3px;
}

.ui-button.is-icon-only {
  min-width: 36px;
  padding-inline: 10px;
}

.el-button__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1em;
  height: 1em;
  font-size: 1.05em;
}

.el-button__icon :deep(svg) {
  width: 1em;
  height: 1em;
  fill: currentColor;
}

.ui-button__spinner {
  width: 1em;
  height: 1em;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 999px;
  animation: ui-button-spin 700ms linear infinite;
}

.el-button__text {
  display: inline-flex;
  align-items: center;
}

@keyframes ui-button-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
