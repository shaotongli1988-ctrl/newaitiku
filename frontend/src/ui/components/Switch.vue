<script setup>
import { computed } from 'vue'
import {
  resolveSwitchChecked,
  resolveSwitchNextValue,
  resolveSwitchPrompt,
} from './switchShared'

const props = defineProps({
  modelValue: {
    type: [Boolean, String, Number],
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  activeValue: {
    type: [Boolean, String, Number],
    default: true,
  },
  inactiveValue: {
    type: [Boolean, String, Number],
    default: false,
  },
  activeText: {
    type: String,
    default: '',
  },
  inactiveText: {
    type: String,
    default: '',
  },
  inlinePrompt: {
    type: Boolean,
    default: false,
  },
  name: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue', 'change'])

const isChecked = computed(() =>
  resolveSwitchChecked(props.modelValue, props.activeValue),
)

const currentPrompt = computed(() =>
  resolveSwitchPrompt(isChecked.value, props.activeText, props.inactiveText),
)

const switchClasses = computed(() => [
  'ui-switch',
  'el-switch',
  isChecked.value ? 'is-checked' : '',
  props.disabled ? 'is-disabled' : '',
  props.loading ? 'is-loading' : '',
  props.inlinePrompt ? 'el-switch--inline-prompt' : '',
])

function toggleSwitch() {
  if (props.disabled || props.loading) {
    return
  }

  const nextChecked = !isChecked.value
  const nextValue = resolveSwitchNextValue(
    nextChecked,
    props.activeValue,
    props.inactiveValue,
  )

  emit('update:modelValue', nextValue)
  emit('change', nextValue)
}
</script>

<template>
  <button
    type="button"
    :class="switchClasses"
    role="switch"
    :name="name || undefined"
    :aria-checked="String(isChecked)"
    :aria-disabled="String(disabled || loading)"
    :disabled="disabled || loading"
    @click="toggleSwitch"
  >
    <span v-if="!inlinePrompt && (activeText || inactiveText)" class="el-switch__label el-switch__label--left">
      {{ currentPrompt }}
    </span>

    <span class="el-switch__core">
      <span v-if="inlinePrompt && currentPrompt" class="el-switch__inner">
        {{ currentPrompt }}
      </span>
      <span class="el-switch__action" />
    </span>
  </button>
</template>

<style scoped>
.ui-switch {
  --ui-switch-track-off: color-mix(in srgb, var(--qb-border-muted) 78%, white 22%);
  --ui-switch-track-on: var(--qb-primary-student);
  --ui-switch-thumb: #ffffff;
  --ui-switch-text: var(--qb-text-inverse);
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--qb-text-secondary);
  font: inherit;
  cursor: pointer;
}

.ui-switch.is-disabled,
.ui-switch.is-loading {
  cursor: not-allowed;
  opacity: 0.62;
}

.el-switch__label {
  font-size: 13px;
  line-height: 1;
  white-space: nowrap;
}

.el-switch__core {
  position: relative;
  display: inline-flex;
  align-items: center;
  width: 46px;
  min-width: 46px;
  height: 26px;
  padding: 0 4px;
  border-radius: 999px;
  background: var(--ui-switch-track-off);
  transition: background-color 180ms ease, box-shadow 180ms ease;
}

.ui-switch:not(.is-disabled):not(.is-loading):hover .el-switch__core {
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--qb-primary-soft-bg) 66%, white 34%);
}

.ui-switch.is-checked .el-switch__core {
  justify-content: flex-end;
  background: var(--ui-switch-track-on);
}

.el-switch__action {
  position: relative;
  z-index: 1;
  display: inline-flex;
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: var(--ui-switch-thumb);
  box-shadow: 0 3px 10px rgba(15, 23, 42, 0.18);
  transition: transform 180ms ease;
}

.el-switch__inner {
  position: absolute;
  left: 8px;
  right: 8px;
  overflow: hidden;
  color: var(--ui-switch-text);
  font-size: 11px;
  line-height: 1;
  text-align: center;
  white-space: nowrap;
  text-overflow: ellipsis;
}
</style>
