<script setup>
import { computed, provide, reactive } from 'vue'
import { formContextKey } from './formShared'

const props = defineProps({
  model: {
    type: Object,
    default: () => ({}),
  },
  rules: {
    type: Object,
    default: () => ({}),
  },
  labelPosition: {
    type: String,
    default: 'right',
  },
  labelWidth: {
    type: [String, Number],
    default: '',
  },
  inline: {
    type: Boolean,
    default: false,
  },
})

const items = reactive(new Map())

function registerItem(item) {
  if (!item?.uid) {
    return
  }
  items.set(item.uid, item)
}

function unregisterItem(uid) {
  items.delete(uid)
}

async function validate(callback) {
  const errors = {}
  let allValid = true

  for (const item of items.values()) {
    if (!item?.validate) {
      continue
    }
    const result = await item.validate()
    if (!result.valid) {
      allValid = false
      if (item.prop) {
        errors[item.prop] = result.message
      }
    }
  }

  if (typeof callback === 'function') {
    callback(allValid, errors)
  }

  if (allValid) {
    return true
  }

  throw errors
}

function clearValidate(propsToClear) {
  const targets = Array.isArray(propsToClear)
    ? propsToClear
    : propsToClear
      ? [propsToClear]
      : null

  for (const item of items.values()) {
    if (!item?.clearValidate) {
      continue
    }
    if (targets && item.prop && !targets.includes(item.prop)) {
      continue
    }
    item.clearValidate()
  }
}

defineExpose({
  validate,
  clearValidate,
})

provide(formContextKey, {
  model: computed(() => props.model),
  rules: computed(() => props.rules),
  labelPosition: computed(() => props.labelPosition),
  labelWidth: computed(() => props.labelWidth),
  inline: computed(() => props.inline),
  registerItem,
  unregisterItem,
})

const formClasses = computed(() => [
  'ui-form',
  'el-form',
  props.inline ? 'el-form--inline' : '',
  props.labelPosition === 'top' ? 'el-form--label-top' : '',
])

const labelWidthStyle = computed(() => {
  if (props.labelPosition === 'top' || props.labelWidth === '' || props.labelWidth === undefined) {
    return {}
  }

  const width = typeof props.labelWidth === 'number'
    ? `${props.labelWidth}px`
    : String(props.labelWidth)

  return { '--ui-form-label-width': width }
})
</script>

<template>
  <form :class="formClasses" :style="labelWidthStyle">
    <slot />
  </form>
</template>

<style scoped>
.ui-form {
  width: 100%;
}

.ui-form.el-form--inline {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 16px;
}
</style>
