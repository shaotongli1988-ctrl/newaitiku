<script setup>
import { computed, provide } from 'vue'

const props = defineProps({
  modelValue: {
    type: [Array, String, Number],
    default: undefined,
  },
  accordion: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'change'])

const normalizedValue = computed(() => {
  if (props.accordion) {
    return props.modelValue ?? ''
  }
  if (Array.isArray(props.modelValue)) {
    return props.modelValue
  }
  if (props.modelValue === undefined || props.modelValue === null || props.modelValue === '') {
    return []
  }
  return [props.modelValue]
})

function isActive(name) {
  if (props.accordion) {
    return normalizedValue.value === name
  }
  return normalizedValue.value.includes(name)
}

function toggle(name) {
  let nextValue

  if (props.accordion) {
    nextValue = normalizedValue.value === name ? '' : name
  } else {
    const current = [...normalizedValue.value]
    const existingIndex = current.findIndex((item) => item === name)
    if (existingIndex >= 0) {
      current.splice(existingIndex, 1)
    } else {
      current.push(name)
    }
    nextValue = current
  }

  emit('update:modelValue', nextValue)
  emit('change', nextValue)
}

provide('uiCollapseContext', computed(() => ({
  accordion: props.accordion,
  isActive,
  toggle,
})))
</script>

<template>
  <div class="ui-collapse el-collapse" role="tablist" :aria-multiselectable="String(!accordion)">
    <slot />
  </div>
</template>

<style scoped>
.ui-collapse {
  border-top: 1px solid color-mix(in srgb, var(--qb-border-subtle) 82%, white 18%);
  border-bottom: 1px solid color-mix(in srgb, var(--qb-border-subtle) 82%, white 18%);
}
</style>
