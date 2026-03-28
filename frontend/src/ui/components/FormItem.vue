<script setup>
import { computed, inject, onBeforeUnmount, reactive, watch } from 'vue'
import { formContextKey, getValueByPath, validateFormField } from './formShared'

const props = defineProps({
  label: {
    type: String,
    default: '',
  },
  prop: {
    type: String,
    default: '',
  },
  required: {
    type: Boolean,
    default: false,
  },
  labelWidth: {
    type: [String, Number],
    default: '',
  },
  error: {
    type: String,
    default: '',
  },
})

const form = inject(formContextKey, null)
const validateState = reactive({
  message: '',
})

const itemUid = Symbol('uiFormItem')

async function validate() {
  if (props.error) {
    validateState.message = props.error
    return {
      valid: false,
      message: props.error,
    }
  }

  if (!form || !props.prop) {
    validateState.message = ''
    return {
      valid: true,
      message: '',
    }
  }

  const result = await validateFormField({
    model: form.model.value,
    prop: props.prop,
    rules: form.rules.value,
  })
  validateState.message = result.message
  return result
}

function clearValidate() {
  validateState.message = ''
}

form?.registerItem({
  uid: itemUid,
  prop: props.prop,
  validate,
  clearValidate,
})

onBeforeUnmount(() => {
  form?.unregisterItem(itemUid)
})

watch(
  () => (form && props.prop ? getValueByPath(form.model.value, props.prop) : undefined),
  () => {
    if (!validateState.message) {
      return
    }
    validate()
  },
)

const isTopLabel = computed(() => form?.labelPosition?.value === 'top')

const resolvedRequired = computed(() => {
  if (props.required) {
    return true
  }
  const rules = form?.rules?.value?.[props.prop]
  return Array.isArray(rules) && rules.some((rule) => rule?.required)
})

const itemClasses = computed(() => [
  'ui-form-item',
  'el-form-item',
  validateState.message ? 'is-error' : '',
  resolvedRequired.value ? 'is-required' : '',
  isTopLabel.value ? 'is-label-top' : '',
])

const labelStyles = computed(() => {
  if (isTopLabel.value) {
    return {}
  }

  const rawWidth = props.labelWidth || form?.labelWidth?.value
  if (!rawWidth) {
    return {}
  }

  const width = typeof rawWidth === 'number' ? `${rawWidth}px` : String(rawWidth)
  return { width }
})
</script>

<template>
  <div :class="itemClasses">
    <label v-if="label" class="el-form-item__label" :style="labelStyles">
      {{ label }}
    </label>
    <div class="el-form-item__content">
      <slot />
      <div v-if="validateState.message" class="el-form-item__error">
        {{ validateState.message }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.ui-form-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 18px;
}

.ui-form-item.is-label-top {
  display: grid;
  gap: 8px;
}

.el-form-item__label {
  flex: 0 0 var(--ui-form-label-width, auto);
  min-height: 22px;
  padding-top: 8px;
  color: var(--qb-text-secondary);
  font-size: 14px;
  line-height: 1.45;
  box-sizing: border-box;
}

.ui-form-item.is-required .el-form-item__label::before {
  content: '*';
  margin-right: 4px;
  color: var(--qb-danger);
}

.ui-form-item.is-label-top .el-form-item__label {
  padding-top: 0;
}

.el-form-item__content {
  min-width: 0;
  flex: 1 1 auto;
}

.el-form-item__error {
  margin-top: 6px;
  color: var(--qb-danger);
  font-size: 12px;
  line-height: 1.4;
}
</style>
