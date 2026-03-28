<script setup>
import { computed, provide } from 'vue'
import { radioGroupContextKey } from './radioShared'

const props = defineProps({
  modelValue: {
    type: [String, Number, Boolean],
    default: undefined,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  name: {
    type: String,
    default: '',
  },
  size: {
    type: String,
    default: '',
  },
  fill: {
    type: String,
    default: '',
  },
  textColor: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue', 'change'])

const groupClasses = computed(() => [
  'ui-radio-group',
  'el-radio-group',
  props.disabled ? 'is-disabled' : '',
])

function changeValue(nextValue) {
  if (props.disabled || props.modelValue === nextValue) {
    return
  }

  emit('update:modelValue', nextValue)
  emit('change', nextValue)
}

provide(radioGroupContextKey, {
  modelValue: computed(() => props.modelValue),
  disabled: computed(() => props.disabled),
  name: computed(() => props.name),
  size: computed(() => props.size),
  fill: computed(() => props.fill),
  textColor: computed(() => props.textColor),
  changeValue,
})
</script>

<template>
  <div :class="groupClasses" role="radiogroup" :aria-disabled="String(disabled)">
    <slot />
  </div>
</template>

<style scoped>
.ui-radio-group {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: stretch;
  gap: 0;
}

.ui-radio-group.is-disabled {
  opacity: 0.72;
}
</style>
