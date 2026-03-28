<script setup>
import { inject, onBeforeUnmount, onMounted, watch } from 'vue'
import { selectContextKey } from './selectShared'

const props = defineProps({
  label: {
    type: [String, Number],
    default: '',
  },
  value: {
    type: [String, Number, Boolean, Object],
    default: undefined,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const select = inject(selectContextKey, null)
const optionUid = Symbol('uiSelectOption')

function syncOption() {
  select?.registerOption({
    uid: optionUid,
    label: props.label,
    value: props.value,
    disabled: props.disabled,
  })
}

onMounted(() => {
  syncOption()
})

watch(
  () => [props.label, props.value, props.disabled],
  () => {
    syncOption()
  },
)

onBeforeUnmount(() => {
  select?.unregisterOption(optionUid)
})
</script>

<template>
  <span class="ui-select-option-registry" aria-hidden="true" />
</template>

<style scoped>
.ui-select-option-registry {
  display: none;
}
</style>
